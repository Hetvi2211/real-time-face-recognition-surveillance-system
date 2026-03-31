# Final Verification Checklist

**Date**: ___________  
**Verified By**: ____________  
**Status**: ❌ NOT READY / 🟡 PARTIAL / ✅ READY

---

## Code Files (Syntax & Features)

- [ ] `app.py` — Main Streamlit app
  - [ ] Runs without errors (`streamlit run app.py`)
  - [ ] Camera controls present
  - [ ] Face registration works
  - [ ] Live recognition displays names
  - [ ] Week 8-11 controls in sidebar

- [ ] `face_matching.py` — Recognition logic
  - [ ] `recognise_frame()` has `max_faces_to_match` parameter
  - [ ] `recognise_frame()` has `model` parameter
  - [ ] Multi-face results returned correctly

- [ ] `face_encoding.py` — Encoding and database
  - [ ] SQLite schema created
  - [ ] Encodings stored as BLOB
  - [ ] Load/save functions work

- [ ] `camera_stream.py` — Camera module
  - [ ] Threaded capture working
  - [ ] FPS calculation correct
  - [ ] No crashes on webcam access

- [ ] `test_camera.py` — Camera test
  - [ ] Can be run to verify webcam
  - [ ] No blockers for debug

---

## Week-wise Deliverables

### Week 1-4: Foundation
- [ ] Webcam test passes (`python test_camera.py`)
- [ ] Camera streaming appears in Streamlit
- [ ] Face detection works
- [ ] Face encoding and basic matching work

### Week 5-7: Core System
- [ ] SQLite database exists and has records
- [ ] Image upload registers faces
- [ ] Live recognition shows names in video
- [ ] Confidence scores displayed

### Week 8: Multi-Face Handling
- [ ] Multiple faces detected simultaneously
- [ ] Each face labeled separately
- [ ] **Week 8 max faces slider** in sidebar: ✅ YES / ❌ NO
- [ ] Large faces prioritized in crowds

### Week 9: Alert System
- [ ] **Known face alert fires** when registered person appears
- [ ] **Unknown face alert fires** when stranger detected
- [ ] **Alert cooldown prevents spam** (same person doesn't alert every frame)
- [ ] **Toast alerts toggle** in sidebar: ✅ YES / ❌ NO
- [ ] **Alert feed shows recent alerts** in UI: ✅ YES / ❌ NO

### Week 10: Dashboard & Logs
- [ ] **Detection history tracked** (timestamp, faces, FPS, latency)
- [ ] **Dashboard metrics shown** (avg faces, avg FPS, avg processing ms)
- [ ] **Event log table visible** with event types
- [ ] **Log filter working** (can filter by known/unknown/camera events)
- [ ] **Clear log button present** and works

### Week 11: Optimization & Testing
- [ ] **Adaptive performance toggle** in sidebar: ✅ YES / ❌ NO
- [ ] **Processing latency metric** displayed: ✅ YES / ❌ NO
- [ ] **Frame skip ratio** in dashboard: ✅ YES / ❌ NO
- [ ] **Model selector** (HOG/CNN) in sidebar: ✅ YES / ❌ NO
- [ ] **Regression test passes** (`python test_week11_regression.py` → PASS)

---

## Documentation Files

- [ ] `PROJECT_COMPLETION_SUMMARY.md` — Overview of all deliverables
- [ ] `DEMO_AND_VIVA_GUIDE.md` — Demo walkthrough for viva
- [ ] `docs/acceptance_report_weeks8_11.md` — Viva checklist template
- [ ] `docs/presentation_weeks8_11.md` — Presentation slide outline
- [ ] `docs/problems_weeks1_4.md` — Problem handling reference
- [ ] `docs/acceptance_report_weeks1_4.md` — Previous weeks reference

---

## Runtime Evidence

- [ ] `evidence/runtime_logs/app_events.log` — Event log auto-created on first run
- [ ] Log contains events like: `camera_started`, `known_face_detected`, `alert_known_face`, etc.
- [ ] Each event has timestamp

---

## Performance Validation

Run under typical conditions (no heavy background apps):

- [ ] **FPS target achieved** (≥ 10 FPS at 640x480)
- [ ] **Processing latency** < 100ms per frame
- [ ] **No crashes** during 5 min continuous run
- [ ] **Alert cooldown working** (alerts don't repeat < cooldown window)
- [ ] **Multi-face labeling correct** with 3+ people in frame

---

## Demo Readiness

- [ ] Team understands all 4 modules (camera, detection, encoding, matching)
- [ ] Team can explain Week 8-11 improvements without notes
- [ ] Database has ≥ 2 test faces registered
- [ ] Test run completed successfully (no runtime errors)

---

## Final Sign-Off

**All boxes checked?** → ✅ READY FOR VIVA

**Missing items?** → 🟡 Review and fix before submission

**Major blockers?** → ❌ HALT and escalate

---

**Sign-off Date**: ___________  
**Member A**: ____________  
**Member B**: ____________
