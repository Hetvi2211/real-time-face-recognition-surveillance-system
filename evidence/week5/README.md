# Week 5 Evidence

## Deliverable

SQLite database creation with encoding storage format verification and CRUD proof.

## Required Artifacts

- `week5.log`: command outputs and conclusions
- `db_file_present.png`: screenshot showing `known_faces.db`
- `schema_query_output.png`: PRAGMA table info output
- `blob_type_output.png`: encoding storage type output (`<class 'bytes'>`)
- `streamlit_db_records.png`: Streamlit DB records panel
- `add_delete_proof.png`: before/after add-delete proof output

## Verification Commands

1. Schema check

`python -c "import sqlite3; c=sqlite3.connect('known_faces.db'); cur=c.cursor(); print(cur.execute('PRAGMA table_info(known_faces)').fetchall()); c.close()"`

2. Encoding storage format check (BLOB bytes)

`python -c "import sqlite3; c=sqlite3.connect('known_faces.db'); cur=c.cursor(); data=cur.execute('select encoding from known_faces limit 1').fetchone()[0]; print(type(data)); c.close()"`

3. CRUD list check

`python -c "import sqlite3; c=sqlite3.connect('known_faces.db'); cur=c.cursor(); print(cur.execute('select name, count(*) from known_faces group by name').fetchall()); c.close()"`

## Pass Criteria

- SQLite schema present and queryable
- Encodings stored as BLOB (`bytes`)
- Add and delete operations reflect in query output
- Streamlit DB records panel displays backend rows
