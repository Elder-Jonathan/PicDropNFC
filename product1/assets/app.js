const GRID = document.getElementById("grid");
const STATUS = document.getElementById("status");
const REFRESH_BTN = document.getElementById("refreshBtn");

const TEN_MIN = 10 * 60 * 1000;

function shuffle(arr) {
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}

async function loadGallery() {
  try {
    STATUS.textContent = " (loading…)";

    const res = await fetch(`./assets/gallery.json?ts=${Date.now()}`, { cache: "no-store" });
    if (!res.ok) throw new Error(`gallery.json fetch failed: ${res.status}`);
    const data = await res.json();

    const photos = shuffle([...(data.photos || [])]);

    GRID.innerHTML = "";
    for (const src of photos) {
      const card = document.createElement("div");
      card.className = "card";

      const img = document.createElement("img");
      img.loading = "lazy";
      img.src = src;

      const meta = document.createElement("div");
      meta.className = "meta";
      meta.textContent = src.split("/").pop();

      card.appendChild(img);
      card.appendChild(meta);
      GRID.appendChild(card);
    }

    const updatedAt = data.updatedAt ? new Date(data.updatedAt * 1000) : null;
    STATUS.textContent = updatedAt
      ? ` (last synced: ${updatedAt.toLocaleString()})`
      : " (loaded)";

    photos.slice(0, 8).forEach((photoPath) => {
      const img = new Image();
      img.src = photoPath;
    });
  } catch (error) {
    console.error(error);
    STATUS.textContent = " (error loading gallery)";
  }
}

REFRESH_BTN.addEventListener("click", loadGallery);

loadGallery();
setInterval(loadGallery, TEN_MIN);
