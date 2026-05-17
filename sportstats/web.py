from __future__ import annotations

import json
import logging
from pathlib import Path
from uuid import uuid4

from flask import Flask, jsonify, render_template, request
from werkzeug.utils import secure_filename

from sportstats.config import BASE_DIR, Config
from sportstats.services.passing_network import build_demo_network, build_network
from sportstats.services.prediction import TeamProfile, predict_match
from sportstats.services.yolo import analyze_video, is_allowed_video


def create_app(config_object: type[Config] = Config) -> Flask:
    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder=str(BASE_DIR / "templates"),
        static_folder=str(BASE_DIR / "static"),
    )
    app.config.from_object(config_object)
    _configure_logging(app)
    _ensure_runtime_dirs(app)

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/predictor")
    def predictor():
        return render_template("predictor.html", result=None)

    @app.post("/predictor")
    def predictor_submit():
        result = _prediction_from_mapping(request.form.to_dict())
        return render_template("predictor.html", result=result)

    @app.post("/api/predict")
    def api_predict():
        payload = request.get_json(silent=True) or {}
        result = _prediction_from_mapping(payload)
        return jsonify(result)

    @app.get("/passing-network")
    def passing_network():
        return render_template("passing_network.html", network=build_demo_network(), error=None)

    @app.post("/passing-network")
    def passing_network_submit():
        raw_events = request.form.get("passes", "").strip()
        try:
            events = json.loads(raw_events) if raw_events else []
            network = build_network(events) if events else build_demo_network()
            return render_template("passing_network.html", network=network, error=None)
        except (TypeError, ValueError) as exc:
            app.logger.info("Invalid passing network payload: %s", exc)
            return (
                render_template(
                    "passing_network.html",
                    network=build_demo_network(),
                    error="Pass events need passer, receiver, start_x, start_y, end_x and end_y fields.",
                ),
                400,
            )

    @app.get("/vision")
    def vision():
        return render_template("vision.html", analysis=None, error=None)

    @app.post("/vision")
    def vision_submit():
        uploaded_file = request.files.get("video")
        if uploaded_file is None or uploaded_file.filename == "":
            return render_template("vision.html", analysis=None, error="Choose a match video first."), 400

        filename = secure_filename(uploaded_file.filename)
        if not is_allowed_video(filename, app.config["ALLOWED_VIDEO_EXTENSIONS"]):
            return render_template("vision.html", analysis=None, error="Upload an MP4, MOV, AVI or MKV video."), 400

        upload_path = Path(app.config["UPLOAD_FOLDER"]) / _unique_upload_filename(filename)
        uploaded_file.save(upload_path)
        app.logger.info("Saved uploaded video to %s", upload_path)

        analysis = analyze_video(
            upload_path,
            output_dir=Path(app.config["OUTPUT_FOLDER"]),
            model_path=app.config.get("YOLO_MODEL_PATH"),
            model_url=app.config.get("YOLO_MODEL_URL"),
            max_frames=app.config["VISION_MAX_FRAMES"],
            use_stubs=app.config["VISION_USE_STUBS"],
            stub_dir=Path(app.config["VISION_STUB_DIR"]),
            allow_pretrained=app.config["ALLOW_PRETRAINED_YOLO"],
        )
        return render_template("vision.html", analysis=analysis, error=None)

    @app.get("/architecture")
    def architecture():
        return render_template("architecture.html")

    @app.get("/healthz")
    def healthz():
        return jsonify({"status": "ok", "service": "sportstats"})

    @app.get("/favicon.ico")
    def favicon():
        return app.send_static_file("favicon.svg")

    @app.errorhandler(413)
    def file_too_large(_error):
        return render_template("vision.html", analysis=None, error="The uploaded video is too large."), 413

    return app


def _prediction_from_mapping(payload: dict) -> dict:
    home = TeamProfile(
        name=str(payload.get("home_name") or "Home FC"),
        elo=_float_value(payload.get("home_elo"), 1540.0),
        attack_strength=_float_value(payload.get("home_attack"), 1.12),
        defense_strength=_float_value(payload.get("home_defense"), 0.94),
    )
    away = TeamProfile(
        name=str(payload.get("away_name") or "Away FC"),
        elo=_float_value(payload.get("away_elo"), 1490.0),
        attack_strength=_float_value(payload.get("away_attack"), 1.04),
        defense_strength=_float_value(payload.get("away_defense"), 1.02),
    )
    simulations = int(_float_value(payload.get("simulations"), 20000.0))
    return predict_match(home, away, simulations=simulations)


def _float_value(value, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _ensure_runtime_dirs(app: Flask) -> None:
    for key in ("UPLOAD_FOLDER", "OUTPUT_FOLDER", "VISION_STUB_DIR"):
        Path(app.config[key]).mkdir(parents=True, exist_ok=True)


def _configure_logging(app: Flask) -> None:
    logging.basicConfig(
        level=app.config.get("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def _unique_upload_filename(filename: str) -> str:
    path = Path(filename)
    suffix = path.suffix.lower()
    stem = secure_filename(path.stem) or "upload"
    return f"{stem}_{uuid4().hex[:8]}{suffix}"
