async function loadData() {
  const res = await fetch("./data/latest.json?ts=" + Date.now());
  if (!res.ok) throw new Error("failed to load data");
  return res.json();
}

function renderStats(stats) {
  const container = document.getElementById("stats");
  container.innerHTML = "";
  Object.entries(stats || {}).forEach(([k, v]) => {
    const card = document.createElement("article");
    card.className = "stat-card";
    card.innerHTML = `
      <div class="stat-key">${k}</div>
      <div class="stat-val">${v}</div>
    `;
    container.appendChild(card);
  });
}

function renderSummary(summary) {
  const list = document.getElementById("summaryList");
  list.innerHTML = "";
  (summary || []).forEach((line) => {
    const li = document.createElement("li");
    li.textContent = line;
    list.appendChild(li);
  });
}

function renderEvents(events) {
  const root = document.getElementById("events");
  root.innerHTML = "";
  (events || []).forEach((item) => {
    const box = document.createElement("article");
    box.className = "event-item";
    const linkHtml = item.url ? `<a href="${item.url}" target="_blank" rel="noreferrer">来源</a>` : "";
    box.innerHTML = `
      <div class="event-top">
        <div class="event-title">${item.title || "-"}</div>
        <span class="badge">${item.type || "info"}</span>
      </div>
      <div class="event-desc">${item.description || ""}</div>
      <div class="event-time">${item.time || ""} ${linkHtml}</div>
    `;
    root.appendChild(box);
  });
}

async function main() {
  try {
    const data = await loadData();
    document.getElementById("updatedAt").textContent = data.updated_at || "--";
    renderStats(data.stats);
    renderSummary(data.summary);
    renderEvents(data.events);
  } catch (err) {
    document.getElementById("updatedAt").textContent = "load failed";
    console.error(err);
  }
}

main();
