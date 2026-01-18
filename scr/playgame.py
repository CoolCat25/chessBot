import random
import chess.polyglot
import berserk
import chess
import time
import signal
import sys
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


API_TOKEN = "lip_CpEAd1KdD5ypRmRUc3Q8"  
session = berserk.TokenSession(API_TOKEN)

retry_strategy = Retry(
    total=3,              # Total number of retries
    backoff_factor=0.1,  
    allowed_methods=frozenset(['GET', 'POST']),  
    status_forcelist=[500, 502, 503, 504],         
    raise_on_redirect=True,
    raise_on_status=True
)

adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)
session.mount("http://", adapter)

client = berserk.Client(session=session)

piece_values = {
    'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0,
    'p': -1, 'n': -3, 'b': -3, 'r': -5, 'q': -9, 'k': 0,
}


pawn_pst_white = [
    [0,   0,   0,   0,   0,   0,   0,  0],
    [1,   1,   1,   1,   1,   1,   1,  1],
    [0.2, 0.2, 0.4, 0.6, 0.6, 0.4, 0.2, 0.2],
    [0.1, 0.1, 0.2, 0.5, 0.5, 0.2, 0.1, 0.1],
    [0,   0,   0,   0.4, 0.4, 0,   0,   0],
    [0.1, -0.1,-0.2, 0,   0,  -0.2,-0.1, 0.1],
    [0.1, 0.2, 0.2, -0.4,-0.4, 0.2, 0.2, 0.1],
    [0,   0,   0,   0,   0,   0,   0,   0]
]

knight_pst_white = [
    [-1,   -0.8, -0.6, -0.6, -0.6, -0.6, -0.8, -1],
    [-0.8, -0.4,  0,    0.1,  0.1,  0,   -0.4, -0.8],
    [-0.6,  0.1,  0.2,  0.3,  0.3,  0.2,  0.1, -0.6],
    [-0.6,  0,    0.3,  0.4,  0.4,  0.3,  0,   -0.6],
    [-0.6,  0.1,  0.3,  0.4,  0.4,  0.3,  0.1, -0.6],
    [-0.6,  0,    0.2,  0.3,  0.3,  0.2,  0,   -0.6],
    [-0.8, -0.4,  0,    0,    0,    0,   -0.4, -0.8],
    [-1,   -0.8, -0.6, -0.6, -0.6, -0.6, -0.8, -1]
]

bishop_pst_white = [
    [-0.4, -0.2, -0.2, -0.2, -0.2, -0.2, -0.2, -0.4],
    [-0.2, 0.1,  0.2,  0.2,  0.2,  0.2,  0.1, -0.2],
    [-0.2, 0.2,  0.4,  0.4,  0.4,  0.4,  0.2, -0.2],
    [-0.2, 0.2,  0.4,  0.6,  0.6,  0.4,  0.2, -0.2],
    [-0.2, 0.2,  0.4,  0.6,  0.6,  0.4,  0.2, -0.2],
    [-0.2, 0.2,  0.4,  0.4,  0.4,  0.4,  0.2, -0.2],
    [-0.2, 0.1,  0.2,  0.2,  0.2,  0.2,  0.1, -0.2],
    [-0.4, -0.2, -0.2, -0.2, -0.2, -0.2, -0.2, -0.4]
]

rook_pst_white = [
    [0,    0,    0,    0.1,  0.1,  0,    0,   0],
    [0.2,  0.2,  0.2,  0.2,  0.2,  0.2,  0.2, 0.2],
    [-0.1, 0,    0,    0,    0,    0,    0,  -0.1],
    [-0.1, 0,    0.1,  0.1,  0.1,  0.1,  0,  -0.1],
    [-0.1, 0,    0.1,  0.1,  0.1,  0.1,  0,  -0.1],
    [-0.1, 0,    0,    0,    0,    0,    0,  -0.1],
    [0.2,  0.2,  0.2,  0.2,  0.2,  0.2,  0.2, 0.2],
    [0,    0,    0,    0.1,  0.1,  0,    0,   0]
]

queen_pst_white = [
    [-0.004, -0.002, -0.002, -0.01, -0.01, -0.002, -0.002, -0.004],
    [-0.2,    0,      0.1,    0.1,   0.1,   0.1,    0,     -0.2],
    [-0.2,    0.1,    0.2,    0.2,   0.2,   0.2,    0.1,   -0.2],
    [-0.1,    0.1,    0.2,    0.3,   0.3,   0.2,    0.1,   -0.1],
    [-0.1,    0.1,    0.2,    0.3,   0.3,   0.2,    0.1,   -0.1],
    [-0.2,    0.1,    0.2,    0.2,   0.2,   0.2,    0.1,   -0.2],
    [-0.2,    0,      0.1,    0.1,   0.1,   0.1,    0,     -0.2],
    [-0.004, -0.002, -0.002, -0.01, -0.01, -0.002, -0.002, -0.004]
]

king_pst_white = [
    [-0.4, -0.2, -0.2, -0.2, -0.2, -0.2, -0.2, -0.4],
    [-0.2, 0,    0.1,  0.1,  0.1,  0.1,  0,   -0.2],
    [-0.2, 0.1,  0.2,  0.3,  0.3,  0.2,  0.1, -0.2],
    [-0.2, 0.1,  0.3,  0.4,  0.4,  0.3,  0.1, -0.2],
    [-0.2, 0.1,  0.3,  0.4,  0.4,  0.3,  0.1, -0.2],
    [-0.2, 0.1,  0.2,  0.3,  0.3,  0.2,  0.1, -0.2],
    [-0.2, 0,    0.1,  0.1,  0.1,  0.1,  0,   -0.2],
    [-0.4, -0.2, -0.2, -0.2, -0.2, -0.2, -0.2, -0.4]
]

pawn_pst_black = [
    [0,   0,   0,   0,   0,   0,   0,   0],
    [-0.1, -0.2, -0.2, 0.4, 0.4, -0.2, -0.2, -0.1],
    [-0.1, 0.1, 0.2, 0, 0, 0.2, 0.1, -0.1],
    [0,   0,   0,   -0.4, -0.4,  0,   0,   0],
    [-0.1, -0.1, -0.2, -0.5, -0.5, -0.2, -0.1, -0.1],
    [-0.2, -0.2, -0.4, -0.6, -0.6, -0.4, -0.2, -0.2],
    [-1,  -1,  -1,  -1,  -1,  -1,  -1,  -1],
    [0,   0,   0,   0,   0,   0,   0,   0]
]

knight_pst_black = [
    [1, 0.8, 0.6, 0.6, 0.6, 0.6, 0.8, 1],
    [0.8, 0.4, 0, 0, 0, 0, 0.4, 0.8],
    [0.6, 0, -0.2, -0.3, -0.3, -0.2, 0, 0.6],
    [0.6, -0.1, -0.3, -0.4, -0.4, -0.3, -0.1, 0.6],
    [0.6, 0, -0.3, -0.4, -0.4, -0.3, 0, 0.6],
    [0.6, -0.1, -0.2, -0.3, -0.3, -0.2, -0.1, 0.6],
    [0.8, 0.4, 0, -0.1, -0.1, 0, 0.4, 0.8],
    [1, 0.8, 0.6, 0.6, 0.6, 0.6, 0.8, 1]
]

bishop_pst_black = [
    [0.4, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.4],
    [0.2, -0.1, -0.2, -0.2, -0.2, -0.2, -0.1, 0.2],
    [0.2, -0.2, -0.4, -0.4, -0.4, -0.4, -0.2, 0.2],
    [0.2, -0.2, -0.4, -0.6, -0.6, -0.4, -0.2, 0.2],
    [0.2, -0.2, -0.4, -0.6, -0.6, -0.4, -0.2, 0.2],
    [0.2, -0.2, -0.4, -0.4, -0.4, -0.4, -0.2, 0.2],
    [0.2, -0.1, -0.2, -0.2, -0.2, -0.2, -0.1, 0.2],
    [0.4, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.4]
]

rook_pst_black = [
    [0, 0, 0, -0.1, -0.1, 0, 0, 0],
    [-0.2, -0.2, -0.2, -0.2, -0.2, -0.2, -0.2, -0.2],
    [0.1, 0, 0, 0, 0, 0, 0, 0.1],
    [0.1, 0, -0.1, -0.1, -0.1, -0.1, 0, 0.1],
    [0.1, 0, -0.1, -0.1, -0.1, -0.1, 0, 0.1],
    [0.1, 0, 0, 0, 0, 0, 0, 0.1],
    [-0.2, -0.2, -0.2, -0.2, -0.2, -0.2, -0.2, -0.2],
    [0, 0, 0, -0.1, -0.1, 0, 0, 0]
]

queen_pst_black = [
    [0.004, 0.002, 0.002, 0.01, 0.01, 0.002, 0.002, 0.004],
    [0.2, 0, -0.1, -0.1, -0.1, -0.1, 0, 0.2],
    [0.2, -0.1, -0.2, -0.2, -0.2, -0.2, -0.1, 0.2],
    [0.1, -0.1, -0.2, -0.3, -0.3, -0.2, -0.1, 0.1],
    [0.1, -0.1, -0.2, -0.3, -0.3, -0.2, -0.1, 0.1],
    [0.2, -0.1, -0.2, -0.2, -0.2, -0.2, -0.1, 0.2],
    [0.2, 0, -0.1, -0.1, -0.1, -0.1, 0, 0.2],
    [0.004, 0.002, 0.002, 0.01, 0.01, 0.002, 0.002, 0.004]
]

king_pst_black = [
    [0.4, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.4],
    [0.2, 0, -0.1, -0.1, -0.1, -0.1, 0, 0.2],
    [0.2, -0.1, -0.2, -0.3, -0.3, -0.2, -0.1, 0.2],
    [0.2, -0.1, -0.3, -0.4, -0.4, -0.3, -0.1, 0.2],
    [0.2, -0.1, -0.3, -0.4, -0.4, -0.3, -0.1, 0.2],
    [0.2, -0.1, -0.2, -0.3, -0.3, -0.2, -0.1, 0.2],
    [0.2, 0, -0.1, -0.1, -0.1, -0.1, 0, 0.2],
    [0.4, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.4]
]


piece_square_tables = {
    'P': pawn_pst_white,
    'N': knight_pst_white,
    'B': bishop_pst_white,
    'R': rook_pst_white,
    'Q': queen_pst_white,
    'K': king_pst_white,
    'p': pawn_pst_black,
    'n': knight_pst_black,
    'b': bishop_pst_black,
    'r': rook_pst_black,
    'q': queen_pst_black,
    'k': king_pst_black
}

def king_safety(board, king_square, color):

    safety_score = 0
    file = chess.square_file(king_square)
    rank = chess.square_rank(king_square)

    pawn_shield_bonus = 0.5
    pawn_penalty = -1  

    # Evaluate adjacent pawns for pawn shield
    for rank_offset in range(1, 3):  
        for file_offset in [-1, 0, 1]:  
            new_file = file + file_offset
            new_rank = rank + (rank_offset if color == chess.WHITE else -rank_offset)
            if 0 <= new_file < 8 and 0 <= new_rank < 8:
                square = chess.square(new_file, new_rank)
                piece = board.piece_at(square)
                if piece:
                    if piece.piece_type == chess.PAWN:
                        if piece.color == color:
                            safety_score += pawn_shield_bonus  
                        else:
                            safety_score += pawn_penalty  

    return safety_score


def evaluate_pawn_structure(board, color):
    """
    Evaluates the pawn structure for weaknesses like doubled or isolated pawns.
    """
    score = 0
    pawns = board.pieces(chess.PAWN, color)
    pawn_files = [chess.square_file(p) for p in pawns]

    for f in set(pawn_files):
        count = pawn_files.count(f)
        if count > 1:
            score -= 1.5 * (count - 1)

    for f in pawn_files:
        if (f - 1) not in pawn_files and (f + 1) not in pawn_files:
            score -= 2

    return score


def evaluate_board(board, is_white):
    """
    Evaluates the board position and returns a score from the bot's perspective.
    """
    if board.is_checkmate():
        return float('-inf') if board.turn == is_white else float('inf')
    if board.is_stalemate() or board.is_insufficient_material():
        return 0

    material_score = 0
    pos_score_white = 0
    pos_score_black = 0
    king_safety_score = 0
    pawn_structure_score = 0

    white_king_safety = 0
    black_king_safety = 0

    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            material_score += piece_values.get(piece.symbol(), 0)

            pst = piece_square_tables.get(piece.symbol(), [[0] * 8] * 8)
            rank, file = divmod(square, 8)
            if piece.color == chess.WHITE:
                pos_score_white += pst[rank][file]
            else:
                pos_score_black += pst[rank][file]

            if piece.piece_type == chess.KING:
                if piece.color == chess.WHITE:
                    white_king_safety = king_safety(board, square, chess.WHITE)
                else:
                    black_king_safety = king_safety(board, square, chess.BLACK)

    # Evaluate pawn structures separately
    pawn_structure_score += evaluate_pawn_structure(board, chess.WHITE)
    pawn_structure_score -= evaluate_pawn_structure(board, chess.BLACK)

    # Adjust king safety perspective
    if is_white:
        king_safety_score = white_king_safety - black_king_safety
    else:
        king_safety_score = black_king_safety - white_king_safety

    # Total evaluation score
    positional_score = pos_score_white + pos_score_black
    total_score = material_score + positional_score/4# + king_safety_score

    # Debugging output
    #print(f"White Positional Score: {pos_score_white}")
    #print(f"Black Positional Score: {pos_score_black}")
    #print(f"Positional Score Difference: {positional_score}")
    #print(f"Total Evaluation Score: {total_score}")

    return total_score if is_white else -total_score


def minimax(board, depth, alpha, beta, maximizing_player, is_white):
    """
    Minimax algorithm with alpha-beta pruning.
    """
    if depth == 0 or board.is_game_over():
        return evaluate_board(board, is_white)

    legal_moves = list(board.legal_moves)
    # Prioritize moves that give check or are captures
    legal_moves.sort(key=lambda move: board.gives_check(move) or board.is_capture(move), reverse=True)

    if maximizing_player:
        max_eval = float('-inf')
        for move in legal_moves:
            board.push(move)
            score = minimax(board, depth - 1, alpha, beta, False, is_white)
            board.pop()
            max_eval = max(max_eval, score)
            alpha = max(alpha, score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for move in legal_moves:
            board.push(move)
            score = minimax(board, depth - 1, alpha, beta, True, is_white)
            board.pop()
            min_eval = min(min_eval, score)
            beta = min(beta, score)
            if beta <= alpha:
                break
        return min_eval


def get_best_move(board, is_white, depth=3):
    """
    Determines the best move using opening book when available, otherwise uses minimax.
    """
    # Use opening book for the first 12 moves (24 plies)
    if board.ply() < 24:
        try:
            with chess.polyglot.open_reader("human.bin") as reader:
                entries = list(reader.find_all(board))
                if entries:
                    # Weighted random selection based on entry frequency
                    total_weight = sum(entry.weight for entry in entries)
                    selected = random.uniform(0, total_weight)
                    cumulative = 0

                    for entry in entries:
                        cumulative += entry.weight
                        if selected <= cumulative:
                            chosen_move = entry.move
                            # Verify the move is legal
                            if chosen_move in board.legal_moves:
                                logging.info(f'Using opening book move: {chosen_move.uci()}')
                                return chosen_move
                            break
        except FileNotFoundError:
            logging.error("Opening book file 'human.bin' not found.")
        except Exception as e:
            logging.error(f'Error reading opening book: {e}')

    legal_moves = list(board.legal_moves)
    best_eval = float('-inf') if is_white else float('inf')
    best_move = None

    for move in legal_moves:
        board.push(move)
        evaluation = minimax(board, depth - 1, float('-inf'), float('inf'), False, is_white)
        board.pop()

        if is_white and evaluation > best_eval:
            best_eval = evaluation
            best_move = move
        elif not is_white and evaluation < best_eval:
            best_eval = evaluation
            best_move = move

    logging.info(f'Best engine move: {best_move.uci() if best_move else "None"}, Evaluation: {best_eval}')
    return best_move

def handle_game(game_id):
    """
    Processes a game stream by handling incoming events.
    """
    logging.info(f'Handling game {game_id}')
    stream = client.bots.stream_game_state(game_id)
    board = chess.Board()
    is_white = None

    account_id = client.account.get()['id']

    for event in stream:
        logging.debug(f'Received event: {event}')
        if event['type'] == 'gameFull':
            moves = event['state']['moves']
            if moves:
                for move in moves.split():
                    board.push_uci(move)
            if event['white']['id'] == account_id:
                is_white = True
                color = 'white'
            else:
                is_white = False
                color = 'black'

            logging.info(f'Playing as {color}')
            if board.turn == is_white and not board.is_game_over():
                best_move = get_best_move(board, is_white)
                if best_move:
                    try:
                        client.bots.make_move(game_id, best_move.uci())
                    except requests.exceptions.HTTPError as e:
                        logging.error(f'HTTP error making move: {e}')
                    except requests.exceptions.RequestException as e:
                        logging.error(f'Request error making move: {e}')

        elif event['type'] == 'gameState':
            moves = event['moves']
            board = chess.Board()
            if moves:
                for move in moves.split():
                    board.push_uci(move)
            if board.turn == is_white and not board.is_game_over():
                best_move = get_best_move(board, is_white)
                if best_move:
                    try:
                        client.bots.make_move(game_id, best_move.uci())
                    except requests.exceptions.HTTPError as e:
                        logging.error(f'HTTP error making move: {e}')
                    except requests.exceptions.RequestException as e:
                        logging.error(f'Request error making move: {e}')

        elif event['type'] == 'chatLine':
            logging.info(f'Chat message from {event.get("username", "Unknown")}: {event.get("text", "")}')

def should_accept(event):

    return True

def signal_handler(sig, frame):
    logging.info('Exiting...')
    sys.exit(0)

def main():
    signal.signal(signal.SIGINT, signal_handler)
    logging.info('Bot is running. Waiting for events...')
    for event in client.bots.stream_incoming_events():
        logging.debug(f'Incoming event: {event}')
        if event['type'] == 'challenge':
            if should_accept(event):
                client.bots.accept_challenge(event['challenge']['id'])
                logging.info(f'Accepted challenge {event["challenge"]["id"]}')
            else:
                client.bots.decline_challenge(event['challenge']['id'])
                logging.info(f'Declined challenge {event["challenge"]["id"]}')
        elif event['type'] == 'gameStart':
            game_id = event['game']['id']
            logging.info(f'Starting game {game_id}')
            handle_game(game_id)

if __name__ == '__main__':
    main()
