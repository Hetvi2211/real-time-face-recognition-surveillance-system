"""
face_detection.py
Week 3 - Face Detection Module
Detect faces and draw bounding boxes.
"""

import cv2

try:
    import face_recognition
except ImportError as exc:
    face_recognition = None
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None


def is_face_detection_available() -> bool:
    """Return True when face_recognition is installed and importable."""
    return face_recognition is not None


def get_face_detection_error() -> str | None:
    """Return a user-friendly dependency error when face detection is unavailable."""
    if _IMPORT_ERROR is None:
        return None
    return (
        "face_recognition is not installed. Run 'pip install -r requirements.txt' "
        "and ensure dlib builds successfully."
    )


def detect_faces(frame, model: str = "hog", resize_scale: float = 0.5):
    """
    Detect faces in a BGR frame.

    The frame is optionally resized before detection to improve real-time
    performance. Returned coordinates are scaled back to the original frame.
    """
    if face_recognition is None:
        raise RuntimeError(get_face_detection_error())

    if frame is None:
        return []

    if not 0 < resize_scale <= 1.0:
        raise ValueError("resize_scale must be between 0 and 1.")

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    if resize_scale != 1.0:
        processed_frame = cv2.resize(
            rgb_frame,
            (0, 0),
            fx=resize_scale,
            fy=resize_scale,
        )
    else:
        processed_frame = rgb_frame

    face_locations = face_recognition.face_locations(processed_frame, model=model)

    if resize_scale == 1.0:
        return face_locations

    scale_back = 1.0 / resize_scale
    frame_height, frame_width = frame.shape[:2]
    scaled_locations = []

    for top, right, bottom, left in face_locations:
        scaled_locations.append(
            (
                max(0, min(int(top * scale_back), frame_height)),
                max(0, min(int(right * scale_back), frame_width)),
                max(0, min(int(bottom * scale_back), frame_height)),
                max(0, min(int(left * scale_back), frame_width)),
            )
        )

    return scaled_locations


def draw_faces(frame, face_locations, color=(0, 255, 0), thickness: int = 2):
    """Draw bounding boxes around each detected face."""
    for top, right, bottom, left in face_locations:
        cv2.rectangle(frame, (left, top), (right, bottom), color, thickness)

    return frame
