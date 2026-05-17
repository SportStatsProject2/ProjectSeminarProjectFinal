import unittest
import json

from sportstats.services.passing_network import build_demo_network, build_network, demo_passes_json, parse_pass_events


class PassingNetworkServiceTest(unittest.TestCase):
    def test_build_network_aggregates_edges_and_nodes(self):
        network = build_network(
            [
                {"passer": "A", "receiver": "B", "start_x": 10, "start_y": 40, "end_x": 30, "end_y": 50},
                {"passer": "A", "receiver": "B", "start_x": 12, "start_y": 42, "end_x": 32, "end_y": 52},
                {"passer": "B", "receiver": "C", "start_x": 30, "start_y": 50, "end_x": 60, "end_y": 45},
            ]
        )

        self.assertEqual(network["total_passes"], 3)
        self.assertEqual(network["edges"][0]["source"], "A")
        self.assertEqual(network["edges"][0]["target"], "B")
        self.assertEqual(network["edges"][0]["count"], 2)
        self.assertEqual(len(network["nodes"]), 3)
        self.assertEqual(network["player_count"], 3)
        self.assertEqual(network["link_count"], 2)
        self.assertEqual(network["central_player"], "B")
        self.assertEqual(network["progressive_passes"], 3)
        self.assertGreater(network["network_density"], 0)

    def test_build_network_tracks_player_involvement(self):
        network = build_network(
            [
                {"passer": "DM", "receiver": "AM", "start_x": 40, "start_y": 50, "end_x": 60, "end_y": 50},
                {"passer": "AM", "receiver": "ST", "start_x": 60, "start_y": 50, "end_x": 80, "end_y": 50},
            ]
        )

        top_node = network["top_nodes"][0]

        self.assertEqual(top_node["player"], "AM")
        self.assertEqual(top_node["passes_sent"], 1)
        self.assertEqual(top_node["passes_received"], 1)
        self.assertEqual(top_node["touches"], 2)
        self.assertEqual(network["edges"][0]["average_progression"], 20.0)

    def test_demo_passes_json_is_valid_input(self):
        network = build_network(json.loads(demo_passes_json()))

        self.assertGreater(network["total_passes"], 0)
        self.assertEqual(network["player_count"], 11)

    def test_demo_network_uses_standard_eleven(self):
        network = build_demo_network()

        self.assertEqual(network["player_count"], 11)
        self.assertEqual(network["warnings"], [])

    def test_parse_pass_events_accepts_wrapped_payload(self):
        events = parse_pass_events(
            json.dumps(
                {
                    "passes": [
                        {"passer": "A", "receiver": "B", "start_x": 10, "start_y": 50, "end_x": 20, "end_y": 50}
                    ]
                }
            )
        )

        self.assertEqual(events[0]["passer"], "A")

    def test_build_network_warns_when_more_than_eleven_players_are_present(self):
        events = [
            {"passer": f"P{index}", "receiver": f"P{index + 1}", "start_x": 10, "start_y": 50, "end_x": 20, "end_y": 50}
            for index in range(12)
        ]

        network = build_network(events)

        self.assertEqual(network["player_count"], 13)
        self.assertIn("13 players", network["warnings"][0])

    def test_build_network_rejects_invalid_coordinates(self):
        with self.assertRaisesRegex(ValueError, "start_x"):
            build_network(
                [
                    {
                        "passer": "A",
                        "receiver": "B",
                        "start_x": -1,
                        "start_y": 40,
                        "end_x": 30,
                        "end_y": 50,
                    }
                ]
            )


if __name__ == "__main__":
    unittest.main()
