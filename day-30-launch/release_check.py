"""
release_check.py

A release checklist that actually RUNS, instead of one a person ticks
by hand from memory. A checklist someone fills in manually only checks
whatever they happened to remember to look at, and it goes stale the
moment the project changes under it. A script re-checks the exact same
things, the exact same way, every single time it runs, which is what
makes "this release was verified" a fact instead of a guess.
"""

import os
import subprocess
import sys

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")
DAY_COUNT = 30
REQUIRED_FILES_PER_DAY = ["README.md", "BEST_PRACTICES.md"]
DAY_29_FOLDER = os.path.join(PROJECT_ROOT, "day-29-complete-system")

CHANGELOG_PATH = os.path.join(os.path.dirname(__file__), "CHANGELOG.md")
EXPECTED_WEEK_MENTIONS = ["Week 1", "Week 2", "Week 3", "Week 4"]


def check_all_day_folders_exist():
    missing = []
    for day_number in range(1, DAY_COUNT + 1):
        matches = [
            name for name in os.listdir(PROJECT_ROOT)
            if name.startswith(f"day-{day_number:02d}-")
        ]
        if not matches:
            missing.append(day_number)
    return (not missing, f"missing day folders: {missing}" if missing else f"all {DAY_COUNT} day folders present")


def check_required_files_present():
    missing_report = []
    for day_number in range(1, DAY_COUNT + 1):
        matches = [name for name in os.listdir(PROJECT_ROOT) if name.startswith(f"day-{day_number:02d}-")]
        if not matches:
            continue  # already reported by check_all_day_folders_exist
        folder_path = os.path.join(PROJECT_ROOT, matches[0])
        for required_file in REQUIRED_FILES_PER_DAY:
            if not os.path.exists(os.path.join(folder_path, required_file)):
                missing_report.append(f"{matches[0]}/{required_file}")
    return (not missing_report, f"missing: {missing_report}" if missing_report else "every day has README.md and BEST_PRACTICES.md")


def check_changelog_mentions_every_week():
    if not os.path.exists(CHANGELOG_PATH):
        return (False, "CHANGELOG.md does not exist")
    with open(CHANGELOG_PATH, "r", encoding="utf-8") as f:
        contents = f.read()
    missing_weeks = [week for week in EXPECTED_WEEK_MENTIONS if week not in contents]
    return (not missing_weeks, f"missing: {missing_weeks}" if missing_weeks else "CHANGELOG.md mentions every week")


def check_subprocess_exits_cleanly(script_name, cwd):
    """Runs a real script as a subprocess and checks its actual exit code, the only trustworthy way to know whether it still works, reading the source and assuming it works is not a check."""
    result = subprocess.run(
        [sys.executable, script_name],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=60,
    )
    passed = result.returncode == 0
    detail = f"exit code {result.returncode}" if passed else f"exit code {result.returncode}, stderr: {result.stderr[-300:]}"
    return (passed, detail)


def main():
    print("=== Release Check ===\n")

    checks = [
        ("All 30 day folders exist", check_all_day_folders_exist),
        ("Every day has README.md and BEST_PRACTICES.md", check_required_files_present),
        ("CHANGELOG.md mentions every week", check_changelog_mentions_every_week),
        ("Day 29 main.py exits cleanly", lambda: check_subprocess_exits_cleanly("main.py", DAY_29_FOLDER)),
        ("Day 29 tests.py exits cleanly", lambda: check_subprocess_exits_cleanly("tests.py", DAY_29_FOLDER)),
    ]

    results = []
    for name, check_fn in checks:
        passed, detail = check_fn()
        results.append((name, passed, detail))
        print(f"[{'PASS' if passed else 'FAIL'}] {name}")
        print(f"       {detail}")

    overall_passed = all(passed for _, passed, _ in results)
    print(f"\nOverall: {'PASS' if overall_passed else 'FAIL'}")

    print(
        "\nWhy a release needs a checklist that RUNS: a checklist a "
        "person ticks by hand only reflects whatever they remembered to "
        "actually look at, and nothing stops someone from checking a box "
        "without really verifying it, especially under the time pressure "
        "a release often happens under. A script has no shortcuts "
        "available: check_subprocess_exits_cleanly() above genuinely "
        "runs main.py and tests.py as real processes and reads their "
        "real exit codes, the same way a CI system would, which is the "
        "only way to know they still work right now, not just that they "
        "worked the last time someone remembered to check."
    )

    return 0 if overall_passed else 1


if __name__ == "__main__":
    sys.exit(main())
