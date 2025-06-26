import chess
import chess.pgn
import pandas as pd
import math
import tqdm
import os
from stockfish import Stockfish
import numpy as np
import google.generativeai as genai

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 1000)

GEMINI_API_KEY = "Secret"
genai.configure(api_key=GEMINI_API_KEY)

def generate_gemini_advice(forkCount, hangingCount, otherCount,pinCount):
    prompt = f"""
    You are a chess coach, give advice to the user based on the followind data.
    They make blunders regarding forks {forkCount} amount of times.
    They make blunders regarding hanging pieces {hangingCount} amount of times.
    They make blunders regarding missed tactics and positional errors {otherCount} amount of times.
    They make blunders regarding pins and skewers {pinCount} amount of times.

"""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"GEMINI ERROR: {e}"

def get_pgn_file_path():

    print("Welcome! To analyze your Chess.com games for blunders, please follow these steps:")
    print("1. Go to Chess.com and log in.")
    print("2. Navigate to your 'Games' -> 'Archive' (or 'Play' -> 'Archive').")
    print("3. Look for an option to 'Download My Games' or 'Export Games'.")
    print("4. Download your PGN file (e.g., 'ChessCom_YourUsername_YYYYMMDD.pgn').")
    print("   Make sure to note down where you save it on your computer.")
    print("\n---")

    while True:
        pgn_file = input("Please enter the FULL PATH to your downloaded Chess.com PGN file: ").strip()
        if os.path.exists(pgn_file):
            if pgn_file.lower().endswith('.pgn'):
                print(f"Using PGN file: {pgn_file}")
                return pgn_file
            else:
                print("Error: The file does not seem to be a PGN. Please ensure it ends with .pgn")
        else:
            print(f"Error: File not found at '{pgn_file}'. Please check the path and try again.")
            print("Example path for Mac: /Users/YourUsername/Downloads/my_games.pgn")
            print("Example path for Windows: C:\\Users\\YourUsername\\Downloads\\my_games.pgn")


def get_cp_value(evaluation):

    if evaluation is None:
        return 0

    if evaluation['type'] == 'cp':
        return evaluation['value']
    elif evaluation['type'] == 'mate':

        return 100000 * evaluation['value']
    return 0

def classify_blunder(blunder_row, stockfish_engine):

    blunder_type = "Positional/Other Blunder"

    board_after_blunder = chess.Board(blunder_row['FEN_After_Blunder'])
    blundering_player_color = chess.WHITE if blunder_row['Player_Who_Blundered'] == 'White' else chess.BLACK
    opponent_color = not blundering_player_color

    if abs(blunder_row['Eval_After_Blunder_CP']) >= 50000:
        return "Checkmate Blunder"

    try:
        stockfish_engine.set_fen_position(board_after_blunder.fen())
        opponent_best_moves = stockfish_engine.get_top_moves(3)

        for move_info in opponent_best_moves:
            opponent_best_move_uci = move_info['Move']
            if opponent_best_move_uci:
                opponent_best_move = chess.Move.from_uci(opponent_best_move_uci)

                temp_board_after_opponent_move = board_after_blunder.copy()
                if opponent_best_move in temp_board_after_opponent_move.legal_moves:
                    temp_board_after_opponent_move.push(opponent_best_move)

                    if board_after_blunder.is_capture(opponent_best_move):
                        captured_piece_square = opponent_best_move.to_square
                        captured_piece = board_after_blunder.piece_at(captured_piece_square)

                        if captured_piece and captured_piece.color == blundering_player_color and captured_piece.piece_type != chess.KING:
                            defenders = board_after_blunder.attackers(blundering_player_color, captured_piece_square)
                            if not defenders:
                                return "Hanging Piece"

                    forking_piece_square = opponent_best_move.to_square
                    attacked_valuable_pieces_count = 0
                    # Iterate through all squares that the forking piece now attacks
                    for attacked_square in temp_board_after_opponent_move.attacks(forking_piece_square):
                        attacked_piece = temp_board_after_opponent_move.piece_at(attacked_square)
                        if attacked_piece and attacked_piece.color == blundering_player_color and \
                           attacked_piece.piece_type not in [chess.PAWN, chess.KING]:
                            attacked_valuable_pieces_count += 1

                    if attacked_valuable_pieces_count >= 2:
                        return "Fork Blunder"


        for square, piece in board_after_blunder.piece_map().items():
            if piece and piece.color == blundering_player_color:
                if board_after_blunder.is_pinned(blundering_player_color, square):
                    return "Pin/Skewer Blunder"

    except ValueError:

        pass
    except Exception as e:

        pass

    return blunder_type


STOCKFISH_EXECUTABLE_PATH = "/opt/homebrew/bin/stockfish"

try:
    engine = Stockfish(STOCKFISH_EXECUTABLE_PATH, parameters={"Contempt": 0, "Threads": 4, "Hash": 256})
    print(f"Stockfish engine initialized successfully from: {STOCKFISH_EXECUTABLE_PATH}")
except Exception as e:
    print(f"Error initializing Stockfish engine. Please ensure the path is correct and Stockfish is installed.")
    print(f"Error details: {e}")
    print("Exiting.")
    exit()
if __name__ == "__main__":
    pgn_file_path = get_pgn_file_path()
    user = "Xx_Galaxy_Dragon_xX"

    forkCount = 0
    pinCount = 0
    otherCount = 0
    hangingCount = 0

    games_data = []
    print("\nProcessing games from PGN file (this may take a moment)...")

    try:
        # Open and read the PGN file game by game
        with open(pgn_file_path, encoding="utf-8") as pgn_file:
            game_idx = 0
            while True:
                game = chess.pgn.read_game(pgn_file)
                if game is None:
                    break

                game_info = {
                    'game_index': game_idx,
                    'Event': game.headers.get('Event', 'N/A'),
                    'Site': game.headers.get('Site', 'N/A'),
                    'Date': game.headers.get('Date', 'N/A'),
                    'Round': game.headers.get('Round', 'N/A'),
                    'White': game.headers.get('White', 'N/A'),
                    'Black': game.headers.get('Black', 'N/A'),
                    'Result': game.headers.get('Result', 'N/A'),
                    'Moves_UCI': [x.uci() for x in game.mainline_moves()] # Convert moves to UCI format
                }
                games_data.append(game_info)
                game_idx += 1

        games_df = pd.DataFrame(games_data)
        print(f"\nDataFrame of {len(games_df)} games created successfully!")

        blunders_found = []

        BLUNDER_CP_THRESHOLD = 50

        print(f"\nStarting blunder analysis with Stockfish (threshold: >{BLUNDER_CP_THRESHOLD} CP loss).")
        print("This will take a while, especially for large archives, as each move is analyzed...")

        for index, game_row in tqdm.tqdm(games_df.iterrows(), total=len(games_df), desc="Analyzing games for blunders"):
            board = chess.Board()

            engine.set_fen_position(board.fen())
            initial_eval_dict = engine.get_evaluation()
            prev_cp_value = get_cp_value(initial_eval_dict)

            for move_num, move_uci in enumerate(game_row['Moves_UCI'], 1):

                try:
                    move = chess.Move.from_uci(move_uci)
                    player_to_move = "White" if board.turn == chess.WHITE else "Black"

                    fen_before_move = board.fen()

                    if move in board.legal_moves:
                        board.push(move)
                        fen_after_move = board.fen()

                        engine.set_fen_position(fen_after_move)
                        current_eval_dict = engine.get_evaluation()
                        current_cp_value = get_cp_value(current_eval_dict)

                        cp_change = prev_cp_value - current_cp_value

                        is_blunder = False
                        centipawn_loss = 0

                        if player_to_move == "White":
                            if cp_change > BLUNDER_CP_THRESHOLD:
                                is_blunder = True
                                centipawn_loss = cp_change
                        else:
                            if cp_change < -BLUNDER_CP_THRESHOLD:
                                is_blunder = True
                                centipawn_loss = abs(cp_change)

                        if is_blunder:
                            blunders_found.append({
                                'Game_Index': game_row['game_index'],
                                'Event': game_row['Event'],
                                'White': game_row['White'],
                                'Black': game_row['Black'],
                                'Result': game_row['Result'],
                                'Move_Number': move_num,
                                'Player_Who_Blundered': player_to_move,
                                'Move_UCI': move_uci,
                                'FEN_Before_Blunder': fen_before_move,
                                'FEN_After_Blunder': fen_after_move,
                                'Eval_Before_Blunder_CP': prev_cp_value,
                                'Eval_After_Blunder_CP': current_cp_value,
                                'Centipawn_Loss': centipawn_loss
                            })

                        prev_cp_value = current_cp_value
                    else:
                        break

                except ValueError:
                    break
                except Exception:
                    break

        blunders_df = pd.DataFrame(blunders_found)

        print("\nAnalysis complete!")

        if not blunders_df.empty:
            print(f"\n--- Found {len(blunders_df)} Blunders! ---")

            print("Classifying blunders...")
            blunders_df['Blunder_Type'] = blunders_df.apply(lambda row: classify_blunder(row, engine), axis=1)

            blunders_df['Move_Number'] = np.ceil(blunders_df['Move_Number']/2).astype(int)
            print(blunders_df[['Game_Index', 'White','Move_Number', 'Black','Move_UCI',
                               'Player_Who_Blundered', 'Centipawn_Loss', 'Blunder_Type',
                               'Eval_Before_Blunder_CP', 'Eval_After_Blunder_CP']])

            user_blunders_df = blunders_df[
                ((blunders_df['White'] == user) & (blunders_df['Player_Who_Blundered'] == 'White')) |
                ((blunders_df['Black'] == user) & (blunders_df['Player_Who_Blundered'] == 'Black'))
            ]

            if not user_blunders_df.empty:


                forkCount = (user_blunders_df['Blunder_Type'] == "Fork Blunder").sum()
                hangingCount = (user_blunders_df['Blunder_Type'] == "Hanging Piece").sum()
                otherCount = (user_blunders_df['Blunder_Type'] == "Positional/Other Blunder").sum()
                pinCount = (user_blunders_df['Blunder_Type'] == "Pin/Skewer Blunder").sum()

                print(f"\n--- Blunder Summary for {user} ---")
                print(f"Forks: {forkCount}")
                print(f"Hanging Pieces: {hangingCount}")
                print(f"Pins/Skewers: {pinCount}")
                print(f"Positional/Other: {otherCount}")

                to_markdown = generate_gemini_advice(forkCount, hangingCount, otherCount, pinCount)
                print("\n--- Gemini Chess Coach Advice ---")
                print(to_markdown)
                print("---------------------------------")
            else:
                print(f"\nNo blunders found for user '{user}'.")

        else:
            print(f"\nNo blunders (with > {BLUNDER_CP_THRESHOLD} CP loss) found in the analyzed games.")

    except FileNotFoundError:
        print(f"Error: The PGN file '{pgn_file_path}' was not found.")
    except Exception as e:
        print(f"An unexpected error occurred during PGN processing or analysis: {e}")


