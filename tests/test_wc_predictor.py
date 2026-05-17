import unittest
from sportstats import create_app
from sportstats.config import TestConfig
from sportstats.services.wc_predictor import WC_2026_GROUPS, load_elo_ratings, simulate_group_stage, get_qualified_teams, simulate_knockouts

class WorldCupPredictorTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.elo_data = {"Argentina": 1800, "France": 1750, "Brazil": 1780}

    def test_group_simulation(self):
        # Test a single group
        test_groups = {"Group A": ["Mexico", "South Africa", "South Korea", "Czechia"]}
        results, standings = simulate_group_stage(test_groups, self.elo_data)
        
        self.assertEqual(len(results["Group A"]), 6) # 4 teams play 6 matches
        self.assertEqual(len(standings["Group A"]), 4)
        # Check if France is in standings (it shouldn't be for this group)
        teams_in_standings = [t["name"] for t in standings["Group A"]]
        self.assertIn("Mexico", teams_in_standings)

    def test_qualification_logic(self):
        # Mock standings for 12 groups
        mock_standings = {}
        for i, group in enumerate(WC_2026_GROUPS.keys()):
            mock_standings[group] = [
                {"name": f"T1_{i}", "points": 9, "gd": 5, "gs": 6},
                {"name": f"T2_{i}", "points": 6, "gd": 2, "gs": 4},
                {"name": f"T3_{i}", "points": 3, "gd": 0, "gs": 3},
                {"name": f"T4_{i}", "points": 0, "gd": -7, "gs": 1}
            ]
        
        qualified = get_qualified_teams(mock_standings)
        # 12*2 (top 2) + 8 (best 3rd) = 32
        self.assertEqual(len(qualified), 32)

    def test_knockout_simulation(self):
        qualified = [f"Team{i}" for i in range(32)]
        bracket = simulate_knockouts(qualified, self.elo_data)
        
        self.assertIn("Champion", bracket)
        self.assertEqual(len(bracket["Round of 32"]), 16)
        self.assertEqual(len(bracket["Final"]), 1)

    def test_wc_route(self):
        response = self.client.get("/world-cup-predictor")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"2026 FIFA World Cup Predictor", response.data)

if __name__ == "__main__":
    unittest.main()
