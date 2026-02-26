# PicDropNFC

GitHub Pages static galleries that sync images from Dropbox via GitHub Actions.

## Structure

```text
PicDropNFC/
  .github/workflows/sync-dropbox.yml
  scripts/sync_dropbox.py
  product1/
    index.html
    assets/
      app.js
      styles.css
      gallery.json
      photos/
        .gitkeep
```

## Dropbox setup

1. Create a Dropbox app with **Scoped access** and **App folder**.
2. Enable file metadata read + file content read scopes.
3. Store photos under `product1/` in the Dropbox app folder.
4. Add these GitHub repo secrets:
   - `DROPBOX_CLIENT_ID`
   - `DROPBOX_CLIENT_SECRET`
   - `DROPBOX_REFRESH_TOKEN`

## GitHub Actions sync

- Workflow: `.github/workflows/sync-dropbox.yml`
- Triggered manually and every 10 minutes.
- Uses OAuth refresh token flow to obtain a short-lived Dropbox access token.
- Syncs Dropbox `/product1` into `product1/assets/photos`.
- Rewrites `product1/assets/gallery.json` with image list + sync metadata.

## GitHub Pages

Set Pages to deploy from your default branch root (`/`).

Product 1 URL:

`https://<you>.github.io/PicDropNFC/product1/`

## Add more products

Copy `product1/` to `product2/`, `product3/`, etc., and add matching workflow jobs (or a matrix job) that target each product's Dropbox folder and output paths.
