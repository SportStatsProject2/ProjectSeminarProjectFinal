from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from time import perf_counter

from sportstats.vision.annotations import FootballAnnotator
from sportstats.vision.ball_assignment import PlayerBallAssigner
from sportstats.vision.camera_movement import CameraMovementEstimator
from sportstats.vision.speed_distance import SpeedAndDistanceEstimator
from sportstats.vision.team_assignment import TeamAssigner
from sportstats.vision.tracking import FootballTracker
from sportstats.vision.video import read_video, save_video
from sportstats.vision.view_transformer import ViewTransformer


@dataclass(frozen=True)
class PipelineConfig:
    model_path: str
    output_dir: Path
    max_frames: int | None = None
    use_stubs: bool = True
    stub_dir: Path = Path("football_analysis/stubs")
    confidence: float = 0.1
    tracker_config: str = "bytetrack.yaml"


@dataclass(frozen=True)
class FootballAnalysisResult:
    status: str
    message: str
    frames_processed: int = 0
    source_frames: int = 0
    player_tracks: int = 0
    referee_tracks: int = 0
    ball_detections: int = 0
    team_1_ball_control: float = 0.0
    team_2_ball_control: float = 0.0
    output_video: str | None = None
    elapsed_seconds: float = 0.0
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


class FootballAnalysisPipeline:
    def __init__(self, config: PipelineConfig):
        self.config = config

    def run(self, video_path: Path) -> FootballAnalysisResult:
        started_at = perf_counter()
        frames, metadata = read_video(video_path, self.config.max_frames)
        if not frames:
            return FootballAnalysisResult(status="error", message="The video has no readable frames.")

        stub_base = self.config.stub_dir / video_path.stem
        tracker = FootballTracker(
            self.config.model_path,
            confidence=self.config.confidence,
            tracker_config=self.config.tracker_config,
        )
        tracks = tracker.get_object_tracks(
            frames,
            read_from_stub=self.config.use_stubs,
            stub_path=stub_base.with_name(f"{stub_base.name}_tracks.pkl"),
        )
        ball_detections = _frames_with_tracks(tracks["ball"])
        tracks["ball"] = tracker.interpolate_ball_positions(tracks["ball"])
        tracker.add_positions_to_tracks(tracks)

        camera_estimator = CameraMovementEstimator(frames[0])
        camera_movement = camera_estimator.get_camera_movement(
            frames,
            read_from_stub=self.config.use_stubs,
            stub_path=stub_base.with_name(f"{stub_base.name}_camera.pkl"),
        )
        camera_estimator.adjust_positions_to_tracks(tracks, camera_movement)

        view_transformer = ViewTransformer(frame_width=metadata.width, frame_height=metadata.height)
        view_transformer.add_transformed_positions_to_tracks(tracks)

        team_assigner = TeamAssigner()
        team_assigner.assign_players_to_teams(frames, tracks)

        ball_assigner = PlayerBallAssigner()
        team_ball_control = ball_assigner.assign_ball_control(tracks)

        speed_estimator = SpeedAndDistanceEstimator(frame_rate=metadata.fps)
        speed_estimator.add_speed_and_distance_to_tracks(tracks)

        annotator = FootballAnnotator()
        output_frames = annotator.draw_annotations(frames, tracks, team_ball_control)
        output_frames = annotator.draw_camera_movement(output_frames, camera_movement)
        output_frames = annotator.draw_speed_and_distance(output_frames, tracks)

        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.config.output_dir / f"{video_path.stem}_football_analysis.mp4"
        save_video(output_frames, output_path, fps=metadata.fps)

        player_ids = _unique_ids(tracks["players"])
        referee_ids = _unique_ids(tracks["referees"])
        team_1_control, team_2_control = _ball_control_percentages(team_ball_control)
        elapsed = perf_counter() - started_at

        return FootballAnalysisResult(
            status="complete",
            message="Football video analysis completed.",
            frames_processed=len(frames),
            source_frames=metadata.frame_count,
            player_tracks=len(player_ids),
            referee_tracks=len(referee_ids),
            ball_detections=ball_detections,
            team_1_ball_control=team_1_control,
            team_2_ball_control=team_2_control,
            output_video=f"outputs/{output_path.name}",
            elapsed_seconds=round(elapsed, 2),
            notes=[
                "Team colors are estimated from shirt pixels with deterministic k-means.",
                "Track counts are unique tracker IDs across the clip, not the live number of players or referees.",
                "Speed is calculated only inside the calibrated perspective polygon.",
            ],
        )


def _unique_ids(frame_tracks: list[dict[int, dict]]) -> set[int]:
    ids: set[int] = set()
    for frame in frame_tracks:
        ids.update(frame.keys())
    return ids


def _frames_with_tracks(frame_tracks: list[dict[int, dict]]) -> int:
    return sum(1 for frame in frame_tracks if frame)


def _ball_control_percentages(team_ball_control: list[int]) -> tuple[float, float]:
    team_frames = [team for team in team_ball_control if team in {1, 2}]
    if not team_frames:
        return 0.0, 0.0
    team_1 = team_frames.count(1) / len(team_frames) * 100
    team_2 = team_frames.count(2) / len(team_frames) * 100
    return round(team_1, 1), round(team_2, 1)
