# Week 7 Evidence

## Goal

Live matching integration with name + confidence on video, speed optimization, and wrong-match reduction.

## Pass Conditions

- Live faces are matched against SQLite encodings
- Name and confidence shown on frame
- Unknown faces labeled correctly
- Recognition speed optimized using frame skip + resize scale
- Log events written for known/unknown detections

## Required Screenshots

- `live_recognition_known.png`
- `live_recognition_unknown.png`

## Required Log Evidence

Runtime log should contain lines like:

- `known_face_detected | name=..., confidence=...`
- `unknown_face_detected | count=1`

## Week 7 Controls Implemented

- `Week 7 confidence threshold`
- `Week 7 frame skip`
- `Week 7 resize scale`
