"""
folder_index.py

Prints a clean index of the whole course: every day's number, its real
title (read from its own README, not retyped by hand somewhere else,
which would drift out of sync the moment a title changed), and how many
Python files it has. A map like this is what lets a newcomer find the
one folder covering a specific topic (say, caching, or security)
without having to open all 30 folders and read every README themselves.
"""

import os

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")


def find_day_folders():
    entries = []
    for name in sorted(os.listdir(PROJECT_ROOT)):
        full_path = os.path.join(PROJECT_ROOT, name)
        if os.path.isdir(full_path) and name.startswith("day-"):
            parts = name.split("-", 2)
            if len(parts) >= 2 and parts[1].isdigit():
                entries.append((int(parts[1]), name, full_path))
    return sorted(entries)


def read_title(folder_path):
    """Reads the first non-empty line of a folder's README.md, stripped of a leading '#', as that day's real title. Returns a fallback if no README exists."""
    readme_path = os.path.join(folder_path, "README.md")
    if not os.path.exists(readme_path):
        return "(no README.md found)"
    with open(readme_path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped:
                return stripped.lstrip("#").strip()
    return "(README.md is empty)"


def count_files(folder_path):
    python_file_count = 0
    notebook_count = 0
    for name in os.listdir(folder_path):
        if name.endswith(".py"):
            python_file_count += 1
        elif name.endswith(".ipynb"):
            notebook_count += 1
    return python_file_count, notebook_count


def build_index():
    rows = []
    for day_number, folder_name, folder_path in find_day_folders():
        title = read_title(folder_path)
        python_file_count, notebook_count = count_files(folder_path)
        rows.append({"day": day_number, "folder": folder_name, "title": title, "python_files": python_file_count, "notebooks": notebook_count})
    return rows


def render_markdown(rows):
    lines = ["# Course Index", ""]
    lines.append("| Day | Folder | Title | Python Files | Notebooks |")
    lines.append("|-----|--------|-------|---------------|-----------|")
    for row in rows:
        lines.append(f"| {row['day']} | {row['folder']} | {row['title']} | {row['python_files']} | {row['notebooks']} |")

    total_python_files = sum(row["python_files"] for row in rows)
    total_notebooks = sum(row["notebooks"] for row in rows)
    lines.append("")
    lines.append(f"Total: {len(rows)} days, {total_python_files} Python files, {total_notebooks} notebooks.")
    return "\n".join(lines) + "\n"


def main():
    print("=== Folder Index ===\n")

    rows = build_index()

    print(f"{'day':<6}{'folder':<32}{'title':<48}{'py':<5}{'nb':<4}")
    print("-" * 95)
    for row in rows:
        print(f"{row['day']:<6}{row['folder']:<32}{row['title'][:46]:<48}{row['python_files']:<5}{row['notebooks']:<4}")

    total_python_files = sum(row["python_files"] for row in rows)
    total_notebooks = sum(row["notebooks"] for row in rows)
    print(f"\nTotal: {len(rows)} days, {total_python_files} Python files, {total_notebooks} notebooks.")

    index_path = os.path.join(os.path.dirname(__file__), "INDEX.md")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(render_markdown(rows))
    print(f"\nWrote the same index to {index_path}")

    print(
        "\nWhy a map helps newcomers: a project with 30 folders and "
        "hundreds of files is genuinely hard to navigate from a cold "
        "start, a newcomer has no way to know that caching lives in Day "
        "14 or that security lives in Day 27 without either being told "
        "or reading every folder's README themselves. One table, built "
        "directly from the real README titles and real file counts on "
        "disk, answers 'where do I find X' in seconds, and stays "
        "accurate automatically since it is generated, not maintained "
        "by hand."
    )


if __name__ == "__main__":
    main()
