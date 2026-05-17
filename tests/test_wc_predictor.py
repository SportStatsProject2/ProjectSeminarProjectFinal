import unittest

from sportstats import create_app
from sportstats.config import TestConfig
from sportstats.services.wc_predictor import (
    WC_2026_GROUPS,
    _build_group_table,
    get_qualified_teams,
    simulate_group_stage,
    simulate_knockouts,
    simulate_tournament,
)


class WorldCupPredictorTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.elo_data = {"Argentina": 1800, "France": 1750, "Brazil": 1780}

    def test_group_simulation(self):
        # Test a single group
        test_groups = {"Group A": ["Mexico", "South Africa", "South Korea", "Czechia"]}
        results, standings = simulate_group_stage(test_groups, self.elo_data, seed=7)

        self.assertEqual(len(results["Group A"]), 6)  # 4 teams play 6 matches
        self.assertEqual(len(standings["Group A"]), 4)
        teams_in_standings = [t["name"] for t in standings["Group A"]]
        self.assertIn("Mexico", teams_in_standings)
        self.assertEqual(sum(team["played"] for team in standings["Group A"]), 12)
        self.assertEqual(sum(team["gs"] for team in standings["Group A"]), sum(team["ga"] for team in standings["Group A"]))

    def test_group_table_uses_head_to_head_for_remaining_ties(self):
        results = [
            {"home_team": "Alpha", "away_team": "Beta", "home_score": 1, "away_score": 0, "winner": "Alpha"},
            {"home_team": "Alpha", "away_team": "Gamma", "home_score": 0, "away_score": 1, "winner": "Gamma"},
            {"home_team": "Beta", "away_team": "Gamma", "home_score": 1, "away_score": 0, "winner": "Beta"},
            {"home_team": "Delta", "away_team": "Alpha", "home_score": 0, "away_score": 2, "winner": "Alpha"},
            {"home_team": "Delta", "away_team": "Beta", "home_score": 0, "away_score": 2, "winner": "Beta"},
            {"home_team": "Delta", "away_team": "Gamma", "home_score": 0, "away_score": 1, "winner": "Gamma"},
        ]
        table = _build_group_table("Group Z", ["Alpha", "Beta", "Gamma", "Delta"], results)

        self.assertEqual(table[0]["name"], "Alpha")
        self.assertEqual(table[1]["name"], "Beta")

    def test_qualification_logic(self):
        # Mock standings for 12 groups
        mock_standings = {}
        for i, group in enumerate(WC_2026_GROUPS.keys()):
            mock_standings[group] = [
                {"name": f"T1_{i}", "points": 9, "gd": 5, "gs": 6},
                {"name": f"T2_{i}", "points": 6, "gd": 2, "gs": 4},
                {"name": f"T3_{i}", "points": 3, "gd": 0, "gs": 3},
                {"name": f"T4_{i}", "points": 0, "gd": -7, "gs": 1},
            ]

        qualified = get_qualified_teams(mock_standings)
        # 12*2 (top 2) + 8 (best 3rd) = 32
        self.assertEqual(len(qualified), 32)

    def test_knockout_simulation(self):
        qualified = [f"Team{i}" for i in range(32)]
        original_order = qualified.copy()
        bracket = simulate_knockouts(qualified, self.elo_data, seed=11)

        self.assertEqual(qualified, original_order)
        self.assertIn("Champion", bracket)
        self.assertEqual(len(bracket["Round of 32"]), 16)
        self.assertEqual(len(bracket["Final"]), 1)
        self.assertEqual(len(bracket["Bronze Final"]), 1)

    def test_tournament_simulation_is_seeded_and_complete(self):
        first = simulate_tournament(WC_2026_GROUPS, self.elo_data, seed=2026)
        second = simulate_tournament(WC_2026_GROUPS, self.elo_data, seed=2026)

        self.assertEqual(first["champion"], second["champion"])
        self.assertEqual([len(round_data["matches"]) for round_data in first["rounds"]], [16, 8, 4, 2, 1])
        self.assertEqual(first["qualified_count"], 32)
        self.assertEqual(first["total_matches"], 104)
        self.assertIn(first["champion"], {first["final"]["home_team"], first["final"]["away_team"]})

    def test_wc_route(self):
        response = self.client.get("/world-cup-predictor")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"2026 FIFA World Cup Predictor", response.data)

    def test_wc_route_runs_posted_seed(self):
        response = self.client.post("/world-cup-predictor", data={"seed": "2026"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Official match-number bracket", response.data)
        self.assertIn(b"Simulated matches", response.data)
        self.assertIn(b"Rating model", response.data)
        self.assertIn(b"Elo", response.data)

    def test_wc_route_handles_invalid_seed(self):
        response = self.client.post("/world-cup-predictor", data={"seed": "nan"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Scenario 2026", response.data)


if __name__ == "__main__":
    unittest.main()
