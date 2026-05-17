import numpy as np
from dataclasses import dataclass
from math import exp, factorial

@dataclass(frozen=True)
class TeamProfile:
    name: str
    elo: float = 1500.0
    attack_strength: float = 1.0
    defense_strength: float = 1.0

def predict_match(
    home: TeamProfile,
    away: TeamProfile,
    *,
    simulations: int = 10000,
    seed: int = 42,
) -> dict:
    """Predicts match outcomes using a Monte Carlo simulation based on Poisson distributions."""
    simulations = min(max(simulations, 1000), 100000)
    home_xg, away_xg = expected_goals(home, away)
    
    # Using numpy for fast vectorized simulations
    np.random.seed(seed)
    home_goals = np.random.poisson(home_xg, simulations)
    away_goals = np.random.poisson(away_xg, simulations)

    home_wins = np.sum(home_goals > away_goals)
    draws = np.sum(home_goals == away_goals)
    away_wins = np.sum(home_goals < away_goals)

    scorelines = _scoreline_probabilities(home_xg, away_xg)

    return {
        "home_team": home.name,
        "away_team": away.name,
        "expected_goals": {"home": round(home_xg, 2), "away": round(away_xg, 2)},
        "probabilities": {
            "home_win": round(float(home_wins) / simulations, 4),
            "draw": round(float(draws) / simulations, 4),
            "away_win": round(float(away_wins) / simulations, 4),
        },
        "most_likely_scores": scorelines[:5],
        "simulations": simulations,
    }

def expected_goals(home: TeamProfile, away: TeamProfile) -> tuple[float, float]:
    """Calculates expected goals for both teams based on their relative strengths and Elo."""
    league_home_goals = 1.42
    league_away_goals = 1.16
    elo_adjustment = (home.elo - away.elo) / 800.0

    home_xg = league_home_goals * home.attack_strength / max(away.defense_strength, 0.2)
    away_xg = league_away_goals * away.attack_strength / max(home.defense_strength, 0.2)
    bounded_elo = max(min(elo_adjustment, 0.35), -0.35)

    return max(home_xg * (1.0 + bounded_elo), 0.05), max(away_xg * (1.0 - bounded_elo), 0.05)

def _poisson_probability(mean: float, goals: int) -> float:
    """Calculates the probability of scoring 'goals' given an average 'mean'."""
    return (mean**goals * exp(-mean)) / factorial(goals)

def _scoreline_probabilities(home_xg: float, away_xg: float, max_goals: int = 6) -> list[dict]:
    """Calculates probabilities for specific scorelines using the Poisson distribution."""
    scorelines = []
    for home_goals in range(max_goals + 1):
        for away_goals in range(max_goals + 1):
            probability = _poisson_probability(home_xg, home_goals) * _poisson_probability(away_xg, away_goals)
            scorelines.append({"score": f"{home_goals}-{away_goals}", "probability": round(probability, 4)})
    return sorted(scorelines, key=lambda item: item["probability"], reverse=True)
