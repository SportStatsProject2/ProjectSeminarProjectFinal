import unittest
from sportstats import create_app
from sportstats.config import TestConfig
from sportstats.services.xg_calculator import calculate_geometry, calculate_xg

class XGCalculatorTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()

    def test_calculate_geometry(self):
        # Distance to center (120, 40) from (85, 40) should be 35
        dist, angle = calculate_geometry(85, 40)
        self.assertEqual(dist, 35.0)
        # Angle should be positive
        self.assertGreater(angle, 0)

    def test_calculate_xg_logic(self):
        # Basic foot shot
        dist, angle = calculate_geometry(85, 40)
        xg = calculate_xg(dist, angle, body_part="Foot")
        self.assertTrue(0 < xg < 1)
        
        # Header should have lower xG than foot from same position
        xg_header = calculate_xg(dist, angle, body_part="Header")
        self.assertLess(xg_header, xg)
        
        # Very close shot should have higher xG than far shot
        dist_close, angle_close = calculate_geometry(115, 40)
        xg_close = calculate_xg(dist_close, angle_close)
        self.assertGreater(xg_close, xg)

    def test_xg_calculator_route(self):
        response = self.client.get("/xg-calculator")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Expected Goals (xG) Calculator", response.data)

    def test_xg_calculator_submit(self):
        response = self.client.post("/xg-calculator", data={
            "x": "85",
            "y": "40",
            "body_part": "Foot"
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"0.018", response.data) # Correct xG for this position
        self.assertIn(b"35.0 yds", response.data)

if __name__ == "__main__":
    unittest.main()
