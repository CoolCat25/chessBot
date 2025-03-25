import datetime
import json
import threading

import berserk
import torch
import torch.nn as nn
import torch.optim as optim
import chess
import numpy as np
import time
from tqdm import tqdm
from datetime import datetime
active_games = {}  # Track game_id: {color, last_fen}
API_TOKEN = "lip_CpEAd1KdD5ypRmRUc3Q8"
session = berserk.TokenSession(API_TOKEN)  # Increased timeout
client = berserk.Client(session=session)
try:
    account_info = client.account.get()
    print(f"Connected as {account_info['username']}")
except berserk.exceptions.ResponseError as e:
    print(f"Token validation failed: {e}")
    exit(1)


# --- Load Move Vocabulary ---
# Load the comprehensive move vocabulary
def load_move_vocab(vocab_path="move_vocab.json"):
    with open(vocab_path, "r") as f:
        move_vocab = json.load(f)
    inv_move_vocab = {int(v): k for k, v in move_vocab.items()}
    return move_vocab, inv_move_vocab

move_vocab, inv_move_vocab = load_move_vocab("move_vocab.json")
num_moves = len(move_vocab)

# Initialize model with the correct number of moves


# --- Bot and Engine Model Code ---

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

# --- Berserk Lichess Bot API Integration ---

# --- Neural Network Helper Functions ---

def load_model(model_path, num_moves):
    model = ChessResNet(num_moves)
    model.load_state_dict(torch.load(model_path))
    model.eval()
    return model

def predict_move(model, board):
    state_tensor = torch.tensor(board_to_tensor(board)).unsqueeze(0)
    with torch.no_grad():
        outputs = model(state_tensor)
    predicted_move_idx = torch.argmax(outputs, dim=1).item()
    print(f"Predicted move index: {predicted_move_idx}")
    return predicted_move_idx

def map_move(predicted_idx):
    # Map the predicted index to a UCI move string using our inverted vocabulary.
    move = inv_move_vocab.get(predicted_idx)
    if move is None:
        print(f"Warning: Predicted index {predicted_idx} not found in vocabulary. Using default move 'e2e4'.")
        return "e2e4"
    return move


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")
# --- Model Loading Fixes ---
# Add this after loading the move_vocab
move_vocab, inv_move_vocab = load_move_vocab("move_vocab.json")
num_moves = len(move_vocab)

# Initialize model with correct device and parameters
model = ChessResNet(num_moves).to(device)
model.load_state_dict(torch.load("chess_resnet_se.pth", map_location=device))
model.eval()

# --- Bot Infrastructure ---
session = berserk.TokenSession(API_TOKEN)
client = berserk.Client(session=session)


class GameHandler(threading.Thread):
    def __init__(self, game_id, color):
        super().__init__()
        self.game_id = game_id
        self.color = color
        self.board = chess.Board()
        self.running = True

    def run(self):
        """Main game loop handling move responses"""
        try:
            stream = client.bots.stream_game_state(self.game_id)
            for event in stream:
                if not self.running:
                    break

                if event['type'] == 'gameFull':
                    self.handle_game_full(event)
                elif event['type'] == 'gameState':
                    self.handle_game_state(event)
        except Exception as e:
            print(f"Game {self.game_id} error: {str(e)}")
        finally:
            print(f"Game {self.game_id} ended")

    def handle_game_full(self, event):
        """Handle initial game state from 'gameFull' event"""
        # Handle Lichess' special 'startpos' notation
        initial_fen = event.get('initialFen', chess.STARTING_FEN)
        if initial_fen == "startpos":
            initial_fen = chess.STARTING_FEN  # Convert to proper FEN

        self.board = chess.Board(initial_fen)

        # Apply any existing moves
        moves_uci = event['state']['moves'].split()
        for move_uci in moves_uci:
            self.board.push_uci(move_uci)

        print(f"Initial position: {self.board.fen()}")
        self.check_and_make_move()

    def handle_game_state(self, state):
        """Process ongoing game state updates"""
        # Handle FEN or startpos
        if 'fen' in state:
            fen = state['fen']
            if fen == "startpos":
                fen = chess.STARTING_FEN
            self.board.set_fen(fen)
        else:
            # Fallback to move list reconstruction
            self.board.reset()
            moves_uci = state['moves'].split()
            for move_uci in moves_uci:
                self.board.push_uci(move_uci)

        print(f"Updated position: {self.board.fen()}")
        self.check_and_make_move()

    def check_and_make_move(self):
        """Check if it's our turn and make a move if needed"""
        print(f"Current turn: {'white' if self.board.turn else 'black'} | Our color: {self.color}")
        if self.should_move():
            print("It's our turn! Choosing move...")
            move = self.choose_move()
            self.make_move(move)
        else:
            print("Not our turn")

    def should_move(self):
        """Check if it's our turn to move (FIXED)"""
        # Convert 'white'/'black' to chess.WHITE/chess.BLACK comparison
        return (self.color == 'white' and self.board.turn == chess.WHITE) or \
            (self.color == 'black' and self.board.turn == chess.BLACK)

    def choose_move(self):
        state_np = board_to_tensor(self.board)
        state_tensor = torch.from_numpy(state_np).unsqueeze(0).float().to(device)

        legal_moves = [move.uci() for move in self.board.legal_moves]
        legal_indices = [move_vocab[m] for m in legal_moves if m in move_vocab]

        if not legal_indices:
            return self.random_legal_move()

        with torch.no_grad():
            outputs = model(state_tensor)
            mask = torch.ones_like(outputs) * float('-inf')
            mask[:, legal_indices] = 0
            masked_outputs = outputs + mask

            # Apply temperature (e.g., 0.5 for more exploration)
            temperature = 0.5
            probs = torch.softmax(masked_outputs / temperature, dim=1)
            move_idx = torch.multinomial(probs, 1).item()

        uci_move = inv_move_vocab.get(move_idx, '0000')

        if uci_move in legal_moves:
            return uci_move
        return self.random_legal_move()
    def random_legal_move(self):
        print("random move")
        """Fallback move selection with safety checks"""
        legal_moves = [m.uci() for m in self.board.legal_moves]

        if not legal_moves:
            if self.board.is_checkmate():
                print("Checkmate - resigning")
            else:
                print("Stalemate - game drawn")
            return "resign"

        return np.random.choice(legal_moves)

    def make_move(self, move):
        """Send move to Lichess"""
        try:
            client.bots.make_move(self.game_id, move)
            print(f"Game {self.game_id} made move: {move}")
        except berserk.exceptions.ResponseError as e:
            print(f"Move error in {self.game_id}: {str(e)}")

    def stop(self):
        self.running = False


def handle_incoming_events():
    """Main event loop for challenges and game starts"""
    while True:
        try:
            for event in client.bots.stream_incoming_events():
                print(f"Received event: {event['type']}")

                if event['type'] == 'challenge':
                    handle_challenge(event)
                elif event['type'] == 'gameStart':
                    start_game(event)
                elif event['type'] == 'gameFinish':
                    pass  # Handle game completion if needed

        except Exception as e:
            print(f"Event stream error: {str(e)}")
            time.sleep(5)


def handle_challenge(challenge):
    """Challenge response logic"""
    challenge_id = challenge['challenge']['id']

    # Accept all standard challenges
    if challenge['challenge']['variant']['key'] == 'standard':
        client.bots.accept_challenge(challenge_id)
        print(f"Accepted challenge {challenge_id}")
    else:
        client.bots.decline_challenge(challenge_id)
        print(f"Declined challenge {challenge_id}")


def start_game(event):
    """Start a new game thread"""
    game_id = event['game']['id']
    color = event['game']['color']

    print(f"Starting game {game_id} as {color}")
    game = GameHandler(game_id, color)
    game.start()

print("Move vocab size:", len(move_vocab))
print("Model output size:", model.fc_layers[-1].out_features)

if __name__ == "__main__":
    print("Bot starting...")
    handle_incoming_events()