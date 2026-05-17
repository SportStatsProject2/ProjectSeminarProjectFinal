# Demo Checklist

## Before The Demo

- `models/best.pt` exists locally.
- If it is missing, run `python scripts/download_model.py`.
- The sample video exists locally in `football_analysis/input_videos/`.
- `python -m pytest` passes.
- `python yolo_inference.py football_analysis/input_videos/08fd33_4.mp4 --model models/best.pt --no-stubs --max-frames 120` produces an output video.
- Flask starts with `flask --app app run --debug`.
- GitHub PR shows CI passing.
- The final run uses fresh stubs after the current `models/best.pt` is copied into place.

## Demo Flow

1. Show the home page.
2. Run the match predictor with two teams.
3. Show the passing-network page.
4. Upload or play the precomputed YOLO output.
5. Point out players, referees, ball marker, ball carrier, team possession, camera movement, speed, and distance.
6. Show `docs/architecture.md` and the GitHub issue/PR workflow.
