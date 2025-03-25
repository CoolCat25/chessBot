import io
import os
import json
import requests
import zstandard as zstd
import chess
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from tqdm import tqdm
import multiprocessing as mp



piece_to_channel = {
    'P': 0, 'N': 1, 'B': 2, 'R': 3, 'Q': 4, 'K': 5,
    'p': 6, 'n': 7, 'b': 8, 'r': 9, 'q': 10, 'k': 11,
}


def board_to_tensor(board):
    tensor = np.zeros((17, 8, 8), dtype=np.float32)
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            row = 7 - (square // 8)
            col = square % 8
            tensor[piece_to_channel[piece.symbol()], row, col] = 1.0

    active_color = 1.0 if board.turn == chess.WHITE else 0.0
    tensor[12, :, :] = active_color

    tensor[13, :, :] = 1.0 if board.has_kingside_castling_rights(chess.WHITE) else 0.0
    tensor[14, :, :] = 1.0 if board.has_queenside_castling_rights(chess.WHITE) else 0.0
    tensor[15, :, :] = 1.0 if board.has_kingside_castling_rights(chess.BLACK) else 0.0
    tensor[16, :, :] = 1.0 if board.has_queenside_castling_rights(chess.BLACK) else 0.0

    return tensor


class LichessEvalDataset(Dataset):
    def __init__(self, jsonl_zst_path, max_positions=200000, vocab_path="move_vocab.json"):
        self.states = []
        self.moves = []
        with open(vocab_path, 'r') as f:
            self.move_vocab = json.load(f)
        self._prepare_dataset(jsonl_zst_path, max_positions)

    def _prepare_dataset(self, path, max_positions):
        pos_count = 0
        with open(path, 'rb') as fh:
            dctx = zstd.ZstdDecompressor()
            stream_reader = dctx.stream_reader(fh)
            text_stream = io.TextIOWrapper(stream_reader, encoding='utf-8')
            for line in tqdm(text_stream, desc="Processing positions"):
                if pos_count >= max_positions:
                    break
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                fen = data.get("fen")
                evals = data.get("evals", [])
                if not fen or not evals:
                    continue
                best_eval = max(evals, key=lambda ev: ev.get("depth", 0))
                if "pvs" not in best_eval or not best_eval["pvs"]:
                    continue
                pv = best_eval["pvs"][0]
                line_moves = pv.get("line", "")
                if not line_moves:
                    continue
                best_move = line_moves.split()[0]
                if best_move not in self.move_vocab:
                    continue
                board = chess.Board(fen)
                state_tensor = board_to_tensor(board)
                self.states.append(state_tensor)
                self.moves.append(self.move_vocab[best_move])
                pos_count += 1
        print(f"Loaded {pos_count} positions. Vocabulary size: {len(self.move_vocab)}")

    def __len__(self):
        return len(self.states)

    def __getitem__(self, idx):
        state = torch.tensor(self.states[idx], dtype=torch.float32)
        target = torch.tensor(self.moves[idx], dtype=torch.long)
        return state, target


def main():
    # --- CUDA Integration ---
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # --- Training Setup ---
    dataset = LichessEvalDataset("lichess_db_eval.jsonl.zst", max_positions=200000)

    # Configure DataLoader with 8 workers
    dataloader = DataLoader(
        dataset,
        batch_size=32,
        shuffle=True,
        num_workers=8,
        pin_memory=True,
        persistent_workers=True,
        multiprocessing_context=mp.get_context('spawn')
    )

    with open('move_vocab.json', 'r') as f:
        move_vocab = json.load(f)
    num_moves = len(move_vocab)

    # --- Model Definition ---

    class SEBlock(nn.Module):
        def __init__(self, channels, reduction=16):
            super(SEBlock, self).__init__()
            self.fc = nn.Sequential(
                nn.AdaptiveAvgPool2d(1),
                nn.Conv2d(channels, channels // reduction, kernel_size=1),
                nn.ReLU(),
                nn.Conv2d(channels // reduction, channels, kernel_size=1),
                nn.Sigmoid()
            )

        def forward(self, x):
            scale = self.fc(x)
            return x * scale

    class ResNetBlock(nn.Module):
        def __init__(self, channels):
            super(ResNetBlock, self).__init__()
            self.conv1 = nn.Conv2d(channels, channels, kernel_size=3, padding=1)
            self.relu = nn.ReLU()
            self.conv2 = nn.Conv2d(channels, channels, kernel_size=3, padding=1)
            self.se = SEBlock(channels)

        def forward(self, x):
            residual = x
            out = self.conv1(x)
            out = self.relu(out)
            out = self.conv2(out)
            out = self.se(out)
            return self.relu(out + residual)

    class ChessResNet(nn.Module):
        def __init__(self, num_moves):
            super(ChessResNet, self).__init__()
            self.conv1 = nn.Conv2d(17, 64, kernel_size=3, padding=1)
            self.res_blocks = nn.Sequential(
                ResNetBlock(64),
                ResNetBlock(64),
                ResNetBlock(64)
            )
            self.flatten = nn.Flatten()
            self.fc_layers = nn.Sequential(
                nn.Linear(64 * 8 * 8, 512),
                nn.ReLU(),
                nn.Linear(512, num_moves)
            )

        def forward(self, x):
            x = self.conv1(x)
            x = self.res_blocks(x)
            x = self.flatten(x)
            x = self.fc_layers(x)
            return x

        # --- Data Processing ---

    model = ChessResNet(num_moves).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    # --- Training Loop ---
    num_epochs = 50
    for epoch in range(num_epochs):
        running_loss = 0.0
        for states, targets in tqdm(dataloader, desc=f"Epoch {epoch + 1}/{num_epochs}"):
            states, targets = states.to(device), targets.to(device)
            optimizer.zero_grad()
            outputs = model(states)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()
            running_loss += loss.item()
        print(f"Epoch [{epoch + 1}/{num_epochs}], Loss: {running_loss / len(dataloader):.4f}")

    torch.save(model.state_dict(), "chess_resnet_se.pth")


if __name__ == "__main__":
    mp.set_start_method('spawn', force=True)
    main()