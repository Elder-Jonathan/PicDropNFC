import json
import os
import pathlib
import time
from typing import Dict, List

import requests

TOKEN_URL = "https://api.dropboxapi.com/oauth2/token"
LIST_FOLDER_URL = "https://api.dropboxapi.com/2/files/list_folder"
LIST_FOLDER_CONTINUE_URL = "https://api.dropboxapi.com/2/files/list_folder/continue"
DOWNLOAD_URL = "https://content.dropboxapi.com/2/files/download"

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def must_env(name: str) -> str:
    v = os.environ.get(name)
    if not v:
        raise SystemExit(f"Missing required env var: {name}")
    return v


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
    data = resp.json()
    if "access_token" not in data:
        raise SystemExit(f"Dropbox token response missing access_token: {data}")
    return data["access_token"]


def list_all_files(access_token: str, folder_path: str) -> List[dict]:
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    payload = {
        "path": folder_path,
        "recursive": False,
        "include_non_downloadable_files": False,
    }

    resp = requests.post(LIST_FOLDER_URL, headers=headers, json=payload, timeout=30)
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

    files: List[dict] = []
    for e in entries:
        if e.get(".tag") != "file":
            continue
        name = e.get("name", "")
        ext = pathlib.Path(name).suffix.lower()
        if ext in IMAGE_EXTS:
            files.append(e)
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


def read_json(path: pathlib.Path) -> Dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def main() -> None:
    client_id = must_env("DROPBOX_CLIENT_ID")
    client_secret = must_env("DROPBOX_CLIENT_SECRET")
    refresh_token = must_env("DROPBOX_REFRESH_TOKEN")

    folder_path = must_env("DROPBOX_FOLDER_PATH")
    output_dir = pathlib.Path(must_env("OUTPUT_DIR"))
    gallery_json_path = pathlib.Path(must_env("GALLERY_JSON"))

    access_token = get_access_token(client_id, client_secret, refresh_token)

    manifest = read_json(gallery_json_path)
    known_hashes = manifest.get("hashes", {})

    files = list_all_files(access_token, folder_path)

    # Build a list of relative URLs the site will use
    # (These are relative to product1/, since gallery.json lives under product1/assets/)
    photos_rel: List[str] = []
    updated_any = False

    for f in files:
        name = f["name"]
        dropbox_path = f["path_lower"]
        content_hash = f.get("content_hash") or ""

        photos_rel.append(f"./photos/{name}")

        # Download if new/changed
        if not content_hash or known_hashes.get(name) != content_hash:
            download_file(access_token, dropbox_path, output_dir / name)
            known_hashes[name] = content_hash or str(int(time.time()))
            updated_any = True

    # Remove local files that no longer exist in Dropbox
    existing = {f["name"] for f in files}
    to_remove = [n for n in list(known_hashes.keys()) if n not in existing]
    for n in to_remove:
        known_hashes.pop(n, None)
        local = output_dir / n
        if local.exists():
            local.unlink()
            updated_any = True

    payload = {
        "updatedAt": int(time.time()),
        "count": len(photos_rel),
        "photos": sorted(photos_rel),
        "hashes": known_hashes,
    }

    gallery_json_path.parent.mkdir(parents=True, exist_ok=True)
    gallery_json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"Dropbox folder: {folder_path}")
    print(f"Photos found: {len(photos_rel)}")
    print(f"Updated files: {updated_any}")
    print(f"Wrote manifest: {gallery_json_path}")


if __name__ == "__main__":
    main()
