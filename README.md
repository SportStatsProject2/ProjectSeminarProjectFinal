# SportStatsProject

SportStatsProject is a Flask football analytics application that combines statistical match prediction, passing-network visualization, and a full YOLO/OpenCV football video-analysis pipeline.

The project is structured for the seminar marking criteria: demoable use cases, clear run instructions, Docker support, automated checks in CI, architecture documentation, and a GitHub issue/PR workflow.

## Demoable Use Cases

1. Match prediction with Poisson expected goals and Monte Carlo simulation.
2. Elo/team-strength tuning for richer match forecasts.
3. Passing-network graphics from pass-event JSON.
4. Football video analysis with YOLO tracking for players, referees, and ball.
5. Team assignment from shirt colors using k-means color clustering.
6. Ball possession and team ball-control percentages.
7. Camera-motion correction with Lucas-Kanade optical flow.
8. Perspective transformation from broadcast pixels to pitch meters.
9. Player speed and distance-covered overlays.

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
cp .env.example .env
flask --app app run --debug
```

Open http://127.0.0.1:5000.

## Full YOLO Runtime

Install the optional computer-vision dependencies:

```bash
python -m pip install -r requirements-vision.txt
```

Put the trained detector weights here:

```text
models/best.pt
```

The public project model can be downloaded automatically:

```bash
python scripts/download_model.py
```

Then run the analysis on a local video:

```bash
python yolo_inference.py football_analysis/input_videos/08fd33_4.mp4 --model models/best.pt
```

The annotated video is written to `football_analysis/output_videos/`. The Flask upload page writes outputs to `static/outputs/`.

If `models/best.pt` is missing, the Flask app can download it from `YOLO_MODEL_URL` in `.env` before running the first video analysis.

If you only want a baseline smoke test with the COCO model, add `--allow-pretrained` to the CLI or set `ALLOW_PRETRAINED_YOLO=1` in `.env`. The baseline can detect people and sports balls, but it will not classify football-specific players/referees/goalkeepers as well as the trained model.

## Training

Use Roboflow or Kaggle manually for the data, then train on a GPU machine or Google Colab.

```bash
python -m pip install -r requirements-training.txt
export ROBOFLOW_API_KEY=your_key
python scripts/download_roboflow_dataset.py --workspace your-workspace --project your-project --version 1 --format yolov8
python scripts/train_yolo.py --data datasets/data.yaml --model yolov8x.pt --epochs 100 --imgsz 640
```

For Colab, use `training/colab_football_training.md`.

## Docker

Lightweight web app:

```bash
docker compose up --build
```

With optional YOLO runtime:

```bash
INSTALL_VISION=true docker compose up --build
```

## Tests

```bash
ruff check .
pytest
```

Without pytest installed locally:

```bash
python -m unittest discover
```

CI runs Ruff and Pytest on pull requests and pushes to `dev` or `main`.

## Project Structure

```text
app.py                         Flask entry point
sportstats/                    Application package
  services/                    Match predictor, passing network, YOLO service wrapper
  vision/                      Full football CV pipeline
templates/                     Server-rendered pages
static/css/app.css             UI styling
scripts/                       Dataset download and YOLO training helpers
training/                      Colab training notes
tests/                         Route and service tests
docs/                          Architecture, process, and CV documentation
.github/workflows/ci.yml       CI merge gate
```

## Branch Workflow

Use this flow:

```text
feature branch -> pull request into dev -> review + CI -> merge into dev
dev -> pull request into main -> review + CI -> release merge
```

Every issue should have acceptance criteria and an assignee. Every PR should reference an issue with `Closes #123`, pass CI, and receive at least one meaningful review from the other teammate before merge.

## Team Roles

- Daniel: YOLO/OpenCV video analysis, detector training, model integration, CV demo preparation.
- Assylkhan Balmukhanov: Flask website, statistical predictor, Elo/Monte Carlo workstream, CI/CD, documentation, release workflow.
- Shared: issues, PR reviews, demo script, README updates, and final seminar presentation.
