import logging
import pathlib
import tempfile
import time
from datetime import datetime
from statistics import mean

import cv2
import numpy as np
import streamlit as st

from camera_stream import CameraStream
from face_encoding import (
    KnownFaceDB,
    encode_face_from_image,
    is_encoding_available,
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


def push_recent_alert(message: str) -> None:
    alerts: list[str] = st.session_state.week9_recent_alerts
    alerts.insert(0, message)
    st.session_state.week9_recent_alerts = alerts[:10]


def push_detection_history(face_count: int, known_count: int, fps: float, processing_ms: float) -> None:
    history: list[dict[str, object]] = st.session_state.week10_history
    history.append(
        {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "faces": int(face_count),
            "known": int(known_count),
            "unknown": int(max(0, face_count - known_count)),
            "fps": float(fps),
            "processing_ms": float(round(processing_ms, 1)),
        }
    )
    limit = int(st.session_state.week10_history_limit)
    if len(history) > limit:
        del history[:-limit]


def read_recent_event_logs(limit: int = 100, event_filter: str = "All") -> list[dict[str, str]]:
    if not EVIDENCE_LOG_PATH.exists():
        return []

    lines = EVIDENCE_LOG_PATH.read_text(encoding="utf-8").splitlines()
    out: list[dict[str, str]] = []

    for line in reversed(lines):
        if not line.strip():
            continue

        event = "unknown_event"
        details = ""
        timestamp = ""

        if line.startswith("[") and "]" in line:
            close_idx = line.find("]")
            timestamp = line[1:close_idx]
            payload = line[close_idx + 1 :].strip()
        else:
            payload = line

        if "|" in payload:
            left, right = payload.split("|", 1)
            event = left.strip()
            details = right.strip()
        else:
            event = payload.strip()

        if event_filter != "All" and event != event_filter:
            continue

        out.append({"time": timestamp, "event": event, "details": details})
        if len(out) >= limit:
            break

    return out


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
    "week8_max_faces_to_match": 5,
    "week9_known_alert_cooldown": 10.0,
    "week9_unknown_alert_cooldown": 12.0,
    "week9_enable_toast_alerts": True,
    "week9_last_alert_known": {},
    "week9_last_alert_unknown": 0.0,
    "week9_recent_alerts": [],
    "week10_history": [],
    "week10_history_limit": 400,
    "week11_adaptive_performance": True,
    "week11_model": "hog",
    "week11_last_processing_ms": 0.0,
    "week11_processed_frames": 0,
    "week11_skipped_frames": 0,
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
        "Confidence threshold",
        min_value=0.50,
        max_value=0.80,
        value=float(st.session_state.week7_confidence_threshold),
        step=0.01,
        key="week7_conf_threshold",
        help="Higher value reduces wrong matches but may increase Unknown labels.",
    )

    st.session_state.week7_process_every_n = st.selectbox(
        "Frame skip",
        options=[1, 2, 3],
        index=[1, 2, 3].index(int(st.session_state.week7_process_every_n)),
        key="week7_frame_skip",
        help="Process every Nth frame for faster live recognition.",
    )

    st.session_state.week7_resize_scale = st.selectbox(
        "Resize scale",
        options=[0.4, 0.5, 0.6, 0.75],
        index=[0.4, 0.5, 0.6, 0.75].index(float(st.session_state.week7_resize_scale)),
        key="week7_resize_scale_select",
        help="Smaller scale improves speed; larger scale improves detail.",
    )

    st.session_state.week11_model = st.selectbox(
        "Detection model",
        options=["hog", "cnn"],
        index=["hog", "cnn"].index(str(st.session_state.week11_model)),
        key="week11_model_select",
        help="Use HOG for CPU speed, CNN for higher accuracy (requires stronger hardware).",
    )

    st.session_state.week8_max_faces_to_match = st.slider(
        "Max faces to match per frame",
        min_value=1,
        max_value=12,
        value=int(st.session_state.week8_max_faces_to_match),
        step=1,
        key="week8_max_faces",
        help="For crowds, limit encoding/matching load to keep video smooth.",
    )

    st.session_state.week11_adaptive_performance = st.checkbox(
        "Adaptive performance",
        value=bool(st.session_state.week11_adaptive_performance),
        key="week11_adaptive_toggle",
        help="Automatically increases frame skipping when FPS drops.",
    )

    st.markdown("---")
    st.subheader("Alerts")

    st.session_state.week9_enable_toast_alerts = st.checkbox(
        "Enable live alerts",
        value=bool(st.session_state.week9_enable_toast_alerts),
        key="week9_enable_alerts",
    )

    st.session_state.week9_known_alert_cooldown = st.slider(
        "Known alert cooldown (seconds)",
        min_value=3.0,
        max_value=30.0,
        value=float(st.session_state.week9_known_alert_cooldown),
        step=1.0,
        key="week9_known_cooldown",
    )

    st.session_state.week9_unknown_alert_cooldown = st.slider(
        "Unknown alert cooldown (seconds)",
        min_value=3.0,
        max_value=30.0,
        value=float(st.session_state.week9_unknown_alert_cooldown),
        step=1.0,
        key="week9_unknown_cooldown",
    )

    st.markdown("---")
    st.subheader("Logs")
    log_limit = st.slider("Recent log rows", 20, 300, 80, 10, key="week10_log_rows")
    log_filter = st.selectbox(
        "Log event filter",
        options=[
            "All",
            "known_face_detected",
            "unknown_face_detected",
            "alert_known_face",
            "alert_unknown_face",
            "camera_started",
            "camera_stopped",
        ],
        index=0,
        key="week10_log_filter",
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
        st.subheader("Image upload module")
        uploaded_w6 = st.file_uploader(
            "Upload face image",
            type=["jpg", "jpeg", "png"],
            key="upload_face_photo_week6",
        )
        name_w6 = st.text_input("Enter name", key="name_upload_week6")

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
st.markdown("Flow: camera/upload → multi-face recognition → alerts → logs → optimization")
st.markdown("---")

if not st.session_state.streaming:
    st.info("Camera is stopped. Click Start Camera in the sidebar.")
    c1, c2, c3 = st.columns(3)
    c1.metric("Status", "Offline")
    c2.metric("FPS", "-")
    c3.metric("Known Faces", len(st.session_state.db.get_names()))

    st.markdown("#### Dashboard")
    history = st.session_state.week10_history
    if history:
        c4, c5, c6, c7 = st.columns(4)
        c4.metric("Avg Faces", f"{mean(h['faces'] for h in history):.1f}")
        c5.metric("Avg Known", f"{mean(h['known'] for h in history):.1f}")
        c6.metric("Avg FPS", f"{mean(h['fps'] for h in history):.1f}")
        c7.metric("Avg Processing", f"{mean(h['processing_ms'] for h in history):.1f} ms")
        st.dataframe(list(reversed(history[-50:])), use_container_width=True, hide_index=True)
    else:
        st.caption("No detection history yet. Start camera to collect dashboard metrics.")

    st.markdown("#### Event logs")
    recent_logs = read_recent_event_logs(limit=int(log_limit), event_filter=str(log_filter))
    if recent_logs:
        st.dataframe(recent_logs, use_container_width=True, hide_index=True)
    else:
        st.caption("No matching log entries.")

    if st.button("Clear runtime event log", key="clear_runtime_log"):
        EVIDENCE_LOG_PATH.write_text("", encoding="utf-8")
        log_event("runtime_log_cleared")
        st.success("Runtime event log cleared.")
else:
    cam: CameraStream = st.session_state.cam
    encoding_available = is_encoding_available()

    if not encoding_available:
        st.warning("face_recognition is not available in the active Python environment.")

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    fps_ph = c1.empty()
    res_ph = c2.empty()
    faces_ph = c3.empty()
    known_ph = c4.empty()
    uptime_ph = c5.empty()
    latency_ph = c6.empty()

    st.markdown("#### Recently Recognized")
    last_seen_ph = st.empty()

    st.markdown("#### Alert feed")
    alerts_ph = st.empty()

    st.markdown("#### Live metrics")
    dashboard_ph = st.empty()

    video_ph = st.empty()

    frame_count = 0
    stream_start = time.time()

    st.caption(f"Loaded known faces: {len(st.session_state.db.get_names())}")

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
                else:
                    log_event("face_register_webcam_failed", f"name={st.session_state.capture_name}")
                st.session_state.capture_pending = False
                st.session_state.capture_name = ""
                st.rerun()

            base_skip = int(st.session_state.week7_process_every_n)
            dynamic_skip = base_skip
            if st.session_state.week11_adaptive_performance:
                live_fps = float(cam.get_fps())
                if live_fps < 8:
                    dynamic_skip = max(base_skip, 3)
                elif live_fps < 15:
                    dynamic_skip = max(base_skip, 2)

            should_process = frame_count % dynamic_skip == 0

            if should_process:
                started = time.perf_counter()
                results = recognise_frame(
                    frame,
                    st.session_state.db,
                    tolerance=st.session_state.tolerance,
                    resize_scale=float(st.session_state.week7_resize_scale),
                    model=str(st.session_state.week11_model),
                    max_faces_to_match=int(st.session_state.week8_max_faces_to_match),
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
                st.session_state.week11_processed_frames += 1

                processing_ms = (time.perf_counter() - started) * 1000.0
                st.session_state.week11_last_processing_ms = processing_ms

                now_ts = time.time()
                seen_cache: dict[str, float] = st.session_state.last_logged_seen
                known_alert_cache: dict[str, float] = st.session_state.week9_last_alert_known
                for r in filtered_results:
                    if not r.is_known:
                        continue
                    prev = seen_cache.get(r.name, 0.0)
                    if now_ts - prev >= 10.0:
                        log_event("known_face_detected", f"name={r.name}, confidence={r.confidence:.3f}")
                        seen_cache[r.name] = now_ts

                    alert_prev = known_alert_cache.get(r.name, 0.0)
                    if now_ts - alert_prev >= float(st.session_state.week9_known_alert_cooldown):
                        alert_msg = f"Known face: {r.name} ({int(r.confidence * 100)}%)"
                        push_recent_alert(alert_msg)
                        log_event("alert_known_face", f"name={r.name}, confidence={r.confidence:.3f}")
                        if st.session_state.week9_enable_toast_alerts:
                            st.toast(alert_msg)
                        known_alert_cache[r.name] = now_ts

                unknown_count = sum(not r.is_known for r in filtered_results)
                if unknown_count > 0:
                    log_event("unknown_face_detected", f"count={unknown_count}")

                    prev_unknown_alert = float(st.session_state.week9_last_alert_unknown)
                    if now_ts - prev_unknown_alert >= float(st.session_state.week9_unknown_alert_cooldown):
                        alert_msg = f"Unknown face(s) detected: {unknown_count}"
                        push_recent_alert(alert_msg)
                        log_event("alert_unknown_face", f"count={unknown_count}")
                        if st.session_state.week9_enable_toast_alerts:
                            st.toast(alert_msg)
                        st.session_state.week9_last_alert_unknown = now_ts

                w, h = cam.get_resolution()
                fps = cam.get_fps()
                push_detection_history(
                    face_count=len(filtered_results),
                    known_count=sum(r.is_known for r in filtered_results),
                    fps=fps,
                    processing_ms=processing_ms,
                )
            else:
                st.session_state.week11_skipped_frames += 1

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
            latency_ph.metric("Processing", f"{st.session_state.week11_last_processing_ms:.1f} ms")

            ls = st.session_state.stats.last_seen
            if ls:
                last_seen_ph.markdown(" | ".join(f"**{n}** {t}" for n, t in ls.items()))
            else:
                last_seen_ph.caption("No known faces seen yet.")

            recent_alerts = st.session_state.week9_recent_alerts
            if recent_alerts:
                alerts_ph.markdown("\n".join(f"- {msg}" for msg in recent_alerts))
            else:
                alerts_ph.caption("No alerts yet.")

            history = st.session_state.week10_history
            if history:
                avg_faces = mean(item["faces"] for item in history)
                avg_fps = mean(item["fps"] for item in history)
                avg_ms = mean(item["processing_ms"] for item in history)
                processed = int(st.session_state.week11_processed_frames)
                skipped = int(st.session_state.week11_skipped_frames)
                skip_ratio = (skipped / (processed + skipped)) * 100 if (processed + skipped) > 0 else 0.0
                dashboard_ph.markdown(
                    f"Avg faces: **{avg_faces:.1f}** | Avg FPS: **{avg_fps:.1f}** | "
                    f"Avg processing: **{avg_ms:.1f} ms** | Skipped frames: **{skip_ratio:.1f}%**"
                )
            else:
                dashboard_ph.caption("Dashboard history will appear after first processed frames.")

        time.sleep(0.03)
