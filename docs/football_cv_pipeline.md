# Football Computer-Vision Pipeline

This implements the full project from the video transcript with updated runtime choices.

## Implemented Steps

1. Read a match video with OpenCV.
2. Detect and track players, referees, and ball with Ultralytics YOLO + ByteTrack.
3. Normalize `goalkeeper` and `person` detections into the player track group for downstream metrics.
4. Cache tracks and camera movement in `football_analysis/stubs/` so repeated runs are faster.
5. Draw cleaner annotations: player ellipses, track IDs, referee ellipses, ball triangles, and ball-carrier markers.
6. Assign teams from shirt pixels with deterministic k-means color clustering.
7. Interpolate missing ball detections.
8. Assign ball possession to the closest player foot.
9. Compute team ball-control percentages over time.
10. Estimate cumulative camera movement using OpenCV sparse Lucas-Kanade optical flow on top/bottom image bands.
11. Adjust tracked positions by camera displacement.
12. Apply a perspective transform from broadcast pixels into pitch-meter coordinates.
13. Estimate player speed and distance covered.
14. Save an annotated output video.

## Why This Differs From The Old Video

- The code uses Ultralytics `model.track(..., tracker="bytetrack.yaml", persist=True)` instead of manually calling `supervision.ByteTrack`. This avoids depending on old `supervision` API names.
- Shirt-color clustering uses NumPy instead of scikit-learn, so the app does not need another heavy dependency.
- Ball interpolation uses NumPy instead of pandas.
- The web app does not silently download a pretrained model by default. Put trained weights at `models/best.pt` for reproducible demos.

## Run

```bash
python -m pip install -r requirements-vision.txt
python yolo_inference.py football_analysis/input_videos/08fd33_4.mp4 --model models/best.pt
```

Use `--no-stubs` after changing model weights or calibration values.

## Calibration

The perspective transform uses default pixel vertices for the Bundesliga 1080p sample from the video:

```text
(110, 1035), (265, 275), (910, 260), (1640, 915)
```

If your source video has a different camera angle, update `DEFAULT_VERTICES_1080P` in `sportstats/vision/view_transformer.py` or add a calibration UI later.

## What You Still Need To Do Manually

- Download the Bundesliga sample clip, such as `08fd33_4.mp4`, and place it in `football_analysis/input_videos/`.
- Download/export the Roboflow football player detection dataset with your own API key.
- Train the detector on Colab or another GPU machine.
- Copy the trained `best.pt` into `models/best.pt`.
- Leave `VISION_MAX_FRAMES=0` or unset for full-video processing. Set a positive value only when you need a short smoke test.
