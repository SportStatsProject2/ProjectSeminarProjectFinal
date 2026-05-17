import numpy as np
import pandas as pd
import random
import os
from pathlib import Path

NAME_ALIASES = {
    'Czechia': 'Czech Republic',
    'Türkiye': 'Turkey',
    'Bosnia-Herzegovina': 'Bosnia and Herzegovina',
    'Congo DR': 'DR Congo',
    'USA': 'United States'
}

WC_2026_GROUPS = {
    "Group A": ["Mexico", "South Africa", "South Korea", "Czechia"],
    "Group B": ["Canada", "Bosnia-Herzegovina", "Qatar", "Switzerland"],
    "Group C": ["Brazil", "Morocco", "Haiti", "Scotland"],
    "Group D": ["United States", "Paraguay", "Australia", "Türkiye"],
    "Group E": ["Germany", "Curaçao", "Ivory Coast", "Ecuador"],
    "Group F": ["Netherlands", "Japan", "Sweden", "Tunisia"],
    "Group G": ["Belgium", "Egypt", "Iran", "New Zealand"],
    "Group H": ["Spain", "Cape Verde", "Saudi Arabia", "Uruguay"],
    "Group I": ["France", "Senegal", "Iraq", "Norway"],
    "Group J": ["Argentina", "Algeria", "Austria", "Jordan"],
    "Group K": ["Portugal", "Congo DR", "Uzbekistan", "Colombia"],
    "Group L": ["England", "Croatia", "Ghana", "Panama"]
}

def load_elo_ratings(filename):
    """Loads the Elo ratings from the CSV and maps them to a dictionary."""
    if not os.path.exists(filename):
        return {}

    df = pd.read_csv(filename)
    elo_dict = dict(zip(df['Team'], df['Elo Rating']))

    # Apply aliases
    for wc_name, db_name in NAME_ALIASES.items():
        if db_name in elo_dict:
            elo_dict[wc_name] = elo_dict[db_name]

    return elo_dict

def simulate_match(team_a, team_b, elo_dict, knockout=False):
    """Simulates a match and returns scores and result."""
    elo_a = elo_dict.get(team_a, 1500)
    elo_b = elo_dict.get(team_b, 1500)

    elo_diff = elo_a - elo_b
    xg_a = max(0.2, 1.25 + (elo_diff / 400))
    xg_b = max(0.2, 1.25 - (elo_diff / 400))

    goals_a = np.random.poisson(xg_a)
    goals_b = np.random.poisson(xg_b)

    is_pens = False
    winner = None

    if goals_a > goals_b:
        winner = team_a
    elif goals_b > goals_a:
        winner = team_b
    else:
        if knockout:
            is_pens = True
            prob_a_wins = 1 / (1 + 10 ** ((elo_b - elo_a) / 400))
            winner = team_a if np.random.rand() < prob_a_wins else team_b
        else:
            winner = "Draw"

    return {
        "home_team": team_a,
        "away_team": team_b,
        "home_score": int(goals_a),
        "away_score": int(goals_b),
        "winner": winner,
        "decided_on_pens": is_pens
    }

def simulate_group_stage(groups, elo_dict):
    """Simulates the group stage and returns standings."""
    group_results = {}
    standings = {}

    for group_name, teams in groups.items():
        results = []
        # Each team plays every other team once
        for i in range(len(teams)):
            for j in range(i + 1, len(teams)):
                res = simulate_match(teams[i], teams[j], elo_dict, knockout=False)
                results.append(res)
        
        group_results[group_name] = results
        
        # Calculate table
        table = {team: {"points": 0, "gd": 0, "gs": 0, "name": team} for team in teams}
        for res in results:
            h, a = res["home_team"], res["away_team"]
            hs, ascore = res["home_score"], res["away_score"]
            
            table[h]["gs"] += hs
            table[h]["gd"] += (hs - ascore)
            table[a]["gs"] += ascore
            table[a]["gd"] += (ascore - hs)
            
            if res["winner"] == h:
                table[h]["points"] += 3
            elif res["winner"] == a:
                table[a]["points"] += 3
            else:
                table[h]["points"] += 1
                table[a]["points"] += 1
        
        # Sort table
        sorted_table = sorted(table.values(), key=lambda x: (x["points"], x["gd"], x["gs"]), reverse=True)
        standings[group_name] = sorted_table

    return group_results, standings

def get_qualified_teams(standings):
    """Picks top 2 and 8 best 3rd placed teams."""
    qualified = []
    third_placed = []

    for group_name, table in standings.items():
        qualified.append(table[0]["name"])
        qualified.append(table[1]["name"])
        third_placed.append(table[2])

    # Sort 3rd placed teams
    sorted_third = sorted(third_placed, key=lambda x: (x["points"], x["gd"], x["gs"]), reverse=True)
    for i in range(8):
        qualified.append(sorted_third[i]["name"])

    return qualified

def simulate_knockouts(qualified_teams, elo_dict):
    """Simulates the knockout bracket (32 teams)."""
    # For simplicity in this demo, we randomize the R32 pairings
    random.shuffle(qualified_teams)
    
    current_round_teams = qualified_teams.copy()
    tournament_history = {
        "Round of 32": [],
        "Round of 16": [],
        "Quarter-Finals": [],
        "Semi-Finals": [],
        "Final": [],
        "Champion": None
    }

    round_names = ["Round of 32", "Round of 16", "Quarter-Finals", "Semi-Finals", "Final"]
    
    for round_name in round_names:
        next_round_teams = []
        for i in range(0, len(current_round_teams), 2):
            team_a = current_round_teams[i]
            team_b = current_round_teams[i+1]
            match_result = simulate_match(team_a, team_b, elo_dict, knockout=True)
            tournament_history[round_name].append(match_result)
            next_round_teams.append(match_result['winner'])
        
        current_round_teams = next_round_teams
        if len(current_round_teams) == 1:
            break

    tournament_history["Champion"] = current_round_teams[0]
    return tournament_history
