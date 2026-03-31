"""
Week 11 Regression and Stability Checks

This script provides lightweight checks that do not require a live webcam.
Run:
    python test_week11_regression.py
"""

from __future__ import annotations

import ast
import py_compile
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
APP_PATH = ROOT / "app.py"
MATCHING_PATH = ROOT / "face_matching.py"


def check_python_syntax() -> list[str]:
    errors: list[str] = []
    for path in (APP_PATH, MATCHING_PATH):
        try:
            py_compile.compile(str(path), doraise=True)
        except Exception as exc:
            errors.append(f"Syntax check failed for {path.name}: {exc}")
    return errors


def check_recognition_signature() -> list[str]:
    errors: list[str] = []
    try:
        source = MATCHING_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except Exception as exc:
        return [f"Unable to parse face_matching.py: {exc}"]

    target = None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "recognise_frame":
            target = node
            break

    if target is None:
        return ["Function 'recognise_frame' not found in face_matching.py."]

    params = [arg.arg for arg in target.args.args]
    if "max_faces_to_match" not in params:
        errors.append("recognise_frame is missing parameter 'max_faces_to_match'.")
    if "model" not in params:
        errors.append("recognise_frame is missing parameter 'model'.")

    return errors


def check_week_feature_flags() -> list[str]:
    errors: list[str] = []
    source = APP_PATH.read_text(encoding="utf-8")

    required_tokens = [
        "week8_max_faces_to_match",
        "week9_known_alert_cooldown",
        "week9_unknown_alert_cooldown",
        "week10_history",
        "week11_adaptive_performance",
        "week11_last_processing_ms",
        "alert_known_face",
        "alert_unknown_face",
    ]

    for token in required_tokens:
        if token not in source:
            errors.append(f"Missing Week 8-11 token in app.py: {token}")

    # Ensure log reader helper exists for dashboard verification.
    if not re.search(r"def\s+read_recent_event_logs\s*\(", source):
        errors.append("Missing helper: read_recent_event_logs")

    return errors


def run_all_checks() -> int:
    checks = [
        ("Python syntax", check_python_syntax),
        ("Recognition API", check_recognition_signature),
        ("Week 8-11 feature flags", check_week_feature_flags),
    ]

    total_errors: list[str] = []

    print("Week 11 Regression Checks")
    print("=" * 28)

    for title, fn in checks:
        errors = fn()
        if errors:
            print(f"[FAIL] {title}")
            for e in errors:
                print(f"  - {e}")
            total_errors.extend(errors)
        else:
            print(f"[PASS] {title}")

    print("-" * 28)
    if total_errors:
        print(f"Result: FAIL ({len(total_errors)} issue(s))")
        return 1

    print("Result: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_all_checks())
