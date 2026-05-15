from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np

from sportstats.vision.tracking import Tracks


class CameraMovementEstimator:
    def __init__(self, first_frame, *, minimum_distance: float = 5.0):
        import cv2

        self.minimum_distance = minimum_distance
        self.cv2 = cv2
        height, width = first_frame.shape[:2]
        mask = np.zeros((height, width), dtype=np.uint8)
        top_band = max(int(height * 0.08), 20)
        bottom_start = min(int(height * 0.83), height - 1)
        mask[:top_band, :] = 255
        mask[bottom_start:, :] = 255
        self.feature_params = {
            "maxCorners": 100,
            "qualityLevel": 0.3,
            "minDistance": 3,
            "blockSize": 7,
            "mask": mask,
        }
        self.lk_params = {
            "winSize": (15, 15),
            "maxLevel": 2,
            "criteria": (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03),
        }

    def get_camera_movement(
        self,
        frames: list,
        *,
        read_from_stub: bool = False,
        stub_path: Path | None = None,
    ) -> list[tuple[float, float]]:
        if read_from_stub and stub_path and stub_path.exists():
            with stub_path.open("rb") as handle:
                movement = pickle.load(handle)
            if isinstance(movement, list) and len(movement) == len(frames):
                return movement

        if not frames:
            return []

        cv2 = self.cv2
        movement = [(0.0, 0.0)] * len(frames)
        cumulative_x = 0.0
        cumulative_y = 0.0
        old_gray = cv2.cvtColor(frames[0], cv2.COLOR_BGR2GRAY)
        old_features = cv2.goodFeaturesToTrack(old_gray, **self.feature_params)

        for frame_index in range(1, len(frames)):
            frame_gray = cv2.cvtColor(frames[frame_index], cv2.COLOR_BGR2GRAY)
            if old_features is None or len(old_features) == 0:
                old_features = cv2.goodFeaturesToTrack(old_gray, **self.feature_params)
                movement[frame_index] = (cumulative_x, cumulative_y)
                old_gray = frame_gray
                continue

            new_features, status, _error = cv2.calcOpticalFlowPyrLK(
                old_gray,
                frame_gray,
                old_features,
                None,
                **self.lk_params,
            )
            if new_features is None or status is None:
                movement[frame_index] = (cumulative_x, cumulative_y)
                old_gray = frame_gray
                old_features = cv2.goodFeaturesToTrack(old_gray, **self.feature_params)
                continue

            valid_new = new_features[status.flatten() == 1]
            valid_old = old_features[status.flatten() == 1]
            if len(valid_new):
                deltas = (valid_new - valid_old).reshape(-1, 2)
                median_delta = np.median(deltas, axis=0)
                if float(np.linalg.norm(median_delta)) >= self.minimum_distance:
                    cumulative_x += float(median_delta[0])
                    cumulative_y += float(median_delta[1])

            movement[frame_index] = (cumulative_x, cumulative_y)
            old_gray = frame_gray
            old_features = cv2.goodFeaturesToTrack(old_gray, **self.feature_params)

        if stub_path:
            stub_path.parent.mkdir(parents=True, exist_ok=True)
            with stub_path.open("wb") as handle:
                pickle.dump(movement, handle)

        return movement

    @staticmethod
    def adjust_positions_to_tracks(tracks: Tracks, camera_movement_per_frame: list[tuple[float, float]]) -> None:
        for object_tracks in tracks.values():
            for frame_index, frame_tracks in enumerate(object_tracks):
                movement_x, movement_y = camera_movement_per_frame[frame_index]
                for track_info in frame_tracks.values():
                    position = track_info.get("position")
                    if position is None:
                        continue
                    track_info["position_adjusted"] = (position[0] - movement_x, position[1] - movement_y)
