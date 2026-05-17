from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any

import numpy as np

from sportstats.vision.geometry import get_center_of_bbox, get_foot_position


TrackInfo = dict[str, Any]
Tracks = dict[str, list[dict[int, TrackInfo]]]


class FootballTracker:
    def __init__(self, model_path: str, *, confidence: float = 0.1, tracker_config: str = "bytetrack.yaml"):
        from ultralytics import YOLO

        self.model = YOLO(model_path)
        self.confidence = confidence
        self.tracker_config = tracker_config

    def get_object_tracks(
        self,
        frames: list,
        *,
        read_from_stub: bool = False,
        stub_path: Path | None = None,
    ) -> Tracks:
        if read_from_stub and stub_path and stub_path.exists():
            with stub_path.open("rb") as handle:
                stub_tracks = pickle.load(handle)
            if _tracks_match_frame_count(stub_tracks, len(frames)):
                return stub_tracks

        tracks: Tracks = {"players": [], "referees": [], "ball": []}
        fallback_track_id = 10_000

        for frame in frames:
            result = self.model.track(
                frame,
                persist=True,
                conf=self.confidence,
                tracker=self.tracker_config,
                verbose=False,
            )[0]
            tracks["players"].append({})
            tracks["referees"].append({})
            tracks["ball"].append({})

            boxes = result.boxes
            if boxes is None or len(boxes) == 0:
                continue

            xyxy = _tensor_to_numpy(boxes.xyxy)
            class_ids = _tensor_to_numpy(boxes.cls).astype(int)
            confidences = _tensor_to_numpy(boxes.conf) if boxes.conf is not None else np.ones(len(class_ids))
            track_ids = _tensor_to_numpy(boxes.id).astype(int) if boxes.id is not None else None
            names = result.names or getattr(self.model, "names", {})

            for index, bbox in enumerate(xyxy):
                class_id = int(class_ids[index])
                class_name = _class_name(names, class_id)
                category = _class_to_category(class_name)
                if category is None:
                    continue

                confidence = float(confidences[index])
                if category == "ball":
                    object_id = 1
                elif track_ids is not None:
                    object_id = int(track_ids[index])
                else:
                    object_id = fallback_track_id
                    fallback_track_id += 1

                track_info = {
                    "bbox": [float(value) for value in bbox],
                    "class_id": class_id,
                    "class_name": class_name,
                    "confidence": confidence,
                    "interpolated": False,
                }
                if category == "ball":
                    current_ball = tracks[category][-1].get(object_id)
                    if current_ball and current_ball.get("confidence", 0.0) >= confidence:
                        continue
                tracks[category][-1][object_id] = track_info

        if stub_path:
            stub_path.parent.mkdir(parents=True, exist_ok=True)
            with stub_path.open("wb") as handle:
                pickle.dump(tracks, handle)

        return tracks

    @staticmethod
    def interpolate_ball_positions(ball_positions: list[dict[int, TrackInfo]]) -> list[dict[int, TrackInfo]]:
        if not ball_positions:
            return ball_positions

        bbox_values = []
        existing = []
        for frame_tracks in ball_positions:
            bbox = frame_tracks.get(1, {}).get("bbox")
            if bbox:
                bbox_values.append([float(value) for value in bbox])
                existing.append(True)
            else:
                bbox_values.append([np.nan, np.nan, np.nan, np.nan])
                existing.append(False)

        array = np.asarray(bbox_values, dtype=float)
        valid_indices = np.where(~np.isnan(array[:, 0]))[0]
        if len(valid_indices) == 0:
            return ball_positions

        frame_indices = np.arange(len(array))
        interpolated = np.empty_like(array)
        for column in range(4):
            interpolated[:, column] = np.interp(frame_indices, valid_indices, array[valid_indices, column])

        output = []
        for index, bbox in enumerate(interpolated):
            confidence = ball_positions[index].get(1, {}).get("confidence", 0.0)
            output.append(
                {
                    1: {
                        "bbox": [float(value) for value in bbox],
                        "class_name": "ball",
                        "confidence": float(confidence),
                        "interpolated": not existing[index],
                    }
                }
            )
        return output

    @staticmethod
    def add_positions_to_tracks(tracks: Tracks) -> None:
        for object_name, object_tracks in tracks.items():
            for frame_tracks in object_tracks:
                for track_info in frame_tracks.values():
                    bbox = track_info.get("bbox")
                    if not bbox:
                        continue
                    if object_name == "ball":
                        track_info["position"] = get_center_of_bbox(bbox)
                    else:
                        track_info["position"] = get_foot_position(bbox)


def _tensor_to_numpy(value) -> np.ndarray:
    if value is None:
        return np.asarray([])
    if hasattr(value, "detach"):
        value = value.detach()
    if hasattr(value, "cpu"):
        value = value.cpu()
    if hasattr(value, "numpy"):
        return value.numpy()
    return np.asarray(value)


def _class_name(names: dict, class_id: int) -> str:
    name = names.get(class_id, str(class_id)) if isinstance(names, dict) else str(class_id)
    return str(name).strip().lower().replace("_", " ")


def _class_to_category(class_name: str) -> str | None:
    if class_name in {"ball", "sports ball", "football", "soccer ball"}:
        return "ball"
    if class_name in {"referee", "official"}:
        return "referees"
    if class_name in {"player", "goalkeeper", "person"}:
        return "players"
    return None


def _tracks_match_frame_count(tracks: Tracks, expected_frame_count: int) -> bool:
    return (
        isinstance(tracks, dict)
        and set(tracks) >= {"players", "referees", "ball"}
        and all(len(tracks[key]) == expected_frame_count for key in ("players", "referees", "ball"))
    )
