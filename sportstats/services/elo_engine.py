import pandas as pd
import math
from pathlib import Path

# --- 1. CONFIGURATION ---
BASE_RATING = 1500
K_FACTOR = 30  # How drastically ratings change per match
HOME_ADVANTAGE = 100  # Elo points added to the home team to reflect home-field advantage

def expected_result(rating_a, rating_b):
    """Calculates the expected probability of Team A beating Team B."""
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

def calculate_elo(csv_path):
    """Processes historical match data to calculate Elo ratings for all teams."""
    try:
        df = pd.read_csv(csv_path)
    except Exception:
        return {}

    # Sort chronologically to ensure Elo calculates correctly over time
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(by='date')

    # Dictionary to hold current Elo ratings for each team
    elo_ratings = {}

    for index, row in df.iterrows():
        home_team = row['home_team']
        away_team = row['away_team']
        home_score = row['home_score']
        away_score = row['away_score']
        neutral = row.get('neutral', False)

        # Initialize teams if they don't exist in our dictionary yet
        if home_team not in elo_ratings:
            elo_ratings[home_team] = BASE_RATING
        if away_team not in elo_ratings:
            elo_ratings[away_team] = BASE_RATING

        # Get current ratings
        current_home_elo = elo_ratings[home_team]
        current_away_elo = elo_ratings[away_team]

        # Apply Home Advantage (only if the match is not played at a neutral venue)
        home_elo_adjusted = current_home_elo + HOME_ADVANTAGE if not neutral else current_home_elo

        # Determine actual match result (W)
        if home_score > away_score:
            actual_home_result = 1.0
            actual_away_result = 0.0
        elif home_score < away_score:
            actual_home_result = 0.0
            actual_away_result = 1.0
        else:
            actual_home_result = 0.5
            actual_away_result = 0.5

        # Calculate Expected Win probabilities (We)
        expected_home_win = expected_result(home_elo_adjusted, current_away_elo)
        expected_away_win = expected_result(current_away_elo, home_elo_adjusted)

        # Update Ratings
        new_home_elo = current_home_elo + K_FACTOR * (actual_home_result - expected_home_win)
        new_away_elo = current_away_elo + K_FACTOR * (actual_away_result - expected_away_win)

        # Save back to dictionary
        elo_ratings[home_team] = new_home_elo
        elo_ratings[away_team] = new_away_elo

    return elo_ratings

def get_elo_dataframe(elo_ratings):
    """Converts the ratings dictionary to a sorted DataFrame for display."""
    elo_df = pd.DataFrame(list(elo_ratings.items()), columns=['Team', 'Elo Rating'])
    elo_df = elo_df.sort_values(by='Elo Rating', ascending=False).reset_index(drop=True)
    elo_df['Elo Rating'] = elo_df['Elo Rating'].round(1)
    return elo_df
