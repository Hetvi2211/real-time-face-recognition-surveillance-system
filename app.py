import time
import pathlib
import tempfile
import logging
from datetime import datetime

import cv2
import streamlit as st

from camera_stream import CameraStream
from face_encoding import KnownFaceDB, is_encoding_available
from face_matching import RecognitionStats, draw_recognition_results, recognise_frame


logging.basicConfig(
    filename="app_events.log",
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
)


EVIDENCE_LOG_PATH = pathlib.Path("evidence/runtime_logs/app_events.log")


def log_event(event: str, details: str = "") -> None:
    """Append timestamped runtime events for weekly evidence logs."""
    EVIDENCE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {event}"
    if details:
        line += f" | {details}"
    with EVIDENCE_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(line + "\n")

st.set_page_config(
    page_title="Face Recognition Surveillance",
    page_icon="🎥",
    layout="wide",
)

DEFAULTS = {
    "cam": None,
    "streaming": False,
    "db": None,
    "stats": RecognitionStats(),
    "tolerance": 0.50,
    "capture_pending": False,
    "capture_name": "",
    "last_snap": None,
    "last_logged_seen": {},
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

if st.session_state.db is None:
    st.session_state.db = KnownFaceDB()


def start_camera(src: int, width: int, height: int) -> None:
    try:
        cam = CameraStream(src=src, width=width, height=height).start()
        st.session_state.cam = cam
        st.session_state.streaming = True
        logging.info("Camera started")
        log_event("camera_started", f"index={src}, resolution={width}x{height}")
    except RuntimeError as exc:
        log_event("camera_error", str(exc))
        st.error(f"Camera error: {exc}")


def stop_camera() -> None:
    if st.session_state.cam is not None:
        st.session_state.cam.stop()
        st.session_state.cam = None
        st.session_state.streaming = False
        logging.info("Camera stopped")
        log_event("camera_stopped")

with st.sidebar:
    st.image("https://img.icons8.com/emoji/96/video-camera-emoji.png", width=80)
    st.title("Controls")
    st.markdown("---")

    st.subheader("📷 Camera")
    cam_index = st.selectbox("Camera Index", options=[0, 1, 2], index=0)
    resolution = st.selectbox("Resolution",
                              options=["640 × 480", "1280 × 720", "1920 × 1080"], index=0)
    res_w, res_h = map(int, resolution.replace(" ", "").split("×"))

    if not st.session_state.streaming:
        if st.button("▶  Start Camera", use_container_width=True, type="primary"):
            start_camera(cam_index, res_w, res_h)
            st.rerun()
    else:
        if st.button("⏹  Stop Camera", use_container_width=True, type="secondary"):
            stop_camera()
            st.rerun()

    st.markdown("---")

    st.subheader("🔎 Recognition")
    st.session_state.tolerance = st.slider(
        "Match tolerance",
        min_value=0.35, max_value=0.65,
        value=float(st.session_state.tolerance), step=0.01,
        help="Lower = stricter. 0.50 recommended."
    )

    st.markdown("---")

    if is_encoding_available():
        st.subheader("➕ Register Face")
        st.caption("Upload a clear photo and name, or capture from webcam.")

        uploaded = st.file_uploader("Upload photo", type=["jpg", "jpeg", "png"],
                                    label_visibility="collapsed")
        name_upload = st.text_input("Name (upload)", placeholder="e.g. Alice")
        if st.button("Add from photo", use_container_width=True):
            if not name_upload.strip():
                st.warning("Enter a name first.")
            elif uploaded is None:
                st.warning("Upload a photo first.")
            else:
                suffix = pathlib.Path(uploaded.name).suffix
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(uploaded.read())
                    tmp_path = tmp.name
                ok = st.session_state.db.add_face_from_image(name_upload.strip(), tmp_path)
                if ok:
                    log_event("face_registered_photo", f"name={name_upload.strip()}")
                else:
                    log_event("face_register_photo_failed", f"name={name_upload.strip()}")
                st.success(f"✅ Added '{name_upload.strip()}'") if ok else st.error("No face found in photo.")

        st.markdown("---")

        name_live = st.text_input("Name (webcam)", placeholder="e.g. Bob")
        if st.button("📸 Capture from webcam", use_container_width=True,
                     disabled=not st.session_state.streaming):
            if not name_live.strip():
                st.warning("Enter a name first.")
            else:
                st.session_state.capture_pending = True
                st.session_state.capture_name = name_live.strip()
                log_event("face_capture_requested", f"name={name_live.strip()}")

        if st.session_state.last_snap is not None:
            st.image(cv2.cvtColor(st.session_state.last_snap, cv2.COLOR_BGR2RGB),
                     caption="Last captured frame", use_container_width=True)

        st.markdown("---")

        st.subheader("🗂 Known Faces")
        names = st.session_state.db.get_names()
        if names:
            for n in names:
                c1, c2 = st.columns([3, 1])
                c1.write(f"👤 {n}")
                if c2.button("✕", key=f"rm_{n}"):
                    st.session_state.db.remove_face(n)
                    st.rerun()
        else:
            st.caption("No faces registered yet.")

        st.markdown("---")
        st.subheader("📊 Database Records")
        records = st.session_state.db.get_all_records()
        if records:
            for r in records:
                st.write(f"ID: {r[0]} | Name: {r[1]}")
        else:
            st.caption("No records in SQLite table yet.")

    st.markdown("---")
    st.caption("Real-Time Face Recognition System")

st.title("🎥 Real-Time Face Recognition Surveillance System")
st.markdown("Register known people and identify them in real time.")
st.markdown("---")

if not st.session_state.streaming:
    st.info("Camera is stopped. Click **▶ Start Camera** in the sidebar to begin.")
    c1, c2, c3 = st.columns(3)
    c1.metric("Status", "Offline")
    c2.metric("FPS", "—")
    c3.metric("Known Faces", len(st.session_state.db.get_names()))
else:
    cam: CameraStream = st.session_state.cam
    encoding_available = is_encoding_available()

    if not encoding_available:
        st.warning("face_recognition is not available in the active Python environment.")

    c1, c2, c3, c4, c5 = st.columns(5)
    fps_ph = c1.empty()
    res_ph = c2.empty()
    faces_ph = c3.empty()
    known_ph  = c4.empty()
    uptime_ph = c5.empty()

    st.markdown("##### 🏷 Recently Recognised")
    last_seen_ph = st.empty()

    video_ph = st.empty()

    frame_count = 0
    stream_start = time.time()

    while st.session_state.streaming:
        frame = cam.read()
        if frame is None:
            time.sleep(0.05)
            continue

        frame_count += 1
        face_count = 0
        known_count = 0

        if encoding_available:
            if st.session_state.capture_pending:
                snap = frame.copy()
                ok = st.session_state.db.add_face_from_frame(
                    st.session_state.capture_name, snap)
                st.session_state.last_snap = snap
                if ok:
                    log_event("face_registered_webcam", f"name={st.session_state.capture_name}")
                else:
                    log_event("face_register_webcam_failed", f"name={st.session_state.capture_name}")
                st.session_state.capture_pending = False
                st.session_state.capture_name = ""
                st.rerun()

            results = recognise_frame(
                frame,
                st.session_state.db,
                tolerance=st.session_state.tolerance,
                resize_scale=0.75,
            )
            frame = draw_recognition_results(frame, results, show_confidence=True)
            face_count = len(results)
            known_count = sum(r.is_known for r in results)
            st.session_state.stats.update(results)
            logging.info(f"Detected {face_count} faces")

            now_ts = time.time()
            seen_cache: dict[str, float] = st.session_state.last_logged_seen
            for r in results:
                if not r.is_known:
                    continue
                prev = seen_cache.get(r.name, 0.0)
                if now_ts - prev >= 10.0:
                    log_event("known_face_detected", f"name={r.name}, confidence={r.confidence:.3f}")
                    seen_cache[r.name] = now_ts
            if face_count > 0 and known_count == 0 and frame_count % 60 == 0:
                log_event("unknown_face_detected", f"count={face_count}")

        w, h = cam.get_resolution()
        fps = cam.get_fps()
        cv2.putText(frame,
                    f"Faces: {face_count}  |  FPS: {fps}  |  {w}x{h}  |  Frame: {frame_count}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2)

        video_ph.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB),
                       channels="RGB", use_container_width=True)

        if frame_count % 15 == 0:
            fps_ph.metric("FPS", fps)
            res_ph.metric("Resolution", f"{w} × {h}")
            faces_ph.metric("Faces", face_count)
            known_ph.metric("Recognised", known_count)
            uptime_ph.metric("Uptime", f"{int(time.time() - stream_start)}s")

            ls = st.session_state.stats.last_seen
            if ls:
                last_seen_ph.markdown(
                    "  |  ".join(f"**{n}** {t}" for n, t in ls.items()))
            else:
                last_seen_ph.caption("No known faces seen yet.")

        time.sleep(0.03)
