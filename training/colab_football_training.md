# Colab Football Detector Training

Run these cells in Google Colab with a GPU runtime.

The target dataset for this project is the Roboflow YOLOv8 export:

- Workspace: `roboflow-jvuqo`
- Project: `football-players-detection-3zvbc`
- Version: `1`
- Classes: `ball`, `goalkeeper`, `player`, `referee`

```python
!pip install ultralytics roboflow
```

```python
from roboflow import Roboflow

rf = Roboflow(api_key="YOUR_ROBOFLOW_API_KEY")
project = rf.workspace("roboflow-jvuqo").project("football-players-detection-3zvbc")
dataset = project.version(1).download("yolov8")
print(dataset.location)
```

Baseline training run used for the demo weights:

```python
from ultralytics import YOLO

model = YOLO("yolov8s.pt")
results = model.train(
    data=f"{dataset.location}/data.yaml",
    epochs=100,
    imgsz=640,
    batch=16,
    device=0,
    project="/content/sportstats_training",
    name="football_yolov8s",
)
```

Download the trained detector and place it in this repository as `models/best.pt`:

```python
from google.colab import files

files.download("/content/sportstats_training/football_yolov8s/weights/best.pt")
```

The first 100-epoch `yolov8s.pt` run on a Colab T4 completed in about 27 minutes and produced these validation metrics:

| Class | Precision | Recall | mAP50 | mAP50-95 |
| --- | ---: | ---: | ---: | ---: |
| all | 0.828 | 0.766 | 0.788 | 0.530 |
| ball | 0.638 | 0.343 | 0.335 | 0.101 |
| goalkeeper | 0.804 | 0.889 | 0.917 | 0.707 |
| player | 0.963 | 0.968 | 0.982 | 0.728 |
| referee | 0.906 | 0.865 | 0.919 | 0.584 |

The ball is the weakest class because it is tiny and has far fewer labels than players. The runtime pipeline interpolates missing ball detections, so this is usable for the demo.

For a higher-accuracy overnight rerun, train at a larger image size:

```python
model = YOLO("yolov8s.pt")
results = model.train(
    data=f"{dataset.location}/data.yaml",
    epochs=100,
    imgsz=960,
    batch=8,
    device=0,
    project="/content/sportstats_training",
    name="football_yolov8s_960",
)
```

If Colab runs out of GPU memory, use `batch=4`. If the new run has better ball validation metrics, download its `weights/best.pt` and replace the local `models/best.pt`.
