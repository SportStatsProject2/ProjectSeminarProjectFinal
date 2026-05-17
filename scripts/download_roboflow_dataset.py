from __future__ import annotations

import argparse
import os
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Download a Roboflow football dataset for YOLO training.")
    parser.add_argument("--workspace", required=True, help="Roboflow workspace slug.")
    parser.add_argument("--project", required=True, help="Roboflow project slug.")
    parser.add_argument("--version", required=True, type=int, help="Roboflow dataset version number.")
    parser.add_argument("--format", default="yolov8", choices=["yolov5", "yolov8"], help="Dataset export format.")
    parser.add_argument("--location", default="datasets", type=Path, help="Local output directory.")
    parser.add_argument("--api-key", default=os.getenv("ROBOFLOW_API_KEY"), help="Roboflow API key.")
    args = parser.parse_args()

    if not args.api_key:
        raise SystemExit("Set ROBOFLOW_API_KEY or pass --api-key.")

    try:
        from roboflow import Roboflow
    except ImportError as exc:
        raise SystemExit("Install training dependencies first: python -m pip install -r requirements-training.txt") from exc

    args.location.parent.mkdir(parents=True, exist_ok=True)
    rf = Roboflow(api_key=args.api_key)
    project = rf.workspace(args.workspace).project(args.project)
    dataset = project.version(args.version).download(args.format, location=str(args.location), overwrite=True)
    print(dataset.location)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
