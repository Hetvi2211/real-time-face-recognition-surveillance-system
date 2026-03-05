"""
app.py — Week 2 | Member B
----------------------------
Streamlit UI that streams live webcam video inside the browser.

Run:
    streamlit run app.py

Features:
- Sidebar controls (camera index, resolution)
- Start / Stop camera button
- Live video feed rendered with st.image()
- Real-time FPS + resolution stats
- Status / error messages
"""

import time
import cv2
import streamlit as st

from camera_stream import CameraStream

# ──────────────────────────────────────────────────────────────────────────────
# Page config  (must be first Streamlit call)
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Face Recognition Surveillance",
    page_icon="🎥",
    layout="wide",
)

# ──────────────────────────────────────────────────────────────────────────────
# Session-state helpers
# ──────────────────────────────────────────────────────────────────────────────
if "cam" not in st.session_state:
    st.session_state.cam = None          # CameraStream instance
if "streaming" not in st.session_state:
    st.session_state.streaming = False   # True when camera is running


def start_camera(src: int, width: int, height: int) -> None:
    """Create and start a CameraStream; store it in session state."""
    try:
        cam = CameraStream(src=src, width=width, height=height).start()
        st.session_state.cam       = cam
        st.session_state.streaming = True
    except RuntimeError as exc:
        st.error(f"Camera error: {exc}")


def stop_camera() -> None:
    """Stop the running camera and clean up session state."""
    if st.session_state.cam is not None:
        st.session_state.cam.stop()
        st.session_state.cam       = None
        st.session_state.streaming = False


# ──────────────────────────────────────────────────────────────────────────────
# Sidebar — controls
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image(
        "https://img.icons8.com/emoji/96/video-camera-emoji.png",
        width=80,
    )
    st.title("Controls")
    st.markdown("---")

    cam_index = st.selectbox(
        "Camera Index",
        options=[0, 1, 2],
        index=0,
        help="0 = built-in webcam, 1/2 = external cameras",
    )

    resolution = st.selectbox(
        "Resolution",
        options=["640 × 480", "1280 × 720", "1920 × 1080"],
        index=0,
    )
    res_w, res_h = map(int, resolution.replace(" ", "").split("×"))

    st.markdown("---")

    # Start / Stop button
    if not st.session_state.streaming:
        if st.button("▶  Start Camera", use_container_width=True, type="primary"):
            start_camera(cam_index, res_w, res_h)
            st.rerun()
    else:
        if st.button("⏹  Stop Camera", use_container_width=True, type="secondary"):
            stop_camera()
            st.rerun()

    st.markdown("---")
    st.caption("Week 2 — Camera Streaming Module")
    st.caption("Real-Time Face Recognition System")


# ──────────────────────────────────────────────────────────────────────────────
# Main area — header
# ──────────────────────────────────────────────────────────────────────────────
st.title("🎥 Real-Time Face Recognition Surveillance System")
st.markdown("**Week 2 Deliverable** — Live camera feed inside Streamlit")
st.markdown("---")

# ──────────────────────────────────────────────────────────────────────────────
# Main area — video feed
# ──────────────────────────────────────────────────────────────────────────────
if not st.session_state.streaming:
    # Placeholder when camera is off
    st.info("Camera is stopped. Click **▶ Start Camera** in the sidebar to begin streaming.")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Status", "Offline")
    with col2:
        st.metric("FPS", "—")
    with col3:
        st.metric("Resolution", "—")

else:
    cam: CameraStream = st.session_state.cam

    # Stats row
    col1, col2, col3 = st.columns(3)
    fps_placeholder = col1.empty()
    res_placeholder = col2.empty()
    status_placeholder = col3.empty()

    # Live video placeholder
    video_placeholder = st.empty()

    # ── Streaming loop ──────────────────────────────────────────────────────
    frame_count = 0
    stream_start = time.time()

    while st.session_state.streaming:
        frame = cam.read()

        if frame is None:
            st.warning("Waiting for first frame …")
            time.sleep(0.05)
            continue

        frame_count += 1

        # Overlay FPS + resolution on the frame
        w, h  = cam.get_resolution()
        fps   = cam.get_fps()
        label = f"FPS: {fps}  |  {w}x{h}  |  Frame: {frame_count}"
        cv2.putText(
            frame, label, (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2,
        )

        # Convert BGR → RGB for Streamlit
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Push frame to the UI
        video_placeholder.image(frame_rgb, channels="RGB", use_container_width=True)

        # Update stats every 15 frames
        if frame_count % 15 == 0:
            fps_placeholder.metric("FPS", fps)
            res_placeholder.metric("Resolution", f"{w} × {h}")
            elapsed = int(time.time() - stream_start)
            status_placeholder.metric("Uptime", f"{elapsed}s")

        # Small sleep to avoid pegging the CPU
        time.sleep(0.03)
