#!/usr/bin/env python3
import argparse
import json
import os
import sys
from datetime import datetime


def validate_root(root: str) -> str:
    if not root.endswith("_Backups"):
        raise ValueError("Root folder must end with '_Backups'")

    try:
        root.encode("ascii")
    except UnicodeEncodeError:
        raise ValueError("Root folder must contain ASCII characters only")

    if not os.path.isabs(root) and "../" in root:
        raise ValueError("Relative root must not contain '../'")

    return root


def ensure_directories(root: str) -> str:
    base_dir = os.path.join(root, "gphotos")
    os.makedirs(base_dir, exist_ok=True)
    return base_dir


def load_state(state_path: str):
    if not os.path.exists(state_path):
        return None
    with open(state_path, "r") as f:
        return json.load(f)


def save_state(state_path: str, state: dict):
    tmp = state_path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, state_path)


def initialize_state(root: str, base_dir: str, year: int, mode: str) -> dict:
    videos_dir = os.path.join(base_dir, "videos", str(year))
    os.makedirs(videos_dir, exist_ok=True)

    return {
        "root_folder": root,
        "year": year,
        "base_directory": videos_dir,
        "queue_mode": mode,
        "created_at": datetime.utcnow().isoformat(),
        "items": [],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root", help="Root backup folder (must end with _Backups)")
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--mode", choices=["manual", "auto"], required=True)
    parser.add_argument("--restart", action="store_true")
    args = parser.parse_args()

    try:
        root = validate_root(args.root)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    base_dir = ensure_directories(root)
    state_path = os.path.join(base_dir, "archive_state.json")

    state = load_state(state_path)

    if state and not args.restart:
        print("Existing state detected. Resuming.")
    else:
        if state and args.restart:
            print("Restart flag provided. Reinitializing state.")
        state = initialize_state(root, base_dir, args.year, args.mode)
        save_state(state_path, state)
        print("State initialized.")

    print(f"Root: {root}")
    print(f"Year: {args.year}")
    print(f"Mode: {args.mode}")
    print(f"State file: {state_path}")

    # Browser automation phases are executed externally via BrowserClaw MCP.
    # This runner strictly owns filesystem and state management.


if __name__ == "__main__":
    main()
