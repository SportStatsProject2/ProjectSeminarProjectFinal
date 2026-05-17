import pickle
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import numpy as np

from sportstats.vision.ball_assignment import PlayerBallAssigner
from sportstats.vision.camera_movement import _load_camera_stub
from sportstats.vision.geometry import get_center_of_bbox, get_foot_position, measure_distance
from sportstats.vision.team_assignment import TeamAssigner, kmeans
from sportstats.vision.tracking import FootballTracker, _tracks_match_frame_count


class VisionHelpersTest(unittest.TestCase):
    def test_geometry_helpers(self):
        bbox = [10, 20, 30, 80]

        self.assertEqual(get_center_of_bbox(bbox), (20.0, 50.0))
        self.assertEqual(get_foot_position(bbox), (20.0, 80.0))
        self.assertEqual(measure_distance((0, 0), (3, 4)), 5.0)

    def test_ball_interpolation_fills_missing_frames(self):
        ball_positions = [
            {1: {"bbox": [0, 0, 10, 10]}},
            {},
            {1: {"bbox": [20, 20, 30, 30]}},
        ]

        interpolated = FootballTracker.interpolate_ball_positions(ball_positions)

        self.assertEqual(interpolated[1][1]["bbox"], [10.0, 10.0, 20.0, 20.0])
        self.assertTrue(interpolated[1][1]["interpolated"])

    def test_raw_ball_frames_are_counted_before_interpolation(self):
        ball_positions = [
            {1: {"bbox": [0, 0, 10, 10]}},
            {},
            {1: {"bbox": [20, 20, 30, 30]}},
        ]

        self.assertEqual(_frames_with_tracks(ball_positions), 2)

    def test_player_ball_assignment_uses_nearest_foot(self):
        players = {
            7: {"bbox": [0, 0, 20, 100]},
            8: {"bbox": [200, 0, 220, 100]},
        }

        assigned = PlayerBallAssigner(max_player_ball_distance=50).assign_ball_to_player(players, [5, 88, 15, 98])

        self.assertEqual(assigned, 7)

    def test_kmeans_separates_two_colors(self):
        points = np.asarray([[0, 0, 0], [5, 5, 5], [250, 250, 250], [245, 245, 245]], dtype=float)

        centroids, labels = kmeans(points, k=2, iterations=10)

        self.assertEqual(len(centroids), 2)
        self.assertEqual(set(labels.tolist()), {0, 1})

    def test_team_color_uses_corner_background_even_when_sampling(self):
        frame = np.zeros((200, 100, 3), dtype=np.uint8)
        frame[:, :] = [0, 160, 0]
        frame[20:90, 30:70] = [20, 20, 230]

        color = TeamAssigner().get_player_color(frame, [0, 0, 100, 200])

        self.assertGreater(color[2], 180)
        self.assertLess(color[1], 80)

    def test_stale_track_stub_is_rejected_by_frame_count(self):
        tracks = {"players": [{}, {}], "referees": [{}, {}], "ball": [{}, {}]}

        self.assertTrue(_tracks_match_frame_count(tracks, 2))
        self.assertFalse(_tracks_match_frame_count(tracks, 3))

    def test_h264_encoder_returns_false_when_input_is_missing(self):
        with TemporaryDirectory() as directory:
            output_path = Path(directory) / "out.mp4"

            encoded = _encode_h264(Path(directory) / "missing.mp4", output_path)

            self.assertFalse(encoded)
            self.assertFalse(output_path.exists())


if __name__ == "__main__":
    unittest.main()
