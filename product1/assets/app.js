const GALLERY_URL = "./assets/gallery.json";

function qs(id) {
  return document.getElementById(id);
}

function setStatus(text) {
  qs("status").textContent = text;
}

function fmtTime(epochSeconds) {
  if (!epochSeconds) return "";
  const d = new Date(epochSeconds * 1000);
  return d.toLocaleString();
}

function clearGrid() {
  qs("grid").innerHTML = "";
}

function showEmpty(show) {
  const el = qs("emptyState");
  el.classList.toggle("hidden", !show);
}

function makeCard(src) {
  const card = document.createElement("a");
  card.className = "card";
  card.href = src;
  card.target = "_blank";
  card.rel = "noopener";

  const img = document.createElement("img");
  img.loading = "lazy";
  img.decoding = "async";
  img.alt = "Photo";
  img.src = src;

  card.appendChild(img);
  return card;
}

async function loadGallery() {
  setStatus("Loading…");
  showEmpty(false);
  clearGrid();

  try {
    // Cache-bust so GitHub Pages doesn’t serve stale JSON
    const url = `${GALLERY_URL}?t=${Date.now()}`;
    const res = await fetch(url, { cache: "no-store" });

    if (!res.ok) {
      throw new Error(`Failed to fetch gallery.json (HTTP ${res.status})`);
    }

    const data = await res.json();

    const photos = Array.isArray(data.photos) ? data.photos : [];
    const updatedAt = data.updatedAt ? fmtTime(data.updatedAt) : "";

    qs("updatedAt").textContent = updatedAt ? `Updated: ${updatedAt}` : "";

    if (photos.length === 0) {
      setStatus("No photos found.");
      showEmpty(true);
      return;
    }

    // Randomize display order each load
    const shuffled = [...photos].sort(() => Math.random() - 0.5);

    const grid = qs("grid");
    for (const rel of shuffled) {
      grid.appendChild(makeCard(rel));
    }

    setStatus(`${photos.length} photo(s)`);
  } catch (err) {
    console.error(err);
    setStatus(`Error: ${err.message}`);
    showEmpty(true);
  }
}

function init() {
  qs("refreshBtn").addEventListener("click", loadGallery);
  loadGallery();

  // Light auto-refresh on the client side too
  setInterval(loadGallery, 10 * 60 * 1000);
}

document.addEventListener("DOMContentLoaded", init);
