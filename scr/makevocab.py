import json
import chess

def generate_all_uci_moves():
    moves = set()
    for from_sq in chess.SQUARE_NAMES:
        for to_sq in chess.SQUARE_NAMES:
            # Non-promotion moves
            moves.add(f"{from_sq}{to_sq}")
            # Promotion moves for each possible piece (q, r, b, n)
            for promo in ['q', 'r', 'b', 'n']:
                moves.add(f"{from_sq}{to_sq}{promo}")
    return sorted(moves)

all_moves = generate_all_uci_moves()
move_vocab = {move: idx for idx, move in enumerate(all_moves)}

with open('move_vocab.json', 'w') as f:
    json.dump(move_vocab, f)

print(f"Generated {len(all_moves)} UCI moves.")