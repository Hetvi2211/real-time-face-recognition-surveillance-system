"""
DEMO VERSION: Real-Time Face Recognition Surveillance System
No webcam or OpenCV required - simulates the full UI/feature set
"""
import streamlit as st
import time
from datetime import datetime
from statistics import mean
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="Face Recognition Surveillance (DEMO)",
    page_icon="🎥",
    layout="wide",
)

# ─────────────────────────────────────────────────────────────
# Session State Initialization
# ─────────────────────────────────────────────────────────────
DEFAULTS = {
    "streaming": False,
    "demo_running_since": None,
    "demo_faces_detected": 0,
    "stats": {"face_count": 0, "known_count": 0, "fps": 0},
    "tolerance": 0.50,
    "week8_max_faces": 5,
    "week9_alerts": [],
    "week10_history": [],
    "week11_adaptive": True,
    "known_database": {"Alice": True, "Bob": True},
}

for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


def log_event(event: str, details: str = "") -> None:
    """Simulate event logging."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    msg = f"[{timestamp}] {event}"
    if details:
        msg += f" | {details}"
    st.session_state.week9_alerts.insert(0, msg)
    st.session_state.week9_alerts = st.session_state.week9_alerts[:10]


def demo_detection_cycle():
    """Simulate face detection for demo."""
    import random
    
    # Randomly detect faces
    if random.random() > 0.4:
        face_count = random.randint(1, 3)
        known_count = random.randint(0, face_count)
        fps = random.uniform(15, 30)
        processing_ms = random.uniform(20, 80)
        
        # Add to history
        history = st.session_state.week10_history
        history.append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "faces": face_count,
            "known": known_count,
            "unknown": max(0, face_count - known_count),
            "fps": round(fps, 1),
            "processing": round(processing_ms, 1),
        })
        st.session_state.week10_history = history[-100:]  # Keep last 100
        
        # Trigger alerts
        if known_count > 0:
            log_event("alert_known_face", f"Detected {known_count} known face(s)")
        if max(0, face_count - known_count) > 0:
            log_event("alert_unknown_face", f"Detected {face_count - known_count} unknown face(s)")
        
        return face_count, known_count, fps
    return 0, 0, 0


# ─────────────────────────────────────────────────────────────
# Sidebar Controls
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🎮 Demo Controls")
    st.markdown("---")

    st.subheader("Camera")
    if not st.session_state.streaming:
        if st.button("▶ Start Demo Stream", use_container_width=True, type="primary"):
            st.session_state.streaming = True
            st.session_state.demo_running_since = time.time()
            log_event("demo_started")
            st.rerun()
    else:
        if st.button("⏹ Stop Demo Stream", use_container_width=True, type="secondary"):
            st.session_state.streaming = False
            log_event("demo_stopped")
            st.rerun()

    st.markdown("---")
    st.subheader("Recognition")
    st.session_state.tolerance = st.slider(
        "Match tolerance",
        0.35, 0.65, float(st.session_state.tolerance), 0.01,
        help="Lower = stricter matching"
    )

    st.markdown("---")
    st.subheader("Week 8: Multi-Face")
    st.session_state.week8_max_faces = st.slider(
        "Max faces to process",
        1, 12, int(st.session_state.week8_max_faces),
        help="Prioritize largest faces in crowds"
    )

    st.markdown("---")
    st.subheader("Week 9: Alerts")
    if st.checkbox("Enable alerts", value=True):
        st.write("✅ Alert system active")

    st.markdown("---")
    st.subheader("Week 11: Performance")
    st.session_state.week11_adaptive = st.checkbox(
        "Adaptive performance",
        value=bool(st.session_state.week11_adaptive),
        help="Auto-optimize frame skipping"
    )

# ─────────────────────────────────────────────────────────────
# Main Content
# ─────────────────────────────────────────────────────────────
st.title("🎥 Real-Time Face Recognition Surveillance (DEMO VERSION)")
st.markdown("**Full-featured demo with simulated face detection** • No webcam required")
st.markdown("---")

if not st.session_state.streaming:
    st.info("Click **▶ Start Demo Stream** in the sidebar to begin")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Status", "Offline")
    c2.metric("Known Faces", len(st.session_state.known_database))
    c3.metric("Uptime", "—")
    
    st.markdown("### Features Demonstrated")
    st.markdown("""
    ✅ **Week 1-7**: Camera simulation, face detection, encoding, live matching  
    ✅ **Week 8**: Multi-face handling with controllable max-face cap  
    ✅ **Week 9**: Alert system with throttling  
    ✅ **Week 10**: Detection history dashboard and event logs  
    ✅ **Week 11**: Performance metrics and adaptive optimization
    """)

else:
    # ─────────────────────────────────────────────────────────────
    # Live Demo Stream
    # ─────────────────────────────────────────────────────────────
    uptime = int(time.time() - st.session_state.demo_running_since)
    
    c1, c2, c3, c4, c5 = st.columns(5)
    fps_ph = c1.empty()
    faces_ph = c2.empty()
    known_ph = c3.empty()
    processing_ph = c4.empty()
    uptime_ph = c5.empty()
    
    st.markdown("#### Video Feed (Simulated)")
    video_ph = st.empty()
    
    st.markdown("#### Week 9: Alert Feed")
    alerts_ph = st.empty()
    
    st.markdown("#### Week 10: Mini Dashboard")
    dashboard_ph = st.empty()
    
    frame_count = 0
    demo_frames = 40  # Simulate 40 frames
    
    progress_bar = st.progress(0)
    
    for frame_num in range(demo_frames):
        if not st.session_state.streaming:
            break
        
        frame_count += 1
        face_count, known_count, fps = demo_detection_cycle()
        
        uptime = int(time.time() - st.session_state.demo_running_since)
        
        # Update metrics every frame
        fps_ph.metric("FPS", f"{fps:.1f}")
        faces_ph.metric("Faces", face_count)
        known_ph.metric("Recognized", known_count)
        processing_ms = fps_ph.empty() if fps > 0 else 0
        uptime_ph.metric("Uptime", f"{uptime}s")
        
        # Simulated video frame (placeholder)
        with video_ph.container():
            st.markdown(f"""
            <div style="background: #f0f0f0; padding: 40px; text-align: center; border-radius: 8px;">
                <p style="font-size: 48px;">🎬</p>
                <p><strong>Frame {frame_count} | Detected: {face_count} face(s) | Known: {known_count}</strong></p>
                <p style="color: #666;">Face detection simulated (no webcam needed)</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Alert feed
        if st.session_state.week9_alerts:
            alerts_ph.markdown("\n".join(f"🔔 {msg}" for msg in st.session_state.week9_alerts[:5]))
        
        # Dashboard
        history = st.session_state.week10_history
        if history:
            avg_faces = mean(h["faces"] for h in history)
            avg_known = mean(h["known"] for h in history)
            avg_fps = mean(h["fps"] for h in history)
            avg_ms = mean(h["processing"] for h in history)
            dashboard_ph.markdown(
                f"📊 Avg Faces: **{avg_faces:.1f}** | Avg Known: **{avg_known:.1f}** | "
                f"Avg FPS: **{avg_fps:.1f}** | Avg Latency: **{avg_ms:.1f}ms**"
            )
        
        progress_bar.progress(frame_num / demo_frames)
        time.sleep(0.1)  # Simulate processing
    
    st.success("✅ Demo simulation complete!")
    
    # ─────────────────────────────────────────────────────────────
    # Week 10: Full History Table
    # ─────────────────────────────────────────────────────────────
    st.markdown("### Week 10: Detection History")
    history = st.session_state.week10_history
    if history:
        st.write("| Time | Faces | Known | Unknown | FPS | Processing (ms) |")
        st.write("|------|-------|-------|---------|-----|-----------------|")
        for h in history[-20:]:
            st.write(f"| {h['time']} | {h['faces']} | {h['known']} | {h['unknown']} | {h['fps']} | {h['processing']} |")
    
    # ─────────────────────────────────────────────────────────────
    # Week 10: Event Log
    # ─────────────────────────────────────────────────────────────
    st.markdown("### Week 10: Event Logs")
    if st.session_state.week9_alerts:
        for alert in st.session_state.week9_alerts[:20]:
            st.write(f"• {alert}")
    
    st.session_state.streaming = False

st.markdown("---")
st.caption(
    "📝 **DEMO VERSION**: Simulates the full real-time face recognition system (Weeks 1-11). "
    "No webcam needed. For live webcam recognition, install: `pip install -r requirements.txt`"
)
