from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

import cv2
import numpy as np

try:
    import face_recognition
except ImportError:
    face_recognition = None

from face_encoding import KnownFaceDB, generate_encoding


@dataclass
class MatchResult:
    """Holds recognition data for one detected face."""
    name: str
    confidence: float
    location: tuple[int, int, int, int]
    is_known: bool = field(init=False)

    def __post_init__(self):
        self.is_known = self.name != "Unknown"


def match_encoding(
    unknown_encoding: np.ndarray,
    known_encodings: list[np.ndarray],
    known_names: list[str],
    tolerance: float = 0.50,
) -> tuple[str, float]:
    """
    Compare *unknown_encoding* against every known encoding.

    Uses majority voting when a person has multiple reference photos:
      - Count votes per candidate name.
      - The winner must also have the best (lowest) average face distance.

    Parameters
    ----------
    tolerance : float
        Maximum face distance to count as a match (lower = stricter).
        0.40 very strict, 0.50 good default, 0.60 lenient (library default).

    Returns
    -------
    (name, confidence)
        confidence is 1 - best_distance, clamped to [0, 1].
    """
    if face_recognition is None:
        raise RuntimeError("face_recognition is not installed.")

    if not known_encodings:
        return "Unknown", 0.0

    matches = face_recognition.compare_faces(known_encodings, unknown_encoding, tolerance=tolerance)
    distances = face_recognition.face_distance(known_encodings, unknown_encoding)

    if not any(matches):
        best_dist = float(np.min(distances))
        confidence = max(0.0, round(1.0 - best_dist, 3))
        return "Unknown", confidence

    candidate_votes: dict[str, list[float]] = {}
    for i, (matched, dist) in enumerate(zip(matches, distances)):
        if matched:
            name = known_names[i]
            candidate_votes.setdefault(name, []).append(dist)

    winner = max(
        candidate_votes,
        key=lambda n: (len(candidate_votes[n]), -sum(candidate_votes[n]) / len(candidate_votes[n])),
    )
    best_dist = min(candidate_votes[winner])
    confidence = round(max(0.0, min(1.0, 1.0 - best_dist)), 3)

    return winner, confidence


def recognise_frame(
    frame_bgr: np.ndarray,
    db: KnownFaceDB,
    tolerance: float = 0.50,
    resize_scale: float = 0.5,
    model: str = "hog",
) -> list[MatchResult]:
    """
    Detect all faces in *frame_bgr* and identify each one.

    Parameters
    ----------
    frame_bgr : np.ndarray
        Live BGR frame from CameraStream.
    db : KnownFaceDB
        The in-memory database of known encodings.
    tolerance : float
        Match strictness (see match_encoding).
    resize_scale : float
        Downscale factor before detection for speed (0.25–1.0).
    model : str
        "hog" (CPU, fast) or "cnn" (GPU, accurate).

    Returns
    -------
    list[MatchResult]
        One entry per detected face.
    """
    if face_recognition is None:
        raise RuntimeError("face_recognition is not installed.")

    if not 0 < resize_scale <= 1.0:
        raise ValueError("resize_scale must be between 0 and 1.")

    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

    if resize_scale == 1.0:
        small_rgb = rgb
    else:
        small_rgb = cv2.resize(rgb, (0, 0), fx=resize_scale, fy=resize_scale)

    small_locations = face_recognition.face_locations(small_rgb, model=model)

    if not small_locations and resize_scale != 1.0:
        small_rgb = rgb
        resize_scale = 1.0
        small_locations = face_recognition.face_locations(small_rgb, model=model)

    if not small_locations:
        return []

    inv = 1.0 / resize_scale
    h, w = frame_bgr.shape[:2]
    orig_locations = [
        (
            max(0, min(int(t * inv), h)),
            max(0, min(int(r * inv), w)),
            max(0, min(int(b * inv), h)),
            max(0, min(int(l * inv), w)),
        )
        for t, r, b, l in small_locations
    ]

    encodings = face_recognition.face_encodings(rgb, known_face_locations=orig_locations)

    known_encodings, known_names = db.get_all()
    results: list[MatchResult] = []

    for enc, loc in zip(encodings, orig_locations):
        name, confidence = match_encoding(enc, known_encodings, known_names, tolerance=tolerance)
        results.append(MatchResult(name=name, confidence=confidence, location=loc))

    return results


def draw_recognition_results(
    frame: np.ndarray,
    results: list[MatchResult],
    show_confidence: bool = True,
) -> np.ndarray:
    """
    Draw labelled bounding boxes on *frame* for each MatchResult.

    - Green box + name  → known person
    - Red box + "Unknown (XX%)" → unrecognised face
    """
    for r in results:
        top, right, bottom, left = r.location
        color = (0, 200, 0) if r.is_known else (0, 0, 220)

        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

        label = r.name
        if show_confidence:
            label += f" ({int(r.confidence * 100)}%)"

        (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
        cv2.rectangle(
            frame,
            (left, bottom - text_h - 10),
            (left + text_w + 4, bottom),
            color,
            cv2.FILLED,
        )
        cv2.putText(
            frame,
            label,
            (left + 2, bottom - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            1,
        )

    return frame


class RecognitionStats:
    """Track rolling recognition metrics over the last N frames."""

    def __init__(self, window: int = 60):
        self._window = window
        self._history: list[dict] = []
        self._last_seen: dict[str, float] = {}

    def update(self, results: list[MatchResult]) -> None:
        ts = time.time()
        for r in results:
            if r.is_known:
                self._last_seen[r.name] = ts

        self._history.append({"ts": ts, "count": len(results), "known": sum(r.is_known for r in results)})
        if len(self._history) > self._window:
            self._history.pop(0)

    @property
    def avg_face_count(self) -> float:
        if not self._history:
            return 0.0
        return round(sum(h["count"] for h in self._history) / len(self._history), 1)

    @property
    def last_seen(self) -> dict[str, str]:
        """Return {name: "X s ago"} for recently seen known faces."""
        now = time.time()
        return {
            name: f"{int(now - ts)}s ago"
            for name, ts in sorted(self._last_seen.items(), key=lambda x: -x[1])
        }
