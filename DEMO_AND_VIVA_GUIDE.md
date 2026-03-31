# Quick Start Guide for Demo & Viva

## Before Demo

```bash
# 1. Verify environment
pip install -r requirements.txt

# 2. Run regression test (ensure no syntax errors)
python test_week11_regression.py
# Expected: Result: PASS

# 3. Start the app
streamlit run app.py
```

## During Demo (For Viva Committee)

### Part 1: Setup (2 min)
1. Click **"Start Camera"** in sidebar
2. Adjust resolution to **640 x 480** (fastest on laptop)
3. Wait for live stream

### Part 2: Register a Person (3 min)
1. Upload a photo under **"Week 6: Image Upload Module"**
2. Enter name (e.g., "Alice")
3. Click **"Register Uploaded Person"**
4. Check database shows the name in **"Known Faces"** list

### Part 3: Live Recognition (3 min)
1. Show your face to camera (if you uploaded)
2. Observe:
   - Name appears in green box
   - Confidence score shown
   - Recent recognized person in sidebar
3. Show unknown face → appears in red box

### Part 4: Multi-Face Crowd (2 min)
- If team has 2+ people: stand together in frame
- Show separate labels for each person (Week 8)
- Point out **Week 8 max faces slider** in sidebar

### Part 5: Alerts (2 min)
- Toggle **"Week 9 Enable live alerts"** ON
- Known person appears → toast alert pops up
- Wait 10 seconds, person appears again → no new alert (cooldown working)
- Point to **Week 9 Alert Feed** in app showing recent alerts

### Part 6: Dashboard & Logs (2 min)
- **Stop Camera**
- Scroll down to **Week 10 Dashboard** (shows averages)
- Show **Week 10 Event Logs** table
- Use **Log event filter** to search by type
- Explain how logs prove timestamps and events

### Part 7: Performance (1 min)
- **Start Camera**
- Point to **"Processing"** metric (latency in ms)
- Show **"Week 11 adaptive performance"** toggle
- Explain frame skip ratio in dashboard

## Key Points to Mention in Viva

### Weeks 1-4 (Foundation)
- "We built camera streaming in a threaded module for real-time performance."
- "Face detection uses OpenCV HOG, encoding uses dlib's 128D vectors."
- "Tolerance slider lets us tune match strictness from 0.35 to 0.65."

### Weeks 5-7 (Core System)
- "SQLite stores encodings as BLOB bytes for persistence."
- "Live matching compares detected faces against registered database."
- "Confidence scores guide whether to trust a match."

### Week 8 (Multi-Face)
- "In crowds, we prioritize largest faces to avoid processing lag."
- "Each detected face gets a separate bounding box with its own label."

### Week 9 (Alerts)
- "Cooldown prevents alert spam (e.g., same person triggers only once per 10 seconds)."
- "Alert events are logged for audit and evidence."

### Week 10 (Dashboard)
- "Real-time metrics dashboard tracks average FPS, faces detected, processing latency."
- "Event log viewer helps debug what happened during operation."

### Week 11 (Optimization)
- "Adaptive performance auto-increases frame skipping when FPS drops."
- "Regression test ensures all new features are present and correct."

## File Evidence for Viva

Show these files as evidence:

- `PROJECT_COMPLETION_SUMMARY.md` — completed deliverables
- `docs/acceptance_report_weeks8_11.md` — checklist filled out
- `test_week11_regression.py output` (screenshot: Result: PASS)
- `evidence/runtime_logs/app_events.log` — timestamped event proof
- App screenshots with alerts, logs, dashboard visible

## If Viva asks "What Problems Did You Face?"

**Week 8:** Processing lag in crowded scenes → Fixed by capping max faces and frame skipping

**Week 9:** Alerts firing every frame → Fixed by per-person cooldown windows

**Week 10:** Hard to debug events → Fixed by structured logging with timestamps and filters

**Week 11:** FPS inconsistency → Fixed by adaptive frame skipping based on live FPS

---

**Estimated Time**: 20-25 minutes for full demo + questions
