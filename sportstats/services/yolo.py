from __future__ import annotations

from pathlib import Path

from sportstats.vision import FootballAnalysisPipeline, FootballAnalysisResult, PipelineConfig


def is_allowed_video(filename: str, allowed_extensions: set[str]) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def analyze_video(
    video_path: Path,
    *,
    output_dir: Path,
    model_path: str | None = None,
    max_frames: int | None = 300,
    use_stubs: bool = True,
    stub_dir: Path = Path("football_analysis/stubs"),
    allow_pretrained: bool = False,
) -> FootballAnalysisResult:
    if not video_path.exists():
        return FootballAnalysisResult(status="error", message="Video file does not exist.")

    resolved_model = _resolve_model_path(model_path, allow_pretrained=allow_pretrained)
    if resolved_model is None:
        return FootballAnalysisResult(
            status="unavailable",
            message="The football vision model is not available on this server.",
        )

    missing = _missing_optional_dependencies()
    if missing:
        return FootballAnalysisResult(
            status="unavailable",
            message=f"The computer-vision runtime is missing: {', '.join(missing)}.",
        )

    try:
        pipeline = FootballAnalysisPipeline(
            PipelineConfig(
                model_path=resolved_model,
                output_dir=output_dir,
                max_frames=max_frames,
                use_stubs=use_stubs,
                stub_dir=stub_dir,
            )
        )
        return pipeline.run(video_path)
    except Exception as exc:  # pragma: no cover - exercised by real CV runtime
        return FootballAnalysisResult(status="error", message=f"Video analysis failed: {exc}")


def _missing_optional_dependencies() -> list[str]:
    missing = []
    for module_name, package_name in {"cv2": "opencv-python", "ultralytics": "ultralytics"}.items():
        try:
            __import__(module_name)
        except ImportError:
            missing.append(package_name)
    return missing


def _resolve_model_path(model_path: str | None, *, allow_pretrained: bool) -> str | None:
    if model_path:
        path = Path(model_path).expanduser()
        if path.exists():
            return str(path)
    default_path = Path("models/best.pt")
    if default_path.exists():
        return str(default_path)
    if allow_pretrained:
        return "yolov8n.pt"
    return None
