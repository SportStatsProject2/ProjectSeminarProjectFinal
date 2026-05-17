from __future__ import annotations

import os
from pathlib import Path

from sportstats.services.model_assets import DEFAULT_MODEL_URL


BASE_DIR = Path(__file__).resolve().parent.parent


def _bool_env(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _optional_positive_int_env(name: str, default: int | None = None) -> int | None:
    raw = os.getenv(name)
    if raw is None:
        return default
    value = raw.strip()
    if value.lower() in {"", "0", "none", "false", "off"}:
        return None
    parsed = int(value)
    return parsed if parsed > 0 else None


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", str(250 * 1024 * 1024)))
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", str(BASE_DIR / "static" / "uploads"))
    OUTPUT_FOLDER = os.getenv("OUTPUT_FOLDER", str(BASE_DIR / "static" / "outputs"))
    ALLOWED_VIDEO_EXTENSIONS = {"mp4", "mov", "avi", "mkv"}
    YOLO_MODEL_PATH = os.getenv("YOLO_MODEL_PATH", str(BASE_DIR / "models" / "best.pt"))
    YOLO_MODEL_URL = os.getenv("YOLO_MODEL_URL", DEFAULT_MODEL_URL)
    ALLOW_PRETRAINED_YOLO = _bool_env("ALLOW_PRETRAINED_YOLO", False)
    VISION_MAX_FRAMES = _optional_positive_int_env("VISION_MAX_FRAMES")
    VISION_USE_STUBS = _bool_env("VISION_USE_STUBS", True)
    VISION_STUB_DIR = os.getenv("VISION_STUB_DIR", str(BASE_DIR / "football_analysis" / "stubs"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


class TestConfig(Config):
    TESTING = True
    UPLOAD_FOLDER = "/tmp/sportstats-test/uploads"
    OUTPUT_FOLDER = "/tmp/sportstats-test/outputs"
    VISION_STUB_DIR = "/tmp/sportstats-test/stubs"
    YOLO_MODEL_URL = None
    VISION_MAX_FRAMES = 5
    ALLOW_PRETRAINED_YOLO = False
