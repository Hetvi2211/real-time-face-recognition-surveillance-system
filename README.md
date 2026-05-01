# Real-Time Face Recognition Surveillance System

## Project Explanation

This project is a real-time surveillance application that detects and recognizes faces from a live camera stream. It uses computer vision to locate faces frame-by-frame, converts each face into numerical embeddings, and compares them against a registered set of known faces.

If a match is found, the system displays the person's name. If no match is found, the face is labeled as Unknown. The project is designed for practical security monitoring use cases and demonstrates an end-to-end AI pipeline: video capture, detection, encoding, matching, and event logging.

## Features

- Real-time camera stream processing
- Face detection on each frame
- Face encoding and matching against known faces
- Registration and storage of known people
- Unknown face labeling for unmatched identities
- Adjustable matching tolerance for recognition sensitivity
- Event logging for traceability and reporting
- Modular Python files for easy maintenance and extension

## Tech Stack

- Language: Python 3.x
- Computer Vision: OpenCV
- Face Recognition: face_recognition (dlib-based)
- Numerical Computing: NumPy
- App/UI Layer: Streamlit (project UI flow)
- Data Storage: JSON/SQLite-based project storage
- Version Control: Git and GitHub

## Project Structure

- `app.py`: Main application entry point
- `camera_stream.py`: Camera input and frame handling
- `face_detection.py`: Face detection logic
- `face_encoding.py`: Face encoding generation
- `face_matching.py`: Matching logic for known vs unknown faces
- `known_faces.json`: Registered known faces metadata
- `test_camera.py`: Camera testing utility
- `docs/`: Reports and project documentation
- `evidence/`: Week-wise evidence, logs, and screenshots

## Setup and Run

1. Clone the repository:

```bash
git clone https://github.com/Hetvi2211/real-time-face-recognition-surveillance-system.git
cd real-time-face-recognition-surveillance-system
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the project:

```bash
python app.py
```

<<<<<<< HEAD
## Demo Images

Add your screenshots in `evidence/screenshots/` and update the paths below.

![Live Detection Demo](evidence/screenshots/live-detection-demo.png)
![Known Person Recognition](evidence/screenshots/known-person-recognition.png)
![Unknown Face Alert](evidence/screenshots/unknown-face-alert.png)

## Future Improvements
=======
## Demo Images

Add your screenshots in the `evidence/week*/screenshots/` folders and update the paths below.

```markdown
![Live Detection Demo](evidence/week5/screenshots/live-detection-demo.png)
![Known Person Recognition](evidence/week6/screenshots/known-person-recognition.png)
![Unknown Face Alert](evidence/week7/screenshots/unknown-face-alert.png)
```

Example section after adding real images:

![Live Detection Demo](evidence/week5/screenshots/live-detection-demo.png)
![Known Person Recognition](evidence/week6/screenshots/known-person-recognition.png)
![Unknown Face Alert](evidence/week7/screenshots/unknown-face-alert.png)

## Future Improvements

>>>>>>> ace8618 (Cleanup: remove unnecessary comments and polish UI)
- Multi-camera support
- Cloud sync for known faces
- Alert channels (email/SMS)
- Performance optimization for low-power devices
- Additional analytics and attendance reporting
