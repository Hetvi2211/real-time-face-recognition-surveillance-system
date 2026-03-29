# Week 6 Evidence

## Deliverable

Uploaded person stored from image upload module in Streamlit.

## Pass Conditions

- Image upload UI accepts JPG/JPEG/PNG
- Single-face encoding extracted successfully
- Encoding stored in SQLite (`known_faces.db`)
- Bad-quality / multi-face image shows warning and is not stored
- Runtime log contains `face_registered_upload | name=...`

## Required Artifacts

- `upload_success.png`
- `upload_error.png`
- `db_after_upload.png`
- `week6.log`

## Suggested Test Cases

1. Upload clear single-face image -> success
2. Upload blurry image -> warning/fail
3. Upload multi-face/group image -> warning/fail

## Verification Command

`python -c "import sqlite3; c=sqlite3.connect('known_faces.db'); cur=c.cursor(); print(cur.execute('select name,count(*) from known_faces group by name').fetchall()); c.close()"`
