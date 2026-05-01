import logging
import pathlib
import tempfile
import time
from datetime import datetime

import cv2
import numpy as np
import streamlit as st

from camera_stream import CameraStream
from face_encoding import (
    KnownFaceDB,
    encode_face_from_image,
    is_encoding_available,
    load_known_faces,
    save_encoding_to_db,
)
from face_matching import MatchResult, RecognitionStats, draw_recognition_results, recognise_frame


logging.basicConfig(
    filename="app_events.log",
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
)

EVIDENCE_LOG_PATH = pathlib.Path("evidence/runtime_logs/app_events.log")


def log_event(event: str, details: str = "") -> None:
    """Append timestamped runtime events for evidence and debugging."""
    EVIDENCE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {event}"
    if details:
        line += f" | {details}"
    with EVIDENCE_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


st.set_page_config(
    page_title="Face Recognition Surveillance",
    page_icon="CAM",
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
    "last_results": [],
    "week7_process_every_n": 2,
    "week7_resize_scale": 0.5,
    "week7_confidence_threshold": 0.60,
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
    st.title("Controls")
    st.markdown("---")

    st.subheader("Camera")
    cam_index = st.selectbox("Camera Index", options=[0, 1, 2], index=0, key="camera_index")
    resolution = st.selectbox(
        "Resolution",
        options=["640 x 480", "1280 x 720", "1920 x 1080"],
        index=0,
        key="camera_resolution",
    )
    res_w, res_h = map(int, resolution.replace(" ", "").split("x"))

    if not st.session_state.streaming:
        if st.button("Start Camera", use_container_width=True, type="primary", key="start_camera_btn"):
            start_camera(cam_index, res_w, res_h)
            st.rerun()
    else:
        if st.button("Stop Camera", use_container_width=True, type="secondary", key="stop_camera_btn"):
            stop_camera()
            st.rerun()

    st.markdown("---")

    st.subheader("Recognition")
    st.session_state.tolerance = st.slider(
        "Match tolerance",
        min_value=0.35,
        max_value=0.65,
        value=float(st.session_state.tolerance),
        step=0.01,
        key="match_tolerance",
        help="Lower value is stricter. 0.50 is a practical default.",
    )

    st.session_state.week7_confidence_threshold = st.slider(
        "Week 7 confidence threshold",
        min_value=0.50,
        max_value=0.80,
        value=float(st.session_state.week7_confidence_threshold),
        step=0.01,
        key="week7_conf_threshold",
        help="Higher value reduces wrong matches but may increase Unknown labels.",
    )

    st.session_state.week7_process_every_n = st.selectbox(
        "Week 7 frame skip",
        options=[1, 2, 3],
        index=[1, 2, 3].index(int(st.session_state.week7_process_every_n)),
        key="week7_frame_skip",
        help="Process every Nth frame for faster live recognition.",
    )

    st.session_state.week7_resize_scale = st.selectbox(
        "Week 7 resize scale",
        options=[0.4, 0.5, 0.6, 0.75],
        index=[0.4, 0.5, 0.6, 0.75].index(float(st.session_state.week7_resize_scale)),
        key="week7_resize_scale_select",
        help="Smaller scale improves speed; larger scale improves detail.",
    )

    st.markdown("---")

    if is_encoding_available():
        st.subheader("Register Face")
        uploaded = st.file_uploader(
            "Upload photo",
            type=["jpg", "jpeg", "png"],
            key="upload_face_photo",
        )
        name_upload = st.text_input("Name (upload)", placeholder="e.g. Alice", key="name_upload")
        if st.button("Add from photo", use_container_width=True, key="add_photo_btn"):
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
                st.success(f"Added '{name_upload.strip()}'") if ok else st.error("No face found in photo.")

        st.markdown("---")
        st.subheader("Week 6: Image Upload Module")
        uploaded_w6 = st.file_uploader(
            "Upload Face Image (Week 6)",
            type=["jpg", "jpeg", "png"],
            key="upload_face_photo_week6",
        )
        name_w6 = st.text_input("Enter Name (Week 6)", key="name_upload_week6")

        if uploaded_w6 is not None:
            file_bytes = np.asarray(bytearray(uploaded_w6.read()), dtype=np.uint8)
            uploaded_w6.seek(0)
            image_bgr = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            if image_bgr is not None:
                st.image(cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB), caption="Uploaded Image", use_container_width=True)

        if st.button("Register Uploaded Person", use_container_width=True, key="register_uploaded_week6"):
            if uploaded_w6 is None:
                st.warning("Upload an image first.")
            elif not name_w6.strip():
                st.warning("Enter a name first.")
            else:
                file_bytes = np.asarray(bytearray(uploaded_w6.read()), dtype=np.uint8)
                uploaded_w6.seek(0)
                image_bgr = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
                if image_bgr is None:
                    st.error("Invalid image file. Please upload a clear JPG/PNG.")
                else:
                    encoding = encode_face_from_image(image_bgr)
                    if encoding is None:
                        st.warning("Ensure image quality is good and only one clear face is visible.")
                        st.write("- Only ONE face in image")
                        st.write("- Face is clear and well-lit")
                        st.write("- Image is not blurry")
                        log_event("face_register_upload_failed", f"name={name_w6.strip()}")
                    else:
                        ok = save_encoding_to_db(name_w6.strip(), encoding, st.session_state.db.db_path)
                        if ok:
                            st.session_state.db.reload()
                            log_event("face_registered_upload", f"name={name_w6.strip()}")
                            st.success(f"{name_w6.strip()} registered successfully from uploaded image.")
                        else:
                            st.error("Failed to store uploaded face in database.")

        st.markdown("---")

        name_live = st.text_input("Name (webcam)", placeholder="e.g. Bob", key="name_webcam")
        if st.button(
            "Capture from webcam",
            use_container_width=True,
            disabled=not st.session_state.streaming,
            key="capture_webcam_btn",
        ):
            if not name_live.strip():
                st.warning("Enter a name first.")
            else:
                st.session_state.capture_pending = True
                st.session_state.capture_name = name_live.strip()
                log_event("face_capture_requested", f"name={name_live.strip()}")

        if st.session_state.last_snap is not None:
            st.image(
                cv2.cvtColor(st.session_state.last_snap, cv2.COLOR_BGR2RGB),
                caption="Last captured frame",
                use_container_width=True,
            )

        st.markdown("---")

        st.subheader("Known Faces")
        names = st.session_state.db.get_names()
        if names:
            for n in names:
                c1, c2 = st.columns([3, 1])
                c1.write(f"{n}")
                if c2.button("Remove", key=f"rm_{n}"):
                    st.session_state.db.remove_face(n)
                    log_event("face_removed", f"name={n}")
                    st.rerun()
        else:
            st.caption("No faces registered yet.")

        st.markdown("---")
        st.subheader("Database Records")
        records = st.session_state.db.get_all_records()
        if records:
            for r in records:
                st.write(f"ID: {r[0]} | Name: {r[1]}")
        else:
            st.caption("No records in SQLite table yet.")

st.title("Real-Time Face Recognition Surveillance System")
st.markdown("Week 1-7 flow: camera/upload -> detection -> encoding -> live SQLite matching")
st.markdown("---")

if not st.session_state.streaming:
    st.info("Camera is stopped. Click Start Camera in the sidebar.")
    c1, c2, c3 = st.columns(3)
    c1.metric("Status", "Offline")
    c2.metric("FPS", "-")
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
    known_ph = c4.empty()
    uptime_ph = c5.empty()

    st.markdown("#### Recently Recognized")
    last_seen_ph = st.empty()

    video_ph = st.empty()

    frame_count = 0
    stream_start = time.time()

    known_names, known_encodings = load_known_faces(st.session_state.db)
    st.caption(f"Week 7 loaded known faces: {len(known_names)}")

    while st.session_state.streaming:
        frame = cam.read()
        if frame is None:
            time.sleep(0.05)
            continue

        frame_count += 1
        face_count = 0
        known_count = 0
        results_for_frame: list[MatchResult] = st.session_state.last_results

        if encoding_available:
            if st.session_state.capture_pending:
                snap = frame.copy()
                ok = st.session_state.db.add_face_from_frame(st.session_state.capture_name, snap)
                st.session_state.last_snap = snap
                if ok:
                    log_event("face_registered_webcam", f"name={st.session_state.capture_name}")
                    known_names, known_encodings = load_known_faces(st.session_state.db)
                else:
                    log_event("face_register_webcam_failed", f"name={st.session_state.capture_name}")
                st.session_state.capture_pending = False
                st.session_state.capture_name = ""
                st.rerun()

            should_process = frame_count % int(st.session_state.week7_process_every_n) == 0

            if should_process:
                results = recognise_frame(
                    frame,
                    st.session_state.db,
                    tolerance=st.session_state.tolerance,
                    resize_scale=float(st.session_state.week7_resize_scale),
                )

                filtered_results: list[MatchResult] = []
                for r in results:
                    if r.is_known and r.confidence < float(st.session_state.week7_confidence_threshold):
                        filtered_results.append(
                            MatchResult(name="Unknown", confidence=r.confidence, location=r.location)
                        )
                    else:
                        filtered_results.append(r)

                st.session_state.last_results = filtered_results
                results_for_frame = filtered_results
                st.session_state.stats.update(filtered_results)
                logging.info(f"Detected {len(filtered_results)} faces")

                now_ts = time.time()
                seen_cache: dict[str, float] = st.session_state.last_logged_seen
                for r in filtered_results:
                    if not r.is_known:
                        continue
                    prev = seen_cache.get(r.name, 0.0)
                    if now_ts - prev >= 10.0:
                        log_event("known_face_detected", f"name={r.name}, confidence={r.confidence:.3f}")
                        seen_cache[r.name] = now_ts

                unknown_count = sum(not r.is_known for r in filtered_results)
                if unknown_count > 0:
                    log_event("unknown_face_detected", f"count={unknown_count}")

            frame = draw_recognition_results(frame, results_for_frame, show_confidence=True)
            face_count = len(results_for_frame)
            known_count = sum(r.is_known for r in results_for_frame)

        w, h = cam.get_resolution()
        fps = cam.get_fps()
        cv2.putText(
            frame,
            f"Faces: {face_count} | FPS: {fps} | {w}x{h} | Frame: {frame_count}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (0, 255, 0),
            2,
        )

        video_ph.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), channels="RGB", use_container_width=True)

        if frame_count % 15 == 0:
            fps_ph.metric("FPS", fps)
            res_ph.metric("Resolution", f"{w} x {h}")
            faces_ph.metric("Faces", face_count)
            known_ph.metric("Recognized", known_count)
            uptime_ph.metric("Uptime", f"{int(time.time() - stream_start)}s")

            ls = st.session_state.stats.last_seen
            if ls:
                last_seen_ph.markdown(" | ".join(f"**{n}** {t}" for n, t in ls.items()))
            else:
                last_seen_ph.caption("No known faces seen yet.")

        time.sleep(0.03)
