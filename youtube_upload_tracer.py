import os
import sys
import pprint
import google.auth.transport.requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_FILE = "token.json"


def get_authenticated_service():
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing token...")
            creds.refresh(google.auth.transport.requests.Request())
        else:
            print("Opening browser for authentication...")
            flow = InstalledAppFlow.from_client_secrets_file(
                "client_secret.json", SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    print("Authentication successful.")
    return build("youtube", "v3", credentials=creds)


def upload_single_video(youtube, file_path):
    title = os.path.splitext(os.path.basename(file_path))[0]

    print(f"Preparing upload: {file_path}")
    print(f"Title: {title}")

    media = MediaFileUpload(
        file_path,
        chunksize=8 * 1024 * 1024,
        resumable=True
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": "Tracer test upload",
                "categoryId": "22",
            },
            "status": {
                "privacyStatus": "private"
            },
        },
        media_body=media,
    )

    response = None

    print("Starting upload...")

    while response is None:
        status, response = request.next_chunk()
        if status:
            percent = int(status.progress() * 100)
            print(f"Progress: {percent}%")

    print("\nUpload complete.")
    print("Video ID:", response["id"])
    print("Private URL:")
    print(f"https://www.youtube.com/watch?v={response['id']}")

    print("\nFull API response:")
    pprint.pprint(response)
    return response


def is_video_file(path):
    return path.lower().endswith((".mp4", ".mov", ".m4v", ".avi"))


def load_uploaded_log(log_path):
    if not os.path.exists(log_path):
        return set()
    with open(log_path, "r") as f:
        return set(line.strip() for line in f.readlines())


def append_uploaded_log(log_path, video_path, video_id):
    with open(log_path, "a") as f:
        f.write(f"{video_path}|{video_id}\n")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python youtube_upload_tracer.py <video_file_or_folder>")
        sys.exit(1)

    target_path = sys.argv[1]

    if not os.path.exists(target_path):
        print("Path does not exist.")
        sys.exit(1)

    youtube = get_authenticated_service()

    upload_log = "uploaded_videos.log"
    uploaded_entries = load_uploaded_log(upload_log)
    uploaded_paths = {entry.split("|")[0] for entry in uploaded_entries}

    if os.path.isfile(target_path):
        if target_path in uploaded_paths:
            print("Already uploaded. Skipping.")
            sys.exit(0)
        response = upload_single_video(youtube, target_path)
        if response and "id" in response:
            append_uploaded_log(upload_log, target_path, response["id"])

    elif os.path.isdir(target_path):
        for root, _, files in os.walk(target_path):
            for name in files:
                full_path = os.path.join(root, name)
                if not is_video_file(full_path):
                    continue
                if full_path in uploaded_paths:
                    print(f"Skipping already uploaded: {full_path}")
                    continue
                try:
                    response = upload_single_video(youtube, full_path)
                    if response and "id" in response:
                        append_uploaded_log(upload_log, full_path, response["id"])
                except Exception as e:
                    print(f"Error uploading {full_path}: {e}")
