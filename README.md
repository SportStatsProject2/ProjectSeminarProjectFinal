# SportStatsProject

SportStatsProject is a Flask football analytics application that combines statistical match prediction, passing-network visualization, and a full YOLO/OpenCV football video-analysis pipeline.

The repository includes local run instructions, Docker support, automated checks, architecture notes, and a pull-request workflow.

## Core Capabilities

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

Docker is the simplest reproducible run path for grading because it builds the same Python runtime and starts Flask on port `5000`.

```bash
cp .env.example .env
docker compose up --build
```

Open http://127.0.0.1:5000.

The default Docker run starts the lightweight web app: match predictor, xG calculator, Elo ratings, World Cup predictor, passing network, architecture page, and the vision page shell.

For the full YOLO video-analysis runtime, build with the optional CV dependencies:

```bash
cp .env.example .env
INSTALL_VISION=true docker compose up --build
```

The compose file mounts these local folders into the container so uploads, generated videos, cached stubs, and model weights survive container restarts:

```text
./static/uploads      -> /app/static/uploads
./static/outputs      -> /app/static/outputs
./football_analysis/stubs -> /app/football_analysis/stubs
./models              -> /app/models
```

`YOLO_MODEL_URL` is already set in `.env.example`, so the app can download the public `models/best.pt` release asset on the first video run if it is not already in `./models`.

Useful Docker commands:

```bash
docker compose up --build          # build and start the app
docker compose down                # stop containers
docker compose logs -f web         # follow Flask logs
docker compose exec web flask --app app routes
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

- Daniel: YOLO/OpenCV video analysis, detector training, model integration, CV presentation workflow.
- Assylkhan Balmukhanov: Flask website, statistical predictor, Elo/Monte Carlo workstream, CI/CD, documentation, release workflow.
- Shared: issues, PR reviews, demo script, README updates, and final seminar presentation.
