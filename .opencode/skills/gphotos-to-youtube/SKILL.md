---
name: gphotos-to-youtube
description: Archive Google Photos videos to YouTube (Private) using browser automation with resumable state.
---

# Overview

This skill automates year-by-year archival of Google Photos **videos only** to
YouTube (Private visibility), then deletes the originals (moves to Trash).

It uses browser automation (BrowserClaw MCP). No Google APIs are used.

All data is stored under a user-selected root folder.


# Preconditions

1. User is logged into Google Photos in a browser tab.
2. User is logged into YouTube Studio in a browser tab.
3. BrowserClaw MCP is available.
4. Same Google account is used for both services.

Authentication is NOT automated.


# Phase 0 – Root Folder Selection

Prompt user:

Enter root backup folder name (e.g., Ernest_Backups):

Validation rules:

- Must be relative path
- Must NOT start with '/'
- Must NOT contain '../'
- ASCII characters only
- Nested paths allowed (e.g., Archives/Ernest_Backups)

Resolved base directory:

./<root>/gphotos/

If missing:
Ask whether to create it.

State file path:

./<root>/gphotos/archive_state.json


# Phase 1 – Resume Detection

If archive_state.json exists:

Offer:

1. Resume unfinished items
2. Restart current year (reset items)
3. Abort


# Phase 2 – Year Selection

Prompt:

Which year to process?

Navigate to that year in Google Photos.
Apply filter: Videos only.


# Phase 3 – Queue Mode Selection

Prompt:

Queue mode:
1. Manual selection
2. Auto-queue entire year

If Auto:
- Scroll full year
- Collect all video entries
- Build queue

If Manual:
- Scroll full year
- Enumerate videos
- Present numbered list
- Allow selection via numbers, ranges, comma-separated
- Build queue from selection

Persist state immediately after queue creation.


# Directory Structure

Example for root "Ernest_Backups":

./Ernest_Backups/
  gphotos/
    archive_state.json
    videos/
      2021/
      2022/


# State Model

archive_state.json:

{
  "root_folder": "Ernest_Backups",
  "year": 2021,
  "base_directory": "./Ernest_Backups/gphotos/videos/2021",
  "queue_mode": "manual",
  "created_at": "ISO_TIMESTAMP",
  "items": [
    {
      "id": "unique_id",
      "title": "original_title",
      "status": "queued",
      "local_path": null,
      "youtube_url": null,
      "attempts": 0,
      "last_error": null
    }
  ]
}


# Status Lifecycle

queued
downloading
downloaded
uploading
uploaded
deleting
completed
error

State must be saved after every status transition.


# Sequential Processing Engine

Strict single-item processing:

For each item not completed:

1. Download
   - Open video
   - Trigger download
   - Save to ./<root>/gphotos/videos/<year>/
   - Detect completion (file exists + stable size)
   - Update status → downloaded

2. Upload
   - Navigate to YouTube Studio upload
   - Upload file
   - Title = original title
   - Description = "Archived from Google Photos (<year>)"
   - Visibility = Private
   - Not made for kids
   - Wait for upload completion indicator
   - Capture video URL
   - Update status → uploaded

3. Delete
   - Return to Google Photos
   - Delete video (move to Trash)
   - Confirm removal
   - Update status → completed


# Resume Logic

If restarting:

downloading:
- If file exists → treat as downloaded
- Else retry

uploading:
- If youtube_url exists → treat as uploaded
- Else retry

uploaded:
- Skip upload → continue deletion

deleting:
- Retry deletion

error:
- Prompt user: Retry / Skip / Abort


# Progress Reporting

After each item, print:

Year: <year>
Mode: <manual|auto>
Root: <root>

[current/total] <title>
  ✓ Downloaded
  ✓ Uploaded (Private)
  ✓ Deleted

Progress Summary:
Completed: X
Remaining: Y
Errors: Z


# Safety Rules

- Only operate on videos
- Deletion moves to Trash only
- No permanent delete
- No parallel processing
- Max 2 retries per step before marking error


# Non-Features

- No size sorting
- No API usage
- No checksum validation
- No dedup detection
- No permanent deletion


# Failure Handling

On UI timeout or unexpected navigation:

- Retry step (max 2 times)
- If still failing → status = error
- Prompt user for action


# Notes

This skill assumes moderate UI fragility is acceptable.
Sequential execution is intentional for safety and deterministic resume.
