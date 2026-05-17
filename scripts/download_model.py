from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from sportstats.services.model_assets import DEFAULT_MODEL_URL, download_model  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Download the SportStats trained YOLO model.")
    parser.add_argument(
        "--url",
        default=os.getenv("YOLO_MODEL_URL", DEFAULT_MODEL_URL),
        help="Direct URL to the model weights.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(os.getenv("YOLO_MODEL_PATH", "models/best.pt")),
        help="Where to write the model weights.",
    )
    parser.add_argument("--force", action="store_true", help="Download even when the output file already exists.")
    args = parser.parse_args()

    if args.output.exists() and not args.force:
        print(f"Model already exists at {args.output}")
        return

    path = download_model(args.url, args.output)
    print(f"Downloaded model to {path}")


if __name__ == "__main__":
    main()
