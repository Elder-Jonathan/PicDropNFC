import json
import os
import pathlib
import time

import requests

TOKEN_URL = "https://api.dropboxapi.com/oauth2/token"
LIST_FOLDER_URL = "https://api.dropboxapi.com/2/files/list_folder"
LIST_FOLDER_CONTINUE_URL = "https://api.dropboxapi.com/2/files/list_folder/continue"
DOWNLOAD_URL = "https://content.dropboxapi.com/2/files/download"

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def must_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"Missing required env var: {name}")
    return value


def get_access_token(client_id: str, client_secret: str, refresh_token: str) -> str:
    resp = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def list_all_files(access_token: str, folder_path: str) -> list[dict]:
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    data = {"path": folder_path, "recursive": False, "include_non_downloadable_files": False}

    resp = requests.post(LIST_FOLDER_URL, headers=headers, json=data, timeout=30)
    resp.raise_for_status()
    out = resp.json()

    entries = out.get("entries", [])
    while out.get("has_more"):
        resp2 = requests.post(
            LIST_FOLDER_CONTINUE_URL,
            headers=headers,
            json={"cursor": out["cursor"]},
            timeout=30,
        )
        resp2.raise_for_status()
        out = resp2.json()
        entries.extend(out.get("entries", []))

    files = []
    for entry in entries:
        if entry.get(".tag") != "file":
            continue
        name = entry.get("name", "")
        ext = pathlib.Path(name).suffix.lower()
        if ext in IMAGE_EXTS:
            files.append(entry)
    return files


def download_file(access_token: str, dropbox_path: str, local_path: pathlib.Path) -> None:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Dropbox-API-Arg": json.dumps({"path": dropbox_path}),
    }
    resp = requests.post(DOWNLOAD_URL, headers=headers, timeout=120)
    resp.raise_for_status()
    local_path.parent.mkdir(parents=True, exist_ok=True)
    local_path.write_bytes(resp.content)


def load_manifest(gallery_json_path: pathlib.Path) -> dict:
    if gallery_json_path.exists():
        try:
            return json.loads(gallery_json_path.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def main() -> None:
    client_id = must_env("DROPBOX_CLIENT_ID")
    client_secret = must_env("DROPBOX_CLIENT_SECRET")
    refresh_token = must_env("DROPBOX_REFRESH_TOKEN")
    folder_path = must_env("DROPBOX_FOLDER_PATH")
    output_dir = pathlib.Path(must_env("OUTPUT_DIR"))
    gallery_json_path = pathlib.Path(must_env("GALLERY_JSON"))

    access_token = get_access_token(client_id, client_secret, refresh_token)

    current = load_manifest(gallery_json_path)
    known_hashes = current.get("hashes", {})

    files = list_all_files(access_token, folder_path)

    updated = False
    photos_rel = []

    for file_entry in files:
        name = file_entry["name"]
        content_hash = file_entry.get("content_hash")
        dropbox_path = file_entry["path_lower"]

        photos_rel.append(f"./assets/photos/{name}")

        if not content_hash or known_hashes.get(name) != content_hash:
            local_path = output_dir / name
            download_file(access_token, dropbox_path, local_path)
            known_hashes[name] = content_hash or str(time.time())
            updated = True

    existing_names = {entry["name"] for entry in files}
    removed = [name for name in list(known_hashes.keys()) if name not in existing_names]
    for name in removed:
        known_hashes.pop(name, None)
        local = output_dir / name
        if local.exists():
            local.unlink()
            updated = True

    payload = {
        "updatedAt": int(time.time()),
        "count": len(photos_rel),
        "photos": sorted(photos_rel),
        "hashes": known_hashes,
    }
    gallery_json_path.parent.mkdir(parents=True, exist_ok=True)
    gallery_json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"Synced {len(photos_rel)} photos from Dropbox folder '{folder_path}'. Updated={updated}")


if __name__ == "__main__":
    main()
