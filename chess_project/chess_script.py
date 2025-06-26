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


GEMINI_API_KEY = "AIzaSyB43ECTgD2_8IvZcI2x1ZNtSyIirkz0sNs"
genai.configure(api_key=GEMINI_API_KEY)


def get_json_from_url_selenium(url, driver):
    try:
        driver.get(url)
        time.sleep(4)
        pre_element = driver.find_element("tag name", "pre")
        json_data = pre_element.text
        return json.loads(json_data)
    except Exception as e:
        st.error(f"Error loading {url}: {e}")
        return None


def generate_gemini_advice(opening_name, stats, rating, example_moves):
    prompt = f"""
You're a chess coach. Here's a player's performance in the opening "{opening_name}":

- Games Played: {stats['games']}
- Wins: {stats['wins']}
- Losses: {stats['losses']}
- Draws: {stats['draws']}
- Approximate Rating: {rating}
- Example Opening Sequence: {example_moves}

Give this player personalized tips on how to improve in this opening. Mention common traps or mistakes they might be falling for, and give 1–2 action steps they should take to study this opening more effectively.
"""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"GEMINI ERROR: {e}"


def analyze_games(games, player_username):
    opening_stats = {}
    total_games = len(games)
    player_wins = 0
    player_losses = 0
    player_draws = 0
    player_rating = 0

    for game in games:
        eco = game.get("eco", "Unknown ECO")
        opening_data = game.get("opening", {})

        opening_name = opening_data.get("name", "")
        opening_url = opening_data.get("url", "")

        if not opening_name or any(term.lower() in opening_name.lower() for term in ["unknown", "undefined", "pawn", "queen's", "king's", "règle"]):
            if opening_url and "chess.com/openings/" in opening_url:
                try:
                    match = re.search(r'chess\.com/openings/(.*)', opening_url)
                    if match:
                        extracted_name_part = match.group(1)
                        extracted_name_part = re.sub(r'(-[0-9]+\.{3}[a-z0-h][0-9]?|-eco-[A-Z][0-9]+)$', '', extracted_name_part)
                        extracted_name = extracted_name_part.replace('-', ' ').replace('_', ' ').strip()
                        opening_name = ' '.join(word.capitalize() for word in extracted_name.split())
                except Exception:
                    opening_name = "Unknown Opening (URL Parse Error)"

            if not opening_name or "Unknown Opening" in opening_name:
                opening_name = f"ECO {eco}"

        pgn = game.get("pgn", "")
        move_sequence = ""
        for line in pgn.splitlines():
            line_stripped = line.strip()
            if line_stripped and not line_stripped.startswith("["):
                move_sequence = line_stripped
                break

        white = game.get("white", {})
        black = game.get("black", {})

        current_game_rating = 0
        player_outcome = "unknown"

        if white.get("username", "").lower() == player_username:
            current_game_rating = white.get("rating", 0)
            player_outcome = white.get("result")
        elif black.get("username", "").lower() == player_username:
            current_game_rating = black.get("rating", 0)
            player_outcome = black.get("result")
        else:
            continue

        if current_game_rating > 0:
            player_rating = current_game_rating

        loss_outcomes = ["lose", "resigned", "timeout", "abandoned", "checkmated", "disconnected"]

        draw_outcomes = ["draw", "agreed", "repetition", "stalemate", "insufficientmaterial", "50move"]

        if opening_name not in opening_stats:
            opening_stats[opening_name] = {
                "name": opening_name,
                "url": opening_url,
                "games": 0,
                "wins": 0,
                "losses": 0,
                "draws": 0,
                "examples": []
            }

        opening_stats[opening_name]["games"] += 1

        if player_outcome == "win":
            opening_stats[opening_name]["wins"] += 1
            player_wins += 1
        elif player_outcome in loss_outcomes:
            opening_stats[opening_name]["losses"] += 1
            player_losses += 1
        elif player_outcome in draw_outcomes:
            opening_stats[opening_name]["draws"] += 1
            player_draws += 1


        if move_sequence and len(opening_stats[opening_name]["examples"]) < 3:
            if move_sequence not in opening_stats[opening_name]["examples"]:
                opening_stats[opening_name]["examples"].append(move_sequence)

    st.subheader("Player Summary")
    st.write(f"Total games analyzed: {total_games}")
    st.write(f"Wins: {player_wins} | Losses: {player_losses} | Draws: {player_draws}")
    st.write(f"Estimated Rating: {player_rating}")

    st.subheader("Performance Visualizations")


    colors = {
        'win': '#4CAF50',
        'lose': '#F44336',   # Red
        'draw': '#FFEB3B',   # Yellow
        'bar': '#2196F3',
        'text': '#E0E0E0'    # Light grey for text on dark background
    }
    plt.rcParams.update({
        'text.color': colors['text'],
        'axes.labelcolor': colors['text'],
        'xtick.color': colors['text'],
        'ytick.color': colors['text'],
        'axes.facecolor': '#262730',
        'figure.facecolor': '#262730',
        'grid.color': '#424242'
    })



    if total_games > 0:
        labels = ['Wins', 'Losses', 'Draws']
        sizes = [player_wins, player_losses, player_draws]
        pie_colors = [colors['win'], colors['lose'], colors['draw']]

        filtered_labels = [label for i, label in enumerate(labels) if sizes[i] > 0]
        filtered_sizes = [size for size in sizes if size > 0]
        filtered_pie_colors = [color for i, color in enumerate(pie_colors) if sizes[i] > 0]

        if filtered_sizes:
            fig1, ax1 = plt.subplots(figsize=(8, 8))
            wedges, texts, autotexts = ax1.pie(filtered_sizes,
                                               labels=filtered_labels,
                                               autopct='%1.1f%%',
                                               colors=filtered_pie_colors,
                                               startangle=90,
                                               pctdistance=0.85,
                                               wedgeprops={'edgecolor': 'black', 'linewidth': 0.5})

            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(12)
            for text in texts:
                text.set_color(colors['text'])
                text.set_fontsize(12)

            ax1.axis('equal')
            ax1.set_title('Overall Game Outcome Distribution', fontsize=16, color=colors['text'])
            st.pyplot(fig1)
            st.caption("Distribution of your game outcomes (Wins, Losses, Draws).")
        else:
            st.info("No game outcomes to visualize in the pie chart.")
    else:
        st.info("No games to visualize yet.")


    sorted_openings_list = sorted(opening_stats.values(), key=lambda x: x["games"], reverse=True)
    filtered_openings = [op for op in sorted_openings_list if op['games'] > 0]

    if filtered_openings:
        N_top_openings = min(5, len(filtered_openings))
        top_n_openings_data = filtered_openings[:N_top_openings]
        df_openings = pd.DataFrame(top_n_openings_data)

        df_openings['win_rate'] = (df_openings['wins'] / df_openings['games'] * 100).fillna(0)
        df_openings['loss_rate'] = (df_openings['losses'] / df_openings['games'] * 100).fillna(0)
        df_openings['draw_rate'] = (df_openings['draws'] / df_openings['games'] * 100).fillna(0)

        # 2. Top N Openings by Games Played Bar Chart
        st.subheader(f"Top {N_top_openings} Most Played Openings")
        fig2, ax2 = plt.subplots(figsize=(10, 6))
        ax2.barh(df_openings['name'], df_openings['games'], color=colors['bar'])
        ax2.set_xlabel("Number of Games", fontsize=12)
        ax2.set_ylabel("Opening Name", fontsize=12)
        ax2.set_title(f"Most Frequently Played Chess Openings (Top {N_top_openings})", fontsize=14, color=colors['text'])
        ax2.invert_yaxis()
        ax2.tick_params(axis='x', labelsize=10)
        ax2.tick_params(axis='y', labelsize=10)
        plt.tight_layout()
        st.pyplot(fig2)
        st.caption("Shows how many times you've played your most common openings.")

        # 3. Win/Loss/Draw Rates for Top Openings Bar Chart
        st.subheader(f"Performance in Top {N_top_openings} Openings (Rates)")
        fig3, ax3 = plt.subplots(figsize=(12, 7))

        bar_width = 0.25
        index = np.arange(len(df_openings))

        bar1 = ax3.bar(index - bar_width, df_openings['win_rate'], bar_width, label='Win Rate (%)', color=colors['win'])
        bar2 = ax3.bar(index, df_openings['loss_rate'], bar_width, label='Loss Rate (%)', color=colors['lose'])
        bar3 = ax3.bar(index + bar_width, df_openings['draw_rate'], bar_width, label='Draw Rate (%)', color=colors['draw'])

        ax3.set_xlabel("Opening Name", fontsize=12)
        ax3.set_ylabel("Rate (%)", fontsize=12)
        ax3.set_title(f"Win/Loss/Draw Rates in Top {N_top_openings} Openings", fontsize=14, color=colors['text'])
        ax3.set_xticks(index)
        ax3.set_xticklabels(df_openings['name'], rotation=45, ha='right', fontsize=10)
        ax3.legend(fontsize=10)
        ax3.set_ylim(0, 100)
        ax3.tick_params(axis='x', labelsize=10)
        ax3.tick_params(axis='y', labelsize=10)
        plt.tight_layout()
        st.pyplot(fig3)
        st.caption("Percentage of Wins, Losses, and Draws for your most played openings.")
    else:
        st.info("Not enough game data for opening-specific visualizations.")


    st.subheader("Personalized Opening Advice")
    advice_count = 0
    for opening_name, stats in filtered_openings:
        if advice_count >= 3:
            break
        if stats["games"] >= 3:
            if stats["losses"] > stats["wins"] and stats["losses"] > stats["draws"]:
                example_moves = stats["examples"][0] if stats["examples"] else "No example moves available."
                advice = generate_gemini_advice(opening_name, stats, player_rating, example_moves)
                with st.expander(f"💡 Advice for **{opening_name}** (Losses: {stats['losses']})"):
                    st.markdown(advice)
                advice_count += 1
            elif stats["draws"] > stats["wins"] and stats["losses"] <= stats["wins"] and advice_count < 3:
                example_moves = stats["examples"][0] if stats["examples"] else "No example moves available."
                advice = generate_gemini_advice(opening_name, stats, player_rating, example_moves)
                with st.expander(f"🤔 Advice for **{opening_name}** (Draws: {stats['draws']})"):
                    st.markdown(advice)
                advice_count += 1
            elif stats["wins"] > stats["losses"] and stats["wins"] > stats["draws"] and advice_count < 3:
                st.success(f"🎉 Great performance in **{opening_name}**! Keep up the good work. (Wins: {stats['wins']})")
                advice_count += 1
            elif advice_count < 3:
                st.info(f"📊 Stats for **{opening_name}**: Games: {stats['games']}, Wins: {stats['wins']}, Losses: {stats['losses']}, Draws: {stats['draws']}")
                advice_count += 1

    if advice_count == 0:
        st.info("No specific opening advice generated yet. Try playing more games or explore different openings!")


def main():
    st.set_page_config(page_title="Chess Opening Analyzer", page_icon="♟️", layout="wide")
    st.title("♟️ Chess Opening Analyzer")
    st.write("Enter your Chess.com username to get personalized insights on your openings.")

    username = st.text_input("Chess.com Username").strip().lower()

    if st.button("Analyze My Games") and username:
        with st.spinner("Analyzing games... This might take a moment, especially for users with many games."):
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
            chrome_options.add_argument("--log-level=3")

            driver = None
            try:
                driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

                archives_url = f"https://api.chess.com/pub/player/{username}/games/archives"
                archives_data = get_json_from_url_selenium(archives_url, driver)

                if not archives_data or "archives" not in archives_data:
                    st.error("Failed to fetch game archives. Please check your username or if the user has public archives. (Ensure it's not a new account with no games).")
                    return

                archives = archives_data["archives"]
                all_games = []

                st.info(f"Fetching game data from {min(len(archives), 6)} recent monthly archives...")
                for archive_url in archives[-6:]:
                    st.write(f"Fetching from: {archive_url.split('/')[-2]}/{archive_url.split('/')[-1]}")
                    archive_data = get_json_from_url_selenium(archive_url, driver)
                    if archive_data and "games" in archive_data:
                        all_games.extend(archive_data["games"])
                    time.sleep(1.0)

                if all_games:
                    analyze_games(all_games, username)
                else:
                    st.warning("No games found in the last 6 months for this username. Please try another username or check if they have recent games.")

            except Exception as e:
                st.error(f"An unexpected error occurred during analysis: {e}")
                st.info("Common issues: Incorrect username, network problems, or Chess.com API temporary issues. Check your terminal for more error details.")
            finally:
                if driver:
                    driver.quit()
                    st.write("Browser closed.")


if __name__ == "__main__":
    main()