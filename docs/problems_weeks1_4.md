# Problem Handling (Weeks 1-4)

This document explicitly maps each listed problem to detection and resolution steps.

## Week 1

### Problem: Camera not detected

Symptoms:
- webcam window does not open
- camera index 0 fails

Handling:
1. Run `python test_camera.py`
2. If index 0 fails, retry index 1/2
3. Close apps that may lock camera (meetings/calls)
4. Check OS camera privacy permissions

Evidence:
- terminal output saved in `evidence/week1/logs/week1.log`

### Problem: Library installation errors

Symptoms:
- pip build failure for `dlib` or `face_recognition`

Handling:
1. Use supported Python version and clean venv
2. Upgrade pip: `pip install --upgrade pip`
3. Reinstall requirements: `pip install -r requirements.txt`
4. Validate import by launching app and checking warning banner

Evidence:
- install output in `evidence/week1/logs/week1.log`

## Week 2

### Problem: Slow frame rate

Handling:
1. Reduce resolution to `640 x 480`
2. Close heavy background apps
3. Keep `resize_scale` optimized in recognition flow

Evidence:
- FPS metrics screenshots in `evidence/week2/screenshots/`

### Problem: Camera permission issues

Handling:
1. Verify OS camera access permissions
2. Ensure no other app is holding webcam
3. Check app runtime logs for `camera_error`

Evidence:
- `evidence/runtime_logs/app_events.log`

## Week 3

### Problem: Multiple faces confusion

Handling:
1. Validate boxes drawn for each detected face
2. Use visual checks in multi-face screenshots
3. Confirm no crash and stable UI updates

Evidence:
- `evidence/week3/screenshots/face_boxes_multi.png`

### Problem: Slow processing

Handling:
1. Keep detection model on `hog` for CPU realtime
2. Tune `resize_scale` for speed/accuracy balance
3. Lower camera resolution if required

Evidence:
- FPS snapshots and runtime log entries

## Week 4

### Problem: False matches

Handling:
1. Decrease tolerance (stricter matching)
2. Register multiple clean samples per person
3. Use confidence and repeated detections before trust

Evidence:
- known/unknown screenshots and tolerance notes

### Problem: Lighting issues

Handling:
1. Capture registrations under neutral lighting
2. Keep face clearly visible and frontal
3. Re-register under alternate lighting when needed

Evidence:
- comparative screenshots in `evidence/week4/screenshots/`

## Week 5

### Problem: Encoding storage format

Symptoms:
- database exists but encoding format is unclear
- viva question asks whether encoding is BLOB/bytes

Handling:
1. Verify schema: `PRAGMA table_info(known_faces)`
2. Verify type: `select encoding from known_faces limit 1` then check `type(data)`
3. Ensure streamlit shows DB rows via `get_all_records()`
4. Validate add/delete behavior through before/after SQL queries

Evidence:
- `evidence/week5/week5.log`
- `evidence/week5/screenshots/`
