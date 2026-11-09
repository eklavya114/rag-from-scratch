"""
run_all_days.py

A structure check for the whole course, not a demo runner. Checking
that every day's expected files actually exist is a different, much
cheaper question than running every day's demo, and it catches a real,
common mistake: a folder that got renamed, a file that never got
committed, a README that got deleted by accident. A project this large
needs a check like this precisely because nobody can realistically
remember, by hand, that all 29 day folders still have what they are
supposed to have.
"""

import os

EXPECTED_FILES_PER_DAY = ["README.md", "BEST_PRACTICES.md", "notebook.ipynb"]


def find_day_folders(base_dir):
    """Returns every folder matching the day-NN-topic naming pattern, sorted by day number."""
    entries = []
    for name in os.listdir(base_dir):
        full_path = os.path.join(base_dir, name)
        if os.path.isdir(full_path) and name.startswith("day-"):
            parts = name.split("-", 2)
            if len(parts) >= 2 and parts[1].isdigit():
                entries.append((int(parts[1]), name, full_path))
    return sorted(entries)


def check_day_folder(folder_path, expected_files=EXPECTED_FILES_PER_DAY):
    """Checks which expected files exist in a day folder, and separately checks that at least one runnable .py script (other than the expected markdown/notebook files) exists."""
    found = []
    missing = []
    for filename in expected_files:
        if os.path.exists(os.path.join(folder_path, filename)):
            found.append(filename)
        else:
            missing.append(filename)

    has_python_script = any(
        name.endswith(".py") for name in os.listdir(folder_path)
    )
    if not has_python_script:
        missing.append("at least one .py script")

    return found, missing


def main():
    print("=== Smoke Test: Course Structure ===\n")

    base_dir = os.path.join(os.path.dirname(__file__), "..")
    day_folders = find_day_folders(base_dir)

    print(f"Found {len(day_folders)} day folders.\n")

    print(f"{'day':<6}{'folder':<32}{'files found':<16}{'files missing':<30}")
    print("-" * 84)

    all_clean = True
    for day_number, folder_name, folder_path in day_folders:
        found, missing = check_day_folder(folder_path)
        if missing:
            all_clean = False
        found_str = f"{len(found)}/{len(EXPECTED_FILES_PER_DAY)}"
        missing_str = ", ".join(missing) if missing else "none"
        print(f"{day_number:<6}{folder_name:<32}{found_str:<16}{missing_str:<30}")

    print(f"\n{'All days have the expected structure.' if all_clean else 'Some days are missing expected files, see the table above.'}")

    print(
        "\nWhy a structure check matters, separate from actually running "
        "each day's demo: running all 29 days' full demos would take "
        "real time and pull in every dependency each day happens to "
        "need. Checking structure instead, does README.md exist, does "
        "BEST_PRACTICES.md exist, is there at least one runnable script, "
        "answers a narrower but still useful question (is this project "
        "actually intact) in a fraction of a second, which is exactly "
        "the kind of cheap, fast check worth running before every commit, "
        "not just occasionally."
    )


if __name__ == "__main__":
    main()
