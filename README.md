# PicDropNFC

GitHub Pages photo gallery per-product folder (e.g. `/product1/`).

## How it works
- `product1/` is a standalone gallery page.
- The page loads `product1/assets/gallery.json`.
- A GitHub Action runs every 10 minutes to sync photos from Dropbox into:
  - `product1/assets/photos/`
  - and regenerates `product1/assets/gallery.json`.

## Run it now (without Dropbox)
1. Enable GitHub Pages:
   - Repo Settings → Pages → Deploy from branch → `main` → `/ (root)`
2. Open:
   - `https://elder-jonathan.github.io/PicDropNFC/product1/`

You should see “No photos yet” which is expected until Dropbox sync is configured.

## Dropbox setup (later)
You will add repository secrets:
- `DROPBOX_CLIENT_ID`
- `DROPBOX_CLIENT_SECRET`
- `DROPBOX_REFRESH_TOKEN`

And set the Dropbox folder path used by the workflow:
- `DROPBOX_FOLDER_PATH: "/product1"`
