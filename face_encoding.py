from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

try:
    import face_recognition
except ImportError:
    face_recognition = None


# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────
DEFAULT_DB_PATH = Path("known_faces.db")
LEGACY_JSON_PATH = Path("known_faces.json")
ENCODING_DTYPE = np.float64


# ──────────────────────────────────────────────────────────────────────────────
# Low-level helpers
# ──────────────────────────────────────────────────────────────────────────────

def is_encoding_available() -> bool:
    """Return True when face_recognition is installed."""
    return face_recognition is not None


def generate_encoding(frame_bgr: np.ndarray, location: Optional[tuple] = None) -> Optional[list[float]]:
    """
    Compute a 128-d face encoding from a BGR frame.

    Parameters
    ----------
    frame_bgr : np.ndarray
        A single BGR image (as returned by OpenCV / CameraStream.read()).
    location : tuple | None
        (top, right, bottom, left) bounding box.  When None the function
        auto-detects the first face it finds.

    Returns
    -------
    list[float] | None
        128-element list, or None when no face is detected.
    """
    if face_recognition is None:
        raise RuntimeError("face_recognition is not installed.")

    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

    locations = [location] if location is not None else face_recognition.face_locations(rgb, model="hog")

    if not locations:
        return None  # no face found

    encodings = face_recognition.face_encodings(rgb, known_face_locations=locations)

    if not encodings:
        return None

    return encodings[0].tolist()   # numpy array → plain Python list (JSON-serialisable)


def generate_encoding_from_path(image_path: str | Path) -> Optional[list[float]]:
    """
    Load an image from disk and return its face encoding.

    Returns None if the file cannot be opened or no face is detected.
    """
    img = cv2.imread(str(image_path))
    if img is None:
        return None
    return generate_encoding(img)


def encode_face_from_image(image_bgr: np.ndarray) -> Optional[np.ndarray]:
    """
    Return a single face encoding from an uploaded image.

    Rules for Week 6 quality gate:
    - Exactly one face must be present.
    - Image must not be too blurry.
    """
    if face_recognition is None:
        raise RuntimeError("face_recognition is not installed.")

    if image_bgr is None or image_bgr.size == 0:
        return None

    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
    if blur_score < 40.0:
        return None

    rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb, model="hog")

    if len(face_locations) != 1:
        return None

    encodings = face_recognition.face_encodings(rgb, known_face_locations=face_locations)
    if not encodings:
        return None

    return encodings[0]


def save_encoding_to_db(name: str, encoding: np.ndarray, db_path: str | Path = DEFAULT_DB_PATH) -> bool:
    """Insert one encoding row directly into SQLite for Week 6 image uploads."""
    if encoding is None:
        return False

    name = name.strip()
    if not name:
        return False

    path = Path(db_path)
    encoding_array = np.asarray(encoding, dtype=ENCODING_DTYPE)
    encoding_blob = encoding_array.tobytes()
    encoding_json = json.dumps(encoding_array.tolist())

    try:
        with sqlite3.connect(path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS known_faces (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    encoding BLOB,
                    encoding_json TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                "INSERT INTO known_faces(name, encoding_json, encoding) VALUES (?, ?, ?)",
                (name, encoding_json, encoding_blob),
            )
            conn.commit()
    except sqlite3.Error:
        return False

    return True


def load_known_faces(db: "KnownFaceDB") -> tuple[list[str], list[np.ndarray]]:
    """Return known names and encodings from DB helper rows for live matching."""
    names: list[str] = []
    encodings: list[np.ndarray] = []

    for row in db.get_all_faces():
        names.append(row["name"])
        encodings.append(np.array(row["encoding"], dtype=ENCODING_DTYPE))

    return names, encodings


# ──────────────────────────────────────────────────────────────────────────────
# KnownFaceDB — persistent store of named encodings
# ──────────────────────────────────────────────────────────────────────────────

class KnownFaceDB:
    """
    In-memory + SQLite-backed store of known face encodings.

    Each entry maps a person's name → list of 128-d encoding vectors
    (one person may have multiple reference photos for robustness).

        Table schema (known_faces)
        --------------------------
        id INTEGER PRIMARY KEY AUTOINCREMENT
        name TEXT NOT NULL
        encoding BLOB NOT NULL
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    """

    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH):
        self.db_path: Path = Path(db_path)
        # { name: [encoding_list, ...] }
        self._data: dict[str, list[list[float]]] = {}
        self._ensure_schema()
        self._load()

    # ── Persistence ────────────────────────────────────────────────────────────

    def _connect(self) -> sqlite3.Connection:
        """Return a sqlite connection with dict-like row access disabled for speed."""
        return sqlite3.connect(self.db_path)

    def _ensure_schema(self) -> None:
        """Create required tables/indexes if they do not exist."""
        try:
            with self._connect() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS known_faces (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        encoding BLOB,
                        encoding_json TEXT,
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_known_faces_name ON known_faces(name)"
                )

                cols = {
                    row[1] for row in conn.execute("PRAGMA table_info(known_faces)").fetchall()
                }
                if "encoding" not in cols:
                    conn.execute("ALTER TABLE known_faces ADD COLUMN encoding BLOB")

                # Migrate older rows that only have JSON text encodings to BLOB.
                rows = conn.execute(
                    "SELECT id, encoding_json FROM known_faces WHERE encoding IS NULL AND encoding_json IS NOT NULL"
                ).fetchall()
                for row_id, enc_json in rows:
                    try:
                        encoding = json.loads(enc_json)
                    except (TypeError, json.JSONDecodeError):
                        continue
                    if not isinstance(encoding, list):
                        continue
                    blob = self._encoding_to_blob(encoding)
                    conn.execute(
                        "UPDATE known_faces SET encoding = ? WHERE id = ?",
                        (blob, row_id),
                    )

                conn.commit()
        except sqlite3.Error as exc:
            raise RuntimeError(f"Failed to initialise SQLite DB '{self.db_path}': {exc}") from exc

    def _encoding_to_blob(self, encoding: list[float]) -> bytes:
        """Serialize a 128-d encoding list to SQLite BLOB bytes."""
        arr = np.asarray(encoding, dtype=ENCODING_DTYPE)
        return arr.tobytes()

    def _blob_to_encoding(self, blob: bytes) -> list[float] | None:
        """Deserialize SQLite BLOB bytes back to Python float list."""
        if blob is None:
            return None
        arr = np.frombuffer(blob, dtype=ENCODING_DTYPE)
        if arr.size == 0:
            return None
        return arr.tolist()

    def _load(self) -> None:
        """Load encodings from SQLite and auto-migrate legacy JSON when present."""
        self._data = {}
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT name, encoding, encoding_json FROM known_faces ORDER BY id ASC"
                ).fetchall()
        except sqlite3.Error as exc:
            print(f"[KnownFaceDB] Warning: could not read SQLite DB — {exc}")
            rows = []

        for name, encoding_blob, encoding_json in rows:
            enc = self._blob_to_encoding(encoding_blob) if encoding_blob is not None else None
            if enc is None and encoding_json:
                try:
                    legacy = json.loads(encoding_json)
                except json.JSONDecodeError:
                    legacy = None
                if isinstance(legacy, list):
                    enc = legacy
            if enc is not None:
                self._data.setdefault(name, []).append(enc)

        if self.count() == 0 and LEGACY_JSON_PATH.exists():
            self._migrate_legacy_json(LEGACY_JSON_PATH)

        print(f"[KnownFaceDB] Loaded {self.count()} encoding(s) from {self.db_path}")

    def reload(self) -> None:
        """Reload in-memory data from SQLite."""
        self._load()

    def _migrate_legacy_json(self, legacy_path: Path) -> None:
        """One-time migration from known_faces.json to known_faces.db."""
        try:
            with legacy_path.open("r", encoding="utf-8") as f:
                legacy_data = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"[KnownFaceDB] Legacy JSON migration skipped: {exc}")
            return

        migrated: dict[str, list[list[float]]] = {}
        if isinstance(legacy_data, dict):
            for name, vectors in legacy_data.items():
                if not isinstance(name, str) or not isinstance(vectors, list):
                    continue
                clean_vectors: list[list[float]] = []
                for vec in vectors:
                    if isinstance(vec, list):
                        clean_vectors.append(vec)
                if clean_vectors:
                    migrated[name] = clean_vectors

        if not migrated:
            print("[KnownFaceDB] Legacy JSON migration found no valid encodings.")
            return

        self._data = migrated
        self.save()
        print(
            f"[KnownFaceDB] Migrated {self.count()} encoding(s) from {legacy_path} to {self.db_path}"
        )

    def save(self) -> None:
        """Persist in-memory encodings to SQLite."""
        try:
            with self._connect() as conn:
                conn.execute("DELETE FROM known_faces")
                payload = []
                for name, vectors in self._data.items():
                    for vec in vectors:
                        payload.append((name, self._encoding_to_blob(vec), json.dumps(vec)))
                if payload:
                    conn.executemany(
                        "INSERT INTO known_faces(name, encoding, encoding_json) VALUES (?, ?, ?)",
                        payload,
                    )
                conn.commit()
            print(f"[KnownFaceDB] Saved {self.count()} encoding(s) to {self.db_path}")
        except sqlite3.Error as exc:
            print(f"[KnownFaceDB] Error saving DB: {exc}")

    def get_all_records(self) -> list[tuple[int, str]]:
        """Return raw DB rows for admin/debug visibility in UI."""
        try:
            with self._connect() as conn:
                return conn.execute(
                    "SELECT id, name FROM known_faces ORDER BY id ASC"
                ).fetchall()
        except sqlite3.Error as exc:
            print(f"[KnownFaceDB] Error reading records: {exc}")
            return []

    def get_all_faces(self) -> list[dict[str, object]]:
        """Return face rows as dictionaries: {id, name, encoding}."""
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT id, name, encoding, encoding_json FROM known_faces ORDER BY id ASC"
                ).fetchall()
        except sqlite3.Error as exc:
            print(f"[KnownFaceDB] Error reading faces: {exc}")
            return []

        out: list[dict[str, object]] = []
        for row_id, name, enc_blob, enc_json in rows:
            encoding = self._blob_to_encoding(enc_blob) if enc_blob is not None else None
            if encoding is None and enc_json:
                try:
                    legacy = json.loads(enc_json)
                except json.JSONDecodeError:
                    legacy = None
                if isinstance(legacy, list):
                    encoding = legacy
            if encoding is None:
                continue
            out.append({"id": row_id, "name": name, "encoding": encoding})

        return out

    # ── Add faces ──────────────────────────────────────────────────────────────

    def add_face_from_frame(
        self,
        name: str,
        frame_bgr: np.ndarray,
        location: Optional[tuple] = None,
        auto_save: bool = True,
    ) -> bool:
        """
        Encode a face from a live frame and store it under *name*.

        Returns True on success, False when no face is detected.
        """
        encoding = generate_encoding(frame_bgr, location=location)
        if encoding is None:
            print(f"[KnownFaceDB] No face detected — '{name}' not added.")
            return False

        self._data.setdefault(name, []).append(encoding)
        print(f"[KnownFaceDB] Added encoding for '{name}' (total: {len(self._data[name])})")

        if auto_save:
            self.save()
        return True

    def add_face_from_image(
        self,
        name: str,
        image_path: str | Path,
        auto_save: bool = True,
    ) -> bool:
        """
        Load *image_path* from disk, encode the face and store under *name*.

        Returns True on success.
        """
        encoding = generate_encoding_from_path(image_path)
        if encoding is None:
            print(f"[KnownFaceDB] No face found in '{image_path}' — '{name}' not added.")
            return False

        self._data.setdefault(name, []).append(encoding)
        print(f"[KnownFaceDB] Added encoding for '{name}' from '{image_path}'")

        if auto_save:
            self.save()
        return True

    # ── Remove / clear ─────────────────────────────────────────────────────────

    def remove_face(self, name: str, auto_save: bool = True) -> bool:
        """Remove all encodings for *name*. Returns True if name existed."""
        if name in self._data:
            del self._data[name]
            print(f"[KnownFaceDB] Removed all encodings for '{name}'")
            if auto_save:
                self.save()
            return True
        return False

    def clear(self, auto_save: bool = True) -> None:
        """Delete every known face."""
        self._data.clear()
        if auto_save:
            self.save()

    # ── Query ──────────────────────────────────────────────────────────────────

    def get_all(self) -> tuple[list[np.ndarray], list[str]]:
        """
        Return (encodings_list, names_list) ready for face_recognition.compare_faces.

        Each encoding in *encodings_list* is a numpy array.
        *names_list* has the matching name at the same index.
        """
        encodings: list[np.ndarray] = []
        names: list[str] = []

        for name, enc_list in self._data.items():
            for enc in enc_list:
                encodings.append(np.array(enc))
                names.append(name)

        return encodings, names

    def get_names(self) -> list[str]:
        """Return a sorted list of unique person names."""
        return sorted(self._data.keys())

    def count(self) -> int:
        """Total number of stored encoding vectors (across all names)."""
        return sum(len(v) for v in self._data.values())

    def __len__(self) -> int:
        return self.count()

    def __contains__(self, name: str) -> bool:
        return name in self._data

    def __repr__(self) -> str:
        return f"KnownFaceDB(path={self.db_path!r}, names={self.get_names()})"


# ──────────────────────────────────────────────────────────────────────────────
# Quick standalone demo  (python face_encoding.py)
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if not is_encoding_available():
        print("face_recognition is not installed — cannot run demo.")
    else:
        db = KnownFaceDB(db_path="demo_faces.db")
        print(f"\nDatabase: {db}")

        print(
            "\nTo add a face from an image file:\n"
            "  db.add_face_from_image('YourName', 'path/to/photo.jpg')\n"
        )
        print(
            "To add a face live from webcam, capture a frame then:\n"
            "  db.add_face_from_frame('YourName', frame)\n"
        )
