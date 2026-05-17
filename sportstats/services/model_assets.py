from __future__ import annotations

from pathlib import Path
import shutil
from urllib.request import urlopen


DEFAULT_MODEL_URL = (
    "https://github.com/SportStatsProject2/ProjectSeminarProjectFinal/"
    "releases/download/yolo-model-v1/best.pt"
)


def ensure_model_file(model_path: str | Path, model_url: str | None = None) -> Path | None:
    path = Path(model_path).expanduser()
    if path.exists():
        return path
    if not model_url:
        return None
    return download_model(model_url, path)


def download_model(model_url: str, destination: str | Path, *, timeout: int = 120) -> Path:
    destination_path = Path(destination).expanduser()
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = destination_path.with_name(f"{destination_path.name}.download")

    try:
        with urlopen(model_url, timeout=timeout) as response, temporary_path.open("wb") as handle:
            shutil.copyfileobj(response, handle)
        if temporary_path.stat().st_size == 0:
            raise ValueError("Downloaded model file is empty.")
        temporary_path.replace(destination_path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise

    return destination_path
