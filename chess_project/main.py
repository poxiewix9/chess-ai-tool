
import chess.pgn
import pandas as pd
import math
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 1000)

import tqdm
import os
from stockfish import Stockfish


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

    games_data = []
    print("\nProcessing games from PGN file (this may take a moment)...")

    try:
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
                    'Moves_UCI': [x.uci() for x in game.mainline_moves()]
                }
                games_data.append(game_info)
                game_idx += 1



        games_df = pd.DataFrame(games_data)
        print(f"\nDataFrame of {len(games_df)} games created successfully!")

        blunders_found = []
        print("\nStarting blunder analysis with Stockfish (this will take a while, especially for large archives)...")

        for index, game_row in tqdm.tqdm(games_df.iterrows(), total=len(games_df), desc="Analyzing games for blunders"):
            board = chess.Board()

            engine.set_fen_position(board.fen())
            initial_eval_dict = engine.get_evaluation()
            prev_cp_value = get_cp_value(initial_eval_dict)

            for move_num, move_uci in enumerate(game_row['Moves_UCI'], 1):
                try:
                    move = chess.Move.from_uci(move_uci)
                    math.floor(move_num)
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
                            if cp_change > 100:
                                is_blunder = True
                                centipawn_loss = cp_change
                        else:

                            if cp_change < -100:
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

                except ValueError as e:
                    break
                except Exception as e:
                    break

        blunders_df = pd.DataFrame(blunders_found)

        print("\nAnalysis complete!")

        if not blunders_df.empty:
            print(f"\n--- Found {len(blunders_df)} Blunders! ---")

            print(blunders_df[['Game_Index', 'Black', 'Move_Number',
                               'Player_Who_Blundered', 'Move_UCI', 'Centipawn_Loss',
                               'Eval_Before_Blunder_CP', 'Eval_After_Blunder_CP']])

        else:
            print("\nNo blunders (with > 100 CP loss) found in the analyzed games.")

    except FileNotFoundError:
        print(f"Error: The PGN file '{pgn_file_path}' was not found.")
    except Exception as e:
        print(f"An unexpected error occurred during PGN processing or analysis: {e}")