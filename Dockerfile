FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg libglib2.0-0 libgl1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-vision.txt ./
ARG INSTALL_VISION=false
RUN pip install -r requirements.txt \
    && if [ "$INSTALL_VISION" = "true" ]; then pip install -r requirements-vision.txt; fi

COPY . .
RUN mkdir -p static/uploads static/outputs football_analysis/stubs

EXPOSE 5000
CMD ["flask", "--app", "app", "run", "--host", "0.0.0.0", "--port", "5000"]
