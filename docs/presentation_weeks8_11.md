# Presentation Outline (Weeks 8-11)

## Slide 1 - Title
- Real-Time Face Recognition Surveillance System
- Team members and roles
- Scope: Weeks 8 to 11 completion

## Slide 2 - Week 8 Objective: Multiple Face Handling
- Problem: Recognition in crowd scenes
- Solution:
  - Match multiple faces per frame
  - Prioritize largest faces when crowd is large
  - Cap max faces per frame for stable FPS
- Demo shot: 2+ faces with separate labels

## Slide 3 - Week 9 Objective: Alert System
- Problem: Alert spamming every frame
- Solution:
  - Known face cooldown
  - Unknown face cooldown
  - Optional real-time toast alerts
  - Alert feed in app UI
- Demo shot: One alert generated, then cooldown prevents repeats

## Slide 4 - Week 10 Objective: Dashboard and Logs
- Added runtime dashboard metrics:
  - Avg faces
  - Avg known matches
  - Avg FPS
  - Avg processing time
- Added log table with event filtering
- Added one-click runtime log clear

## Slide 5 - Week 11 Objective: Optimization and Testing
- Adaptive performance mode
  - Increases frame skipping when FPS drops
- Model selection (HOG/CNN)
- Processing latency metric and skipped frame ratio
- Added regression check script: `test_week11_regression.py`

## Slide 6 - Architecture Update
- Camera stream -> Face detection/encoding/matching
- Multi-face control layer
- Alert cooldown layer
- Logging + dashboard layer
- Optimization feedback loop

## Slide 7 - Results and Evidence
- Stable live recognition with crowd handling
- Controlled alert behavior
- Persistent runtime logs for audit
- Week 11 checks: script-based validation + syntax checks

## Slide 8 - Challenges and Fixes
- Challenge: speed drop in crowd scenes
- Fix: max-face cap + adaptive frame skipping
- Challenge: repeated noisy alerts
- Fix: per-event cooldown windows
- Challenge: difficult debugging during demo
- Fix: structured event logs and filters

## Slide 9 - Future Scope
- Automated unknown face snapshot capture
- Email/SMS notifications
- Multi-camera support
- Accuracy tuning with richer face dataset

## Slide 10 - Conclusion
- Weeks 8 to 11 deliverables completed
- System now includes detection, recognition, alerts, logs, and optimization
- Ready for final demo and viva
