from __future__ import annotations

import os
from itertools import groupby
from typing import Any

import numpy as np
import pandas as pd

DEFAULT_ELO = 1500.0
ROUND_NAMES = ["Round of 32", "Round of 16", "Quarter-Finals", "Semi-Finals", "Final"]

NAME_ALIASES = {
    "Czechia": "Czech Republic",
    "Türkiye": "Turkey",
    "Bosnia-Herzegovina": "Bosnia and Herzegovina",
    "Congo DR": "DR Congo",
    "USA": "United States",
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
    "Group L": ["England", "Croatia", "Ghana", "Panama"],
}

ROUND_OF_32_SLOTS = [
    (73, ("runner_up", "A"), ("runner_up", "B")),
    (74, ("winner", "E"), ("third", ("A", "B", "C", "D", "F"))),
    (75, ("winner", "F"), ("runner_up", "C")),
    (76, ("winner", "C"), ("runner_up", "F")),
    (77, ("winner", "I"), ("third", ("C", "D", "F", "G", "H"))),
    (78, ("runner_up", "E"), ("runner_up", "I")),
    (79, ("winner", "A"), ("third", ("C", "E", "F", "H", "I"))),
    (80, ("winner", "L"), ("third", ("E", "H", "I", "J", "K"))),
    (81, ("winner", "D"), ("third", ("B", "E", "F", "I", "J"))),
    (82, ("winner", "G"), ("third", ("A", "E", "H", "I", "J"))),
    (83, ("runner_up", "K"), ("runner_up", "L")),
    (84, ("winner", "H"), ("runner_up", "J")),
    (85, ("winner", "B"), ("third", ("E", "F", "G", "I", "J"))),
    (86, ("winner", "J"), ("runner_up", "H")),
    (87, ("winner", "K"), ("third", ("D", "E", "I", "J", "L"))),
    (88, ("runner_up", "D"), ("runner_up", "G")),
]

KNOCKOUT_ROUND_DEPENDENCIES = {
    "Round of 16": [
        (89, 74, 77),
        (90, 73, 75),
        (91, 76, 78),
        (92, 79, 80),
        (93, 83, 84),
        (94, 81, 82),
        (95, 86, 88),
        (96, 85, 87),
    ],
    "Quarter-Finals": [(97, 89, 90), (98, 93, 94), (99, 91, 92), (100, 95, 96)],
    "Semi-Finals": [(101, 97, 98), (102, 99, 100)],
    "Final": [(104, 101, 102)],
}


def load_elo_ratings(filename):
    """Load Elo ratings from CSV and map World Cup display names to the data names."""
    if not os.path.exists(filename):
        return {}

    df = pd.read_csv(filename)
    elo_dict = dict(zip(df["Team"], df["Elo Rating"], strict=False))

    for wc_name, db_name in NAME_ALIASES.items():
        if db_name in elo_dict:
            elo_dict[wc_name] = elo_dict[db_name]

    return elo_dict


def simulate_match(team_a, team_b, elo_dict, knockout=False, rng=None):
    """Simulate one neutral-site match with Elo-driven expected goals."""
    rng = rng or np.random.default_rng()
    elo_a = float(elo_dict.get(team_a, DEFAULT_ELO))
    elo_b = float(elo_dict.get(team_b, DEFAULT_ELO))
    xg_a, xg_b = expected_goals(elo_a, elo_b)

    goals_a = int(rng.poisson(xg_a))
    goals_b = int(rng.poisson(xg_b))

    decided_on_pens = False
    winner = None
    loser = None

    if goals_a > goals_b:
        winner = team_a
        loser = team_b
    elif goals_b > goals_a:
        winner = team_b
        loser = team_a
    elif knockout:
        decided_on_pens = True
        prob_a_wins = expected_win_probability(elo_a, elo_b)
        winner = team_a if rng.random() < prob_a_wins else team_b
        loser = team_b if winner == team_a else team_a
    else:
        winner = "Draw"

    return {
        "home_team": team_a,
        "away_team": team_b,
        "home_score": goals_a,
        "away_score": goals_b,
        "home_elo": round(elo_a, 1),
        "away_elo": round(elo_b, 1),
        "home_xg": round(xg_a, 2),
        "away_xg": round(xg_b, 2),
        "winner": winner,
        "loser": loser,
        "decided_on_pens": decided_on_pens,
    }


def expected_win_probability(elo_a: float, elo_b: float) -> float:
    return 1 / (1 + 10 ** ((elo_b - elo_a) / 400))


def expected_goals(elo_a: float, elo_b: float) -> tuple[float, float]:
    elo_gap = float(np.clip((elo_a - elo_b) / 400, -1.25, 1.25))
    return max(0.25, 1.28 + 0.48 * elo_gap), max(0.25, 1.28 - 0.48 * elo_gap)


def simulate_group_stage(groups, elo_dict, rng=None, seed=None):
    """Simulate the group stage and return match results and ordered standings."""
    rng = rng or np.random.default_rng(seed)
    group_results = {}
    standings = {}

    for group_name, teams in groups.items():
        results = []
        for i in range(len(teams)):
            for j in range(i + 1, len(teams)):
                res = simulate_match(teams[i], teams[j], elo_dict, knockout=False, rng=rng)
                results.append(res)

        group_results[group_name] = results
        standings[group_name] = _build_group_table(group_name, teams, results)

    mark_qualifiers(standings)
    return group_results, standings


def mark_qualifiers(standings):
    third_placed = []

    for group_name, table in standings.items():
        group_letter = _group_letter(group_name)
        for rank, entry in enumerate(table, start=1):
            entry["rank"] = rank
            entry["qualified"] = rank <= 2
            entry["qualification"] = "Top two" if rank <= 2 else "Eliminated"
            entry["seed_label"] = f"{rank}{group_letter}"
        third_placed.append(table[2])

    best_thirds = sorted(third_placed, key=_table_sort_key)[:8]
    best_third_names = {entry["name"] for entry in best_thirds}

    for table in standings.values():
        third_entry = table[2]
        if third_entry["name"] in best_third_names:
            third_entry["qualified"] = True
            third_entry["qualification"] = "Best third"


def get_qualified_teams(standings):
    """Return the 24 top-two teams plus the eight best third-placed teams."""
    mark_qualifiers(standings)
    return [entry["name"] for entry in get_qualified_entries(standings)]


def get_qualified_entries(standings):
    qualifiers = []
    third_placed = []

    for table in standings.values():
        qualifiers.extend(table[:2])
        third_placed.append(table[2])

    qualifiers.extend(sorted(third_placed, key=_table_sort_key)[:8])
    return qualifiers


def simulate_knockouts(qualified_teams, elo_dict, standings=None, rng=None, seed=None):
    """Simulate the fixed 2026 knockout path without mutating or shuffling qualifiers."""
    rng = rng or np.random.default_rng(seed)
    history = {round_name: [] for round_name in ROUND_NAMES}
    history["Bronze Final"] = []
    history["Champion"] = None
    history["Third Place"] = None

    if standings:
        round_of_32_pairings = _build_official_round_of_32_pairings(standings)
    else:
        round_of_32_pairings = _build_seeded_round_of_32_pairings(qualified_teams)

    match_winners = {}
    match_losers = {}

    for match_number, home_team, away_team, home_label, away_label in round_of_32_pairings:
        result = _simulate_bracket_match(
            match_number,
            "Round of 32",
            home_team,
            away_team,
            elo_dict,
            rng,
            home_label,
            away_label,
        )
        history["Round of 32"].append(result)
        match_winners[match_number] = result["winner"]
        match_losers[match_number] = result["loser"]

    for round_name, dependencies in KNOCKOUT_ROUND_DEPENDENCIES.items():
        for match_number, home_source, away_source in dependencies:
            result = _simulate_bracket_match(
                match_number,
                round_name,
                match_winners[home_source],
                match_winners[away_source],
                elo_dict,
                rng,
                f"W{home_source}",
                f"W{away_source}",
            )
            history[round_name].append(result)
            match_winners[match_number] = result["winner"]
            match_losers[match_number] = result["loser"]

    bronze = _simulate_bracket_match(
        103,
        "Bronze Final",
        match_losers[101],
        match_losers[102],
        elo_dict,
        rng,
        "L101",
        "L102",
    )
    history["Bronze Final"].append(bronze)
    history["Champion"] = match_winners[104]
    history["Third Place"] = bronze["winner"]
    history["rounds"] = [{"name": round_name, "matches": history[round_name]} for round_name in ROUND_NAMES]
    return history


def simulate_tournament(groups, elo_dict, seed=None):
    rng = np.random.default_rng(seed)
    group_results, standings = simulate_group_stage(groups, elo_dict, rng=rng)
    qualified_teams = get_qualified_teams(standings)
    bracket = simulate_knockouts(qualified_teams, elo_dict, standings=standings, rng=rng)

    return {
        "groups": group_results,
        "standings": standings,
        "qualified_teams": qualified_teams,
        "qualified_count": len(qualified_teams),
        "bracket": bracket,
        "rounds": bracket["rounds"],
        "champion": bracket["Champion"],
        "third_place": bracket["Third Place"],
        "final": bracket["Final"][0],
        "bronze_final": bracket["Bronze Final"][0],
        "seed": seed,
        "total_matches": sum(len(matches) for matches in group_results.values())
        + sum(len(bracket[round_name]) for round_name in ROUND_NAMES)
        + len(bracket["Bronze Final"]),
    }


def _build_group_table(group_name: str, teams: list[str], results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    table = {
        team: {
            "name": team,
            "group": group_name,
            "group_letter": _group_letter(group_name),
            "played": 0,
            "wins": 0,
            "draws": 0,
            "losses": 0,
            "points": 0,
            "gd": 0,
            "gs": 0,
            "ga": 0,
            "qualified": False,
            "qualification": "Eliminated",
        }
        for team in teams
    }

    for result in results:
        home = result["home_team"]
        away = result["away_team"]
        home_score = result["home_score"]
        away_score = result["away_score"]

        table[home]["played"] += 1
        table[away]["played"] += 1
        table[home]["gs"] += home_score
        table[home]["ga"] += away_score
        table[away]["gs"] += away_score
        table[away]["ga"] += home_score
        table[home]["gd"] += home_score - away_score
        table[away]["gd"] += away_score - home_score

        if result["winner"] == home:
            table[home]["wins"] += 1
            table[away]["losses"] += 1
            table[home]["points"] += 3
        elif result["winner"] == away:
            table[away]["wins"] += 1
            table[home]["losses"] += 1
            table[away]["points"] += 3
        else:
            table[home]["draws"] += 1
            table[away]["draws"] += 1
            table[home]["points"] += 1
            table[away]["points"] += 1

    return _sort_group_table(list(table.values()), results)


def _sort_group_table(table: list[dict[str, Any]], results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(table, key=_table_sort_key)
    sorted_table = []

    for _, tied_entries in groupby(ordered, key=lambda entry: (entry["points"], entry["gd"], entry["gs"])):
        tied_entries = list(tied_entries)
        if len(tied_entries) == 1:
            sorted_table.extend(tied_entries)
            continue

        h2h = _head_to_head_table({entry["name"] for entry in tied_entries}, results)
        sorted_table.extend(
            sorted(
                tied_entries,
                key=lambda entry: (
                    -h2h[entry["name"]]["points"],
                    -h2h[entry["name"]]["gd"],
                    -h2h[entry["name"]]["gs"],
                    entry["name"],
                ),
            )
        )

    return sorted_table


def _head_to_head_table(team_names: set[str], results: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    table = {team: {"points": 0, "gd": 0, "gs": 0} for team in team_names}

    for result in results:
        home = result["home_team"]
        away = result["away_team"]
        if home not in team_names or away not in team_names:
            continue

        home_score = result["home_score"]
        away_score = result["away_score"]
        table[home]["gs"] += home_score
        table[home]["gd"] += home_score - away_score
        table[away]["gs"] += away_score
        table[away]["gd"] += away_score - home_score

        if home_score > away_score:
            table[home]["points"] += 3
        elif away_score > home_score:
            table[away]["points"] += 3
        else:
            table[home]["points"] += 1
            table[away]["points"] += 1

    return table


def _table_sort_key(entry: dict[str, Any]):
    return (-entry["points"], -entry["gd"], -entry["gs"], entry["name"])


def _build_official_round_of_32_pairings(standings):
    by_label = {}
    third_entries = []

    for table in standings.values():
        by_label[f"1{table[0]['group_letter']}"] = table[0]
        by_label[f"2{table[1]['group_letter']}"] = table[1]
        if table[2].get("qualified"):
            by_label[f"3{table[2]['group_letter']}"] = table[2]
            third_entries.append(table[2])

    third_assignments = _assign_third_place_slots(third_entries)
    pairings = []

    for match_number, home_slot, away_slot in ROUND_OF_32_SLOTS:
        home_entry, home_label = _resolve_bracket_slot(home_slot, by_label, third_assignments, match_number)
        away_entry, away_label = _resolve_bracket_slot(away_slot, by_label, third_assignments, match_number)
        pairings.append((match_number, home_entry["name"], away_entry["name"], home_label, away_label))

    return pairings


def _assign_third_place_slots(third_entries: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    by_letter = {entry["group_letter"]: entry for entry in third_entries}
    third_slots = [
        (match_number, slot[1])
        for match_number, _home_slot, slot in ROUND_OF_32_SLOTS
        if slot[0] == "third"
    ]

    def backtrack(index: int, remaining: set[str]) -> dict[int, dict[str, Any]] | None:
        if index == len(third_slots):
            return {}

        match_number, eligible_groups = third_slots[index]
        candidates = sorted(
            (group for group in remaining if group in eligible_groups),
            key=lambda group: _table_sort_key(by_letter[group]),
        )

        for group in candidates:
            rest = backtrack(index + 1, remaining - {group})
            if rest is not None:
                rest[match_number] = by_letter[group]
                return rest

        return None

    assignments = backtrack(0, set(by_letter))
    if assignments is not None:
        return assignments

    fallback = {}
    available = set(by_letter)
    for match_number, eligible_groups in third_slots:
        candidates = [group for group in available if group in eligible_groups] or list(available)
        selected = sorted(candidates, key=lambda group: _table_sort_key(by_letter[group]))[0]
        fallback[match_number] = by_letter[selected]
        available.remove(selected)
    return fallback


def _resolve_bracket_slot(slot, by_label, third_assignments, match_number):
    slot_type, value = slot
    if slot_type == "winner":
        label = f"1{value}"
        return by_label[label], label
    if slot_type == "runner_up":
        label = f"2{value}"
        return by_label[label], label

    entry = third_assignments[match_number]
    return entry, f"3{entry['group_letter']}"


def _build_seeded_round_of_32_pairings(qualified_teams):
    teams = list(qualified_teams)
    if len(teams) != 32:
        raise ValueError("The knockout bracket requires exactly 32 qualified teams.")

    pairings = []
    for index, match_number in enumerate(range(73, 89)):
        home_index = index
        away_index = len(teams) - index - 1
        pairings.append(
            (
                match_number,
                teams[home_index],
                teams[away_index],
                f"Seed {home_index + 1}",
                f"Seed {away_index + 1}",
            )
        )
    return pairings


def _simulate_bracket_match(match_number, round_name, home_team, away_team, elo_dict, rng, home_label, away_label):
    result = simulate_match(home_team, away_team, elo_dict, knockout=True, rng=rng)
    result.update(
        {
            "match_number": match_number,
            "round": round_name,
            "home_seed": home_label,
            "away_seed": away_label,
        }
    )
    return result


def _group_letter(group_name: str) -> str:
    return group_name.rsplit(" ", maxsplit=1)[-1]
