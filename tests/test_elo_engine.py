import unittest
from sportstats import create_app
from sportstats.config import TestConfig
from sportstats.services.elo_engine import calculate_elo, expected_result

class EloEngineTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()

    def test_expected_result(self):
        # Equal ratings should give 0.5 probability
        self.assertEqual(expected_result(1500, 1500), 0.5)
        # Higher rating should have higher probability
        self.assertGreater(expected_result(1600, 1500), 0.5)

    def test_elo_calculation(self, tmp_path=None):
        # Create a tiny mock CSV for testing
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("date,home_team,away_team,home_score,away_score,neutral\n")
            f.write("2023-01-01,France,Morocco,2,0,False\n")
            f.close()
            
            ratings = calculate_elo(f.name)
            self.assertIn("France", ratings)
            self.assertIn("Morocco", ratings)
            # France won at home, rating should increase (considering home advantage)
            # Actually, France was 1500, adjusted 1600 vs 1500.
            # Expected win for France was > 0.5. Since they won, they still gain points but less than if they were away.
            self.assertGreater(ratings["France"], 1500)
            self.assertLess(ratings["Morocco"], 1500)
            
            os.unlink(f.name)

    def test_elo_ratings_route(self):
        # This test relies on the data files existing in sportstats/data/
        # which I just copied.
        response = self.client.get("/elo-ratings")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"International Elo Ratings", response.data)
        # Should contain some top teams
        self.assertIn(b"Argentina", response.data)

if __name__ == "__main__":
    unittest.main()
