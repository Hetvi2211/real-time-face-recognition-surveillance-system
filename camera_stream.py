"""
camera_stream.py — Week 2 | Member A
-------------------------------------
Threaded camera streaming module.
- Runs frame capture in a background thread for smooth, non-blocking reads.
- Tracks real-time FPS.
- Used by app.py (Streamlit UI) and any future modules.

Usage:
    cam = CameraStream(src=0).start()
    frame = cam.read()
    cam.stop()
"""

import cv2
import threading
import time


class CameraStream:
    """
    Threaded webcam capture using OpenCV.

    Parameters
    ----------
    src : int
        Camera index (0 = default webcam, 1 = external, …)
    width : int
        Requested capture width in pixels.
    height : int
        Requested capture height in pixels.
    """

    def __init__(self, src: int = 0, width: int = 640, height: int = 480):
        self.src = src
        self.width = width
        self.height = height

        # Try to open the requested camera; fall back to index 1
        self.cap = cv2.VideoCapture(src)
        if not self.cap.isOpened():
            print(f"[CameraStream] Camera index {src} not found — trying index 1 …")
            self.cap = cv2.VideoCapture(1)
            if not self.cap.isOpened():
                raise RuntimeError(
                    "No camera detected. "
                    "Check that your webcam is connected and not used by another app."
                )

        # Apply requested resolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        # Grab actual values after hardware negotiation
        self.actual_width  = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Read first frame synchronously so callers always have something to show
        ret, self.frame = self.cap.read()
        if not ret:
            raise RuntimeError("Camera opened but could not read the first frame.")

        # Threading control
        self._lock    = threading.Lock()
        self._running = False
        self._thread  = None

        # FPS tracking
        self._fps_start_time  = time.time()
        self._fps_frame_count = 0
        self.fps              = 0.0

        print(
            f"[CameraStream] Camera ready — "
            f"{self.actual_width}x{self.actual_height}"
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> "CameraStream":
        """Start the background capture thread. Returns self for chaining."""
        self._running = True
        self._thread  = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        print("[CameraStream] Streaming started.")
        return self

    def read(self):
        """
        Return the latest captured frame as a BGR numpy array.
        Thread-safe.
        """
        with self._lock:
            return self.frame.copy() if self.frame is not None else None

    def get_fps(self) -> float:
        """Return the current measured FPS."""
        return round(self.fps, 1)

    def get_resolution(self) -> tuple[int, int]:
        """Return (width, height) of the captured stream."""
        return self.actual_width, self.actual_height

    def is_running(self) -> bool:
        """Return True while the capture thread is active."""
        return self._running

    def stop(self) -> None:
        """Stop the capture thread and release the camera."""
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2)
        self.cap.release()
        print("[CameraStream] Camera released.")

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _capture_loop(self) -> None:
        """Continuously grab frames in the background thread."""
        while self._running:
            ret, frame = self.cap.read()

            if not ret:
                print("[CameraStream] Warning: failed to grab frame — retrying …")
                time.sleep(0.05)
                continue

            with self._lock:
                self.frame = frame

            # FPS calculation (rolling over 30 frames)
            self._fps_frame_count += 1
            if self._fps_frame_count >= 30:
                elapsed         = time.time() - self._fps_start_time
                self.fps        = self._fps_frame_count / elapsed if elapsed > 0 else 0
                self._fps_frame_count = 0
                self._fps_start_time  = time.time()


# ------------------------------------------------------------------
# Quick standalone test  (python camera_stream.py)
# ------------------------------------------------------------------
if __name__ == "__main__":
    print("Testing CameraStream — press Q or ESC to quit.\n")

    cam = CameraStream(src=0, width=640, height=480).start()
    win = "CameraStream Test"
    cv2.namedWindow(win, cv2.WINDOW_NORMAL)

    while True:
        frame = cam.read()
        if frame is None:
            continue

        # Overlay FPS and resolution
        w, h = cam.get_resolution()
        cv2.putText(frame, f"FPS : {cam.get_fps()}",   (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.putText(frame, f"Res : {w}x{h}",           (10, 65),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        cv2.imshow(win, frame)

        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), 27):
            break

    cam.stop()
    cv2.destroyAllWindows()
    print("Done.")
