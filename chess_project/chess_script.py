import streamlit as st
import json
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import google.generativeai as genai
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import chess
import chess.pgn
import math
import tqdm
import os
from stockfish import Stockfish
import io


GEMINI_API_KEY = "secret"
genai.configure(api_key=GEMINI_API_KEY)

STOCKFISH_EXECUTABLE_PATH = "/opt/homebrew/bin/stockfish"



def generate_gemini_advice_blunders(forkCount, hangingCount, otherCount, pinCount):
    prompt = f"""
    You are a chess coach, give advice to the user based on the following data about their blunders:
    - Blunders regarding forks: {forkCount} times.
    - Blunders regarding hanging pieces: {hangingCount} times.
    - Blunders regarding missed tactics and positional errors: {otherCount} times.
    - Blunders regarding pins and skewers: {pinCount} times.

    Provide actionable advice focusing on common patterns for these types of blunders. Be concise and encouraging.
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"GEMINI ERROR: {e}"


def get_cp_value(evaluation):
    if evaluation is None:
        return 0
    if evaluation['type'] == 'cp':
        return evaluation['value']
    elif evaluation['type'] == 'mate':
        return 100000 * (1 if evaluation['value'] > 0 else -1)
    return 0


def classify_blunder(blunder_row, stockfish_engine):
    blunder_type = "Positional/Other Blunder"
    board_after_blunder = chess.Board(blunder_row['FEN_After_Blunder'])
    blundering_player_color = chess.WHITE if blunder_row['Player_Who_Blundered'] == 'White' else chess.BLACK

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
                    # Check for Hanging Piece first
                    if board_after_blunder.is_capture(opponent_best_move):
                        captured_piece_square = opponent_best_move.to_square
                        captured_piece = board_after_blunder.piece_at(captured_piece_square)
                        if captured_piece and captured_piece.color == blundering_player_color and captured_piece.piece_type != chess.KING:
                            # CORRECTED LOGIC: Check for the blundering player's own defenders.
                            if not board_after_blunder.attackers(blundering_player_color, captured_piece_square):
                                return "Hanging Piece"

                    # Push the move to check for forks
                    temp_board_after_opponent_move.push(opponent_best_move)

                    # Check for Fork
                    forking_piece_square = opponent_best_move.to_square
                    attacked_valuable_pieces_count = 0
                    # Note: We check attacks from the square the opponent's piece moved TO
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
    except (ValueError, Exception):
        pass
    return blunder_type


def analyze_blunders(games_data, username, stockfish_engine):
    st.subheader(f"Blunder Analysis for {username}")
    blunders_found = []
    BLUNDER_CP_THRESHOLD = 50
    my_bar = st.progress(0, text="Analyzing game moves for blunders...")

    for game_idx, game_info in enumerate(games_data):
        board = chess.Board()
        stockfish_engine.set_fen_position(board.fen())
        prev_cp_value = get_cp_value(stockfish_engine.get_evaluation())
        for move_num, move_uci in enumerate(game_info['Moves_UCI'], 1):
            try:
                move = chess.Move.from_uci(move_uci)
                player_to_move = "White" if board.turn == chess.WHITE else "Black"
                fen_before_move = board.fen()
                if move in board.legal_moves:
                    board.push(move)
                    fen_after_move = board.fen()
                    stockfish_engine.set_fen_position(fen_after_move)
                    current_cp_value = get_cp_value(stockfish_engine.get_evaluation())
                    cp_change = prev_cp_value - current_cp_value
                    is_blunder, centipawn_loss = False, 0
                    if player_to_move == "White":
                        if cp_change > BLUNDER_CP_THRESHOLD:
                            is_blunder, centipawn_loss = True, cp_change
                    else:
                        if cp_change < -BLUNDER_CP_THRESHOLD:
                            is_blunder, centipawn_loss = True, abs(cp_change)
                    if is_blunder:
                        blunders_found.append({
                            'Game_Index': game_idx, 'Event': game_info['Event'], 'Site': game_info['Site'],
                            'Date': game_info['Date'], 'White': game_info['White'], 'Black': game_info['Black'],
                            'Result': game_info['Result'], 'Move_Number': move_num,
                            'Player_Who_Blundered': player_to_move, 'Move_UCI': move_uci,
                            'FEN_Before_Blunder': fen_before_move, 'FEN_After_Blunder': fen_after_move,
                            'Eval_Before_Blunder_CP': prev_cp_value, 'Eval_After_Blunder_CP': current_cp_value,
                            'Centipawn_Loss': centipawn_loss
                        })
                    prev_cp_value = current_cp_value
                else:
                    break
            except (ValueError, Exception):
                break
        my_bar.progress((game_idx + 1) / len(games_data), text=f"Analyzing game {game_idx + 1}/{len(games_data)}")

    my_bar.empty()
    st.write("Analysis complete!")
    blunders_df = pd.DataFrame(blunders_found)
    if not blunders_df.empty:
        st.write("Classifying blunder types...")
        blunders_df['Blunder_Type'] = blunders_df.apply(lambda row: classify_blunder(row, stockfish_engine), axis=1)
        blunders_df['Move_Number_Display'] = np.ceil(blunders_df['Move_Number'] / 2).astype(int)
        user_blunders_df = blunders_df[
            ((blunders_df['White'].str.lower() == username) & (blunders_df['Player_Who_Blundered'] == 'White')) | (
                        (blunders_df['Black'].str.lower() == username) & (
                            blunders_df['Player_Who_Blundered'] == 'Black'))]
    else:
        user_blunders_df = pd.DataFrame()

    if not user_blunders_df.empty:
        st.subheader("Game-by-Game Blunder Details")
        st.caption("This section only lists games where at least one blunder was found for the specified user.")
        unique_game_indices = user_blunders_df['Game_Index'].unique()
        games_data_map = {game['game_index']: game for game in games_data}
        for game_idx in unique_game_indices:
            game_info = games_data_map.get(game_idx)
            if not game_info: continue
            game_blunders = user_blunders_df[user_blunders_df['Game_Index'] == game_idx].copy()
            game_board = chess.Board()
            for move_uci in game_info['Moves_UCI']:
                try:
                    move = chess.Move.from_uci(move_uci)
                    if move in game_board.legal_moves:
                        game_board.push(move)
                    else:
                        break
                except ValueError:
                    break
            board_svg = chess.svg.board(board=game_board, size=300)
            with st.expander(
                    f"Game {game_idx + 1}: {game_info['White']} vs. {game_info['Black']} - Result: {game_info['Result']}"):
                game_url = game_info['Site']
                if game_url and "chess.com" in game_url:
                    st.markdown(f"**[View Game on Chess.com]({game_url})**")
                col_board, col_details = st.columns([0.4, 0.6])
                with col_board:
                    st.markdown(board_svg, unsafe_allow_html=True)
                with col_details:
                    st.write(f"**Event:** {game_info['Event']}")
                    st.write(f"**White:** {game_info['White']} | **Black:** {game_info['Black']}")
                    st.write(f"**Result:** {game_info['Result']}")
                    st.write(f"**Total Moves:** {len(game_info['Moves_UCI'])}")
                st.markdown("---")
                st.markdown(f"**Blunders by {username} in this game:**")
                display_df = game_blunders[['Move_Number_Display', 'Move_UCI', 'Centipawn_Loss', 'Blunder_Type']].copy()
                display_df.rename(
                    columns={'Move_Number_Display': 'Move Number', 'Move_UCI': 'Move', 'Centipawn_Loss': 'CP Loss',
                             'Blunder_Type': 'Type'}, inplace=True)
                st.dataframe(display_df.style.set_properties(**{'font-size': '12px'}), hide_index=True)
    else:
        st.info(f"No blunders specifically attributed to '{username}' found in these games.")

    if not user_blunders_df.empty:
        fork_count = (user_blunders_df['Blunder_Type'] == "Fork Blunder").sum()
        hanging_count = (user_blunders_df['Blunder_Type'] == "Hanging Piece").sum()
        other_count = (user_blunders_df['Blunder_Type'] == "Positional/Other Blunder").sum()
        pin_count = (user_blunders_df['Blunder_Type'] == "Pin/Skewer Blunder").sum()
        checkmate_blunder_count = (user_blunders_df['Blunder_Type'] == "Checkmate Blunder").sum()
        st.subheader(f"Blunder Summary for {username}")
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric(label="Forks", value=fork_count);
        col2.metric(label="Hanging Pieces", value=hanging_count);
        col3.metric(label="Pins/Skewers", value=pin_count);
        col4.metric(label="Positional/Other", value=other_count);
        col5.metric(label="Checkmate Blunders", value=checkmate_blunder_count)
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("Chess Coach Advice on Blunders")
        with st.container(border=True):
            advice = generate_gemini_advice_blunders(fork_count, hanging_count, other_count, pin_count)
            st.markdown(advice)



def get_json_from_url_selenium(url, driver):
    try:
        driver.get(url)
        time.sleep(2)
        pre_element = driver.find_element("tag name", "pre")
        json_data = pre_element.text
        return json.loads(json_data)
    except Exception as e:
        st.error(f"Error loading {url}: {e}")
        return None


def generate_gemini_advice_openings(opening_full_name, stats, rating, example_moves):
    prompt = f"""
    You're a chess coach. Here's a player's performance in the opening "{opening_full_name}":

    - Games Played: {stats['games']}
    - Wins: {stats['wins']}
    - Losses: {stats['losses']}
    - Draws: {stats['draws']}
    - Approximate Rating: {rating}
    - Example Opening Sequence: {example_moves}

    Based on this data, provide personalized advice.
    - If performance is poor, focus on tips to improve, common traps, or mistakes.
    - If performance is good, suggest ways to deepen their understanding, introduce key strategic plans, or mention related variations to explore.
    Give 1-2 concise action steps and be encouraging.
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"GEMINI ERROR: {e}"


def analyze_openings(games, player_username):
    grouped_openings = {}
    player_wins, player_losses, player_draws = 0, 0, 0
    processed_games_count = 0
    player_rating = 0

    opening_groups = {
        "Sicilian Defense": ["Sicilian"],
        "Indian Game": ["Indian", "Grünfeld", "Benoni", "Benko", "Catalan"],
        "French Defense": ["French"],
        "Caro-Kann Defense": ["Caro-Kann"],
        "Queen's Gambit": ["Queen's Gambit", "Slav", "Albin", "Chigorin", "Tarrasch Defense"],
        "Queen's Pawn Opening": ["Queen's Pawn"],
        "Ruy Lopez": ["Ruy Lopez", "Spanish"],
        "Italian Game": ["Italian Game", "Giuoco Piano", "Evans Gambit"],
        "King's Pawn Opening": ["King's Pawn", "Philidor", "Petrov", "Scotch", "Vienna", "Latvian Gambit",
                                "Bishop's Opening"],
        "Four Knights Game": ["Four Knights"],
        "Scandinavian Defense": ["Scandinavian", "Center Counter"],
        "Alekhine's Defense": ["Alekhine"],
        "Pirc Defense": ["Pirc"],
        "Modern Defense": ["Modern"],
        "English Opening": ["English"],
        "Reti Opening": ["Reti"],
        "Nimzowitsch-Larsen Attack": ["Larsen", "Nimzowitsch-Larsen"],
    }
    group_order = [
        "Queen's Gambit", "Queen's Pawn Opening", "Sicilian Defense", "Indian Game", "French Defense",
        "Caro-Kann Defense",
        "Ruy Lopez", "Italian Game", "Four Knights Game", "Scandinavian Defense", "Alekhine's Defense",
        "Pirc Defense", "Modern Defense", "King's Pawn Opening", "English Opening", "Reti Opening",
        "Nimzowitsch-Larsen Attack"
    ]

    for game in games:
        # --- Player and Result Logic ---
        white, black = game.get("white", {}), game.get("black", {})
        player_outcome = "unknown"

        if white.get("username", "").lower() == player_username:
            player_rating = white.get("rating", player_rating)
            player_outcome = white.get("result")
        elif black.get("username", "").lower() == player_username:
            player_rating = black.get("rating", player_rating)
            player_outcome = black.get("result")
        else:
            continue

        processed_games_count += 1

        final_opening_name = "Unknown Opening"
        eco_url = game.get("eco")
        pgn_str = game.get("pgn", "")

        if eco_url and "chess.com/openings" in eco_url:
            match = re.search(r'chess\.com/openings/([^/?]+)', eco_url)
            if match:
                raw_name_part = match.group(1).replace('_', ' ').replace('-', ' ')
                final_opening_name = ' '.join(word.capitalize() for word in raw_name_part.split())
        elif pgn_str:
            pgn_io = io.StringIO(pgn_str)
            try:
                pgn_game = chess.pgn.read_game(pgn_io)
                if pgn_game:
                    pgn_eco_url = pgn_game.headers.get("ECOUrl")
                    if pgn_eco_url and "chess.com/openings" in pgn_eco_url:
                        match = re.search(r'chess\.com/openings/([^/?]+)', pgn_eco_url)
                        if match:
                            raw_name_part = match.group(1).replace('_', ' ').replace('-', ' ')
                            final_opening_name = ' '.join(word.capitalize() for word in raw_name_part.split())
                    else:
                        final_opening_name = pgn_game.headers.get("Opening", "Unknown Opening")
            except Exception:
                pass

        loss_outcomes = ["lose", "resigned", "timeout", "abandoned", "checkmated", "disconnected"]
        draw_outcomes = ["draw", "agreed", "repetition", "stalemate", "insufficientmaterial", "50move"]

        main_opening_key = None
        normalized_final_name = final_opening_name.lower().replace("'", "")

        for group_name in group_order:
            normalized_keywords = [kw.lower().replace("'", "") for kw in opening_groups[group_name]]
            if any(kw in normalized_final_name for kw in normalized_keywords):
                main_opening_key = group_name
                break

        if not main_opening_key:
            if final_opening_name.lower() in ["undefined", "unknown opening"]:
                main_opening_key = "Unclassified Opening"
            else:
                main_opening_key = final_opening_name

        specific_variation_name = final_opening_name if main_opening_key != final_opening_name else "Main Line"

        if main_opening_key not in grouped_openings:
            grouped_openings[main_opening_key] = {"total_games": 0, "total_wins": 0, "total_losses": 0,
                                                  "total_draws": 0, "variations": {}}

        stats = grouped_openings[main_opening_key]
        stats["total_games"] += 1
        if player_outcome == "win":
            stats["total_wins"] += 1;
            player_wins += 1
        elif player_outcome in loss_outcomes:
            stats["total_losses"] += 1;
            player_losses += 1
        elif player_outcome in draw_outcomes:
            stats["total_draws"] += 1;
            player_draws += 1

        if specific_variation_name not in stats["variations"]:
            stats["variations"][specific_variation_name] = {"name": final_opening_name, "games": 0, "wins": 0,
                                                            "losses": 0, "draws": 0}

        var_stats = stats["variations"][specific_variation_name]
        var_stats["games"] += 1
        if player_outcome == "win":
            var_stats["wins"] += 1
        elif player_outcome in loss_outcomes:
            var_stats["losses"] += 1
        elif player_outcome in draw_outcomes:
            var_stats["draws"] += 1

    # --- Display Logic ---
    st.subheader(f"Player Summary for {player_username}")
    col_sum1, col_sum2, col_sum3, col_sum4 = st.columns(4)
    col_sum1.metric("Total Games Analyzed", processed_games_count);
    col_sum2.metric("Wins", player_wins);
    col_sum3.metric("Losses", player_losses);
    col_sum4.metric("Draws", player_draws)
    st.info(f"Estimated Rating: **{player_rating}**")
    st.subheader("Opening Repertoire Breakdown")
    if not grouped_openings:
        st.info("No openings identified for detailed breakdown.");
        return

    sorted_main_openings = sorted(grouped_openings.items(), key=lambda item: item[1]["total_games"], reverse=True)
    for main_op_name, main_op_data in sorted_main_openings:
        with st.expander(f"**{main_op_name}** ({main_op_data['total_games']} games)", expanded=False):
            st.markdown(f"**Overall performance for {main_op_name}:**")
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            col_m1.metric("Games", main_op_data['total_games']);
            col_m2.metric("Wins", main_op_data['total_wins']);
            col_m3.metric("Losses", main_op_data['total_losses']);
            col_m4.metric("Draws", main_op_data['total_draws'])
            if main_op_data['variations']:
                st.markdown("---");
                st.markdown("**Specific variations played:**")
                sorted_variations = sorted(main_op_data['variations'].items(), key=lambda item: item[1]['games'],
                                           reverse=True)
                for var_name, var_stats in sorted_variations:
                    with st.container(border=True):
                        display_name = main_op_name if var_name == "Main Line" else var_name
                        st.markdown(f"**Variation:** {display_name}")
                        st.markdown(
                            f"Games: {var_stats['games']} | Wins: {var_stats['wins']} | Losses: {var_stats['losses']} | Draws: {var_stats['draws']}")

                        pgn = ""
                        for game in games:
                            if game.get('eco', '').endswith(var_stats['name'].replace(' ', '-')):
                                pgn = game.get("pgn", "")
                                break
                        if not pgn:
                            pgn = next((g.get("pgn", "") for g in games if final_opening_name == var_stats['name']), "")

                        move_sequence = ""
                        if pgn:
                            for line in pgn.splitlines():
                                line_stripped = line.strip()
                                if line_stripped and not line_stripped.startswith("["):
                                    move_sequence = line_stripped
                                    break

                        advice = generate_gemini_advice_openings(var_stats['name'], var_stats, player_rating,
                                                                 move_sequence)
                        st.markdown("---")
                        st.markdown(f"**Advice for {display_name}:**")
                        st.markdown(advice)


# --- Main Streamlit Application Logic ---

def main():
    st.set_page_config(page_title="Chess Analyzer", page_icon="♟️", layout="wide")
    st.title("Chess Analyzer: Openings & Blunders")
    st.write("Enter your Chess.com username to get personalized insights on your openings and analyze your blunders.")

    engine = None
    try:
        engine = Stockfish(STOCKFISH_EXECUTABLE_PATH, parameters={"Contempt": 0, "Threads": 4, "Hash": 256})
        st.success(f"Stockfish engine initialized successfully from: {STOCKFISH_EXECUTABLE_PATH}")
    except Exception as e:
        st.error(
            f"Error initializing Stockfish engine. Please ensure the path is correct and Stockfish is installed. Error: {e}")
        st.stop()

    username = st.text_input("Chess.com Username", key="username_input").strip().lower()

    st.info("💡 More games provide a more detailed analysis but will take longer to process. \n\nAs a guide, analyzing 100 games can take 3-5 minutes, primarily due to the move-by-move blunder check.")
    games_to_fetch_count = st.number_input(
        "Select the number of recent games to analyze",
        min_value=5,
        max_value=200,
        value=20,
        step=5,
        key="games_count_input"
    )

    if st.button("Analyze My Games", key="analyze_button") and username:
        with st.spinner("Fetching games and analyzing... This might take a moment, especially for blunder analysis."):
            chrome_options = Options()
            chrome_options.add_argument("--headless");
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage");
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument(
                "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
            chrome_options.add_argument("--log-level=3")

            driver = None
            try:
                driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
                archives_url = f"https://api.chess.com/pub/player/{username}/games/archives"
                archives_data = get_json_from_url_selenium(archives_url, driver)

                if not archives_data or "archives" not in archives_data:
                    st.error(
                        "Failed to fetch game archives. Please check the username or ensure the user has public archives.")
                    return

                all_games = []
                for archive_url in reversed(archives_data["archives"]):
                    if len(all_games) >= games_to_fetch_count: break
                    st.info(f"Fetching games from: {archive_url.split('/')[-2]}/{archive_url.split('/')[-1]}")
                    archive_data = get_json_from_url_selenium(archive_url, driver)
                    if archive_data and "games" in archive_data:
                        games_from_this_archive = archive_data["games"]
                        num_to_add = min(len(games_from_this_archive), games_to_fetch_count - len(all_games))
                        all_games.extend(games_from_this_archive[-num_to_add:])
                    time.sleep(0.5)

                if all_games:
                    recent_games = all_games[-games_to_fetch_count:]
                    blunder_analysis_games_data = []
                    for idx, game in enumerate(recent_games):
                        pgn_moves = []
                        pgn_text = game.get("pgn", "")
                        try:
                            pgn_game = chess.pgn.read_game(io.StringIO(pgn_text))
                            if pgn_game: pgn_moves = [x.uci() for x in pgn_game.mainline_moves()]
                        except Exception as e:
                            st.warning(f"Could not parse PGN for game {idx}: {e}")

                        event_name = game.get("time_class", "Live Game").replace("_", " ").capitalize()

                        blunder_analysis_games_data.append({
                            'game_index': idx, 'Event': event_name, 'Site': game.get("url", "N/A"),
                            'Date': game.get("end_time", "N/A"), 'White': game.get("white", {}).get("username", "N/A"),
                            'Black': game.get("black", {}).get("username", "N/A"),
                            'Result': game.get("white", {}).get("result", "N/A"), 'Moves_UCI': pgn_moves
                        })

                    st.success(f"Successfully fetched {len(recent_games)} most recent games for analysis!")

                    tab1, tab2 = st.tabs(["Opening Analysis", "Blunder Analysis"])
                    with tab1:
                        analyze_openings(recent_games, username)
                    with tab2:
                        analyze_blunders(blunder_analysis_games_data, username, engine)
                else:
                    st.warning("No games found for this username.")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
                st.info("Common issues: Incorrect username, network problems, or temporary Chess.com API issues.")
            finally:
                if driver:
                    driver.quit()
                    st.write("Browser closed.")


if __name__ == "__main__":
    print("im gay")
    main()