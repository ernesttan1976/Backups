#!/usr/bin/env python3

"""
Google Photos → YouTube archival runner.

This is an orchestration + state-management layer intended to be
incrementally extended. Browser automation hooks are intentionally
abstracted into stub methods so they can be implemented or modified
as we iterate.
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path


# ----------------------------
# Utilities
# ----------------------------


def prompt(text):
    return input(text).strip()


def validate_root(root: str) -> str:
    if not root:
        raise ValueError("Root folder cannot be empty")
    if root.startswith("/"):
        raise ValueError("Root must be relative")
    if ".." in root:
        raise ValueError("Root cannot contain '..'")
    try:
        root.encode("ascii")
    except UnicodeEncodeError:
        raise ValueError("Root must be ASCII only")
    return root


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


# ----------------------------
# State Handling
# ----------------------------


class ArchiveState:
    def __init__(self, path: Path):
        self.path = path
        self.data = None

    def exists(self) -> bool:
        return self.path.exists()

    def load(self):
        with open(self.path, "r") as f:
            self.data = json.load(f)

    def save(self):
        tmp = self.path.with_suffix(".tmp")
        with open(tmp, "w") as f:
            json.dump(self.data, f, indent=2)
        tmp.replace(self.path)

    def create(self, root, year, queue_mode, items):
        self.data = {
            "root_folder": root,
            "year": year,
            "base_directory": str(self.base_dir(root, year)),
            "queue_mode": queue_mode,
            "created_at": datetime.utcnow().isoformat(),
            "items": items,
        }
        self.save()

    @staticmethod
    def base_dir(root, year):
        return Path(root) / "gphotos" / "videos" / str(year)


# ----------------------------
# Browser Automation Stubs
# ----------------------------


class BrowserAutomation:
    """
    Replace these stubs with real BrowserClaw integration.
    """

    def verify_sessions(self):
        print("[Stub] Verify Google Photos and YouTube sessions.")

    def collect_videos_for_year(self, year):
        print(f"[Stub] Collecting videos for year {year}...")
        return []  # return list of {id, title}

    def download_video(self, item, target_dir: Path):
        print(f"[Stub] Downloading {item['title']}...")
        time.sleep(1)
        fake_path = target_dir / f"{item['id']}.mp4"
        fake_path.touch()
        return str(fake_path)

    def upload_video(self, item, local_path):
        print(f"[Stub] Uploading {item['title']}...")
        time.sleep(1)
        return f"https://youtube.com/fake/{item['id']}"

    def delete_video(self, item):
        print(f"[Stub] Deleting {item['title']}...")
        time.sleep(1)


# ----------------------------
# Processing Engine
# ----------------------------


def process_queue(state: ArchiveState, browser: BrowserAutomation):
    items = state.data["items"]
    year = state.data["year"]
    root = state.data["root_folder"]

    base_dir = ArchiveState.base_dir(root, year)
    ensure_dir(base_dir)

    total = len(items)

    for idx, item in enumerate(items, start=1):
        if item["status"] == "completed":
            continue

        print(f"\n[{idx}/{total}] {item['title']}")

        try:
            if item["status"] in ("queued", "error"):
                item["status"] = "downloading"
                state.save()

                local_path = browser.download_video(item, base_dir)
                item["local_path"] = local_path
                item["status"] = "downloaded"
                state.save()

            if item["status"] == "downloaded":
                item["status"] = "uploading"
                state.save()

                yt_url = browser.upload_video(item, item["local_path"])
                item["youtube_url"] = yt_url
                item["status"] = "uploaded"
                state.save()

            if item["status"] == "uploaded":
                item["status"] = "deleting"
                state.save()

                browser.delete_video(item)
                item["status"] = "completed"
                state.save()

            print("  ✓ Completed")

        except Exception as e:
            item["status"] = "error"
            item["last_error"] = str(e)
            state.save()
            print(f"  ✗ Error: {e}")


# ----------------------------
# Main Flow
# ----------------------------


def main():
    try:
        root = validate_root(prompt("Enter root backup folder: "))
    except ValueError as e:
        print(f"Invalid root: {e}")
        sys.exit(1)

    # Resume/state file lives directly inside the user's root folder
    root_path = Path(root)
    ensure_dir(root_path)

    state_path = root_path / "archive_state.json"
    state = ArchiveState(state_path)

    browser = BrowserAutomation()
    browser.verify_sessions()

    if state.exists():
        print("Existing archive_state.json detected in root folder.")
        print("1. Resume unfinished items")
        print("2. Restart (delete state file)")
        print("3. Abort")

        choice = prompt("Select option (1/2/3): ")

        if choice == "1":
            state.load()
        elif choice == "2":
            state_path.unlink()
        else:
            print("Aborting.")
            sys.exit(0)

    if not state.exists():
        year = int(prompt("Which year to process? "))
        mode = prompt("Queue mode (manual/auto): ")

        items = browser.collect_videos_for_year(year)

        for item in items:
            item.update({
                "status": "queued",
                "local_path": None,
                "youtube_url": None,
                "attempts": 0,
                "last_error": None,
            })

        state.create(root, year, mode, items)

    process_queue(state, browser)


if __name__ == "__main__":
    main()
