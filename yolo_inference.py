from __future__ import annotations

import argparse
import os
from pathlib import Path

from sportstats.services.model_assets import DEFAULT_MODEL_URL
from sportstats.services.yolo import analyze_video


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the SportStats football-analysis pipeline on a local video.")
    parser.add_argument("video", type=Path, help="Path to the input football video.")
    parser.add_argument("--model", default="models/best.pt", help="Path to trained football YOLO weights.")
    parser.add_argument(
        "--model-url",
        default=os.getenv("YOLO_MODEL_URL", DEFAULT_MODEL_URL),
        help="Download URL to use when the model path is missing.",
    )
    parser.add_argument("--output-dir", type=Path, default=Path("football_analysis/output_videos"))
    parser.add_argument("--stub-dir", type=Path, default=Path("football_analysis/stubs"))
    parser.add_argument("--max-frames", type=int, default=None)
    parser.add_argument("--no-stubs", action="store_true", help="Ignore cached tracking/camera stubs and recompute.")
    parser.add_argument(
        "--allow-pretrained",
        action="store_true",
        help="Allow fallback to yolov8n.pt when no trained football weights are present.",
    )
    args = parser.parse_args()

    result = analyze_video(
        args.video,
        output_dir=args.output_dir,
        model_path=args.model,
        model_url=args.model_url,
        max_frames=args.max_frames,
        use_stubs=not args.no_stubs,
        stub_dir=args.stub_dir,
        allow_pretrained=args.allow_pretrained,
    )
    print(result.to_dict())
    return 0 if result.status == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
