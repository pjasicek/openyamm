"use strict";

const data = window.MM8_TOWN_PORTAL_REVIEW;
const stage = document.getElementById("stage");
const art = document.getElementById("art");
const before = document.getElementById("before");
const size = document.getElementById("size");
const split = document.getElementById("split");
const status = document.getElementById("status");
const showAll = document.getElementById("show-all");
const images = new Map();
const buttons = new Map();
const state = {mode: "candidate", hovered: null, focused: null, pressed: null, ready: false};

function drawMap(canvas, versionName) {
  const version = data.versions[versionName];
  const context = canvas.getContext("2d", {willReadFrequently: true});
  context.imageSmoothingEnabled = versionName !== "original";
  const background = images.get(version.background);
  context.fillStyle = "#0c0e11";
  context.fillRect(0, 0, 1280, 960);
  if (version.fit === "contain") {
    const scale = Math.min(1280 / background.naturalWidth, 960 / background.naturalHeight);
    const width = background.naturalWidth * scale, height = background.naturalHeight * scale;
    context.drawImage(background, (1280 - width) / 2, (960 - height) / 2, width, height);
  } else {
    context.drawImage(background, 0, 0, 1280, 960);
  }
  if (!version.hoverKey) return;
  const active = state.pressed || state.hovered || state.focused;
  for (const item of data.destinations) {
    if (!showAll.checked && item.id !== active) continue;
    const r = item.rect;
    context.drawImage(images.get(item[version.hoverKey]), r.x * 2, r.y * 2, r.width * 2, r.height * 2);
  }
}

function draw() {
  if (!state.ready) return;
  drawMap(art, state.mode === "compare" ? "candidate" : state.mode);
  if (state.mode === "compare") drawMap(before, "previous");
  const active = state.pressed || state.hovered || state.focused;
  const item = data.destinations.find(destination => destination.id === active);
  const version = data.versions[state.mode === "compare" ? "candidate" : state.mode];
  status.textContent = !version.hoverKey ? `${version.label} — background comparison`
    : item ? `Town Portal: ${item.label}` : "Hover a destination to highlight it.";
}

function setMode(mode) {
  if (mode !== "compare" && !data.versions[mode]) return;
  state.mode = mode;
  state.hovered = state.focused = state.pressed = null;
  stage.classList.toggle("native", mode === "original");
  const interactive = Boolean(data.versions[mode === "compare" ? "candidate" : mode].hoverKey);
  document.getElementById("destinations").hidden = !interactive;
  showAll.disabled = !interactive;
  document.getElementById("show-areas").disabled = !interactive;
  for (const input of document.querySelectorAll("input[name=mode]")) input.checked = input.value === mode;
  for (const id of ["before", "divider", "wipe", "left-label", "right-label"]) {
    document.getElementById(id).hidden = mode !== "compare";
  }
  draw();
}

for (const item of data.destinations) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "destination";
  button.dataset.destination = item.id;
  button.setAttribute("aria-label", `Town Portal to ${item.label}`);
  const r = item.rect;
  Object.assign(button.style, {
    left: `${r.x / 640 * 100}%`, top: `${r.y / 480 * 100}%`,
    width: `${r.width / 640 * 100}%`, height: `${r.height / 480 * 100}%`,
  });
  button.addEventListener("pointerenter", () => { state.hovered = item.id; draw(); });
  button.addEventListener("pointerleave", () => { state.hovered = null; draw(); });
  button.addEventListener("focus", () => {
    state.focused = button.matches(":focus-visible") ? item.id : null;
    draw();
  });
  button.addEventListener("blur", () => { state.focused = null; draw(); });
  button.addEventListener("pointerdown", () => { state.pressed = item.id; state.focused = null; draw(); });
  button.addEventListener("click", () => {
    status.textContent = `Selected ${item.label} — preview only`;
  });
  document.getElementById("destinations").append(button);
  buttons.set(item.id, button);
}
window.addEventListener("pointerup", () => { state.pressed = null; draw(); });
window.addEventListener("pointercancel", () => { state.pressed = null; draw(); });
window.addEventListener("blur", () => {
  state.hovered = state.focused = state.pressed = null;
  draw();
});
document.getElementById("modes").addEventListener("change", event => setMode(event.target.value));
size.addEventListener("change", () => { stage.dataset.size = size.value; });
split.addEventListener("input", () => {
  before.style.clipPath = `inset(0 ${100 - Number(split.value)}% 0 0)`;
  document.getElementById("divider").style.left = `${split.value}%`;
});
showAll.addEventListener("change", draw);
document.getElementById("show-areas").addEventListener("change", event => {
  stage.classList.toggle("show-areas", event.target.checked);
});

function verifyPreview() {
  setMode("candidate");
  showAll.checked = false;
  const context = art.getContext("2d");
  const baseline = context.getImageData(0, 0, 1280, 960).data;
  const patch = document.createElement("canvas");
  for (const item of data.destinations) {
    const r = item.rect;
    const button = buttons.get(item.id);
    button.dispatchEvent(new PointerEvent("pointerenter"));
    if (state.hovered !== item.id) throw new Error("Wrong hovered destination: " + item.id);
    patch.width = r.width * 2;
    patch.height = r.height * 2;
    const patchContext = patch.getContext("2d", {willReadFrequently: true});
    const exported = images.get(item.hover);
    if (exported.naturalWidth !== patch.width || exported.naturalHeight !== patch.height) {
      throw new Error("Wrong export dimensions: " + item.id);
    }
    patchContext.drawImage(exported, 0, 0);
    const wanted = patchContext.getImageData(0, 0, patch.width, patch.height).data;
    const actual = context.getImageData(0, 0, 1280, 960).data;
    let changes = 0;
    for (let i = 0; i < actual.length; i += 4) {
      const x = (i / 4) % 1280, y = Math.floor(i / 4 / 1280);
      const inside = x >= r.x * 2 && x < (r.x + r.width) * 2 && y >= r.y * 2 && y < (r.y + r.height) * 2;
      const p = ((y - r.y * 2) * patch.width + x - r.x * 2) * 4;
      for (let channel = 0; channel < 4; channel++) {
        if (actual[i + channel] !== (inside ? wanted[p + channel] : baseline[i + channel])) {
          throw new Error("Hover pixels or surroundings changed incorrectly: " + item.id);
        }
      }
      if (actual[i] !== baseline[i] || actual[i + 1] !== baseline[i + 1] || actual[i + 2] !== baseline[i + 2]) {
        changes++;
      }
    }
    if (!changes) throw new Error("Empty highlight: " + item.id);
    button.dispatchEvent(new PointerEvent("pointerleave"));
    const reset = context.getImageData(0, 0, 1280, 960).data;
    if (reset.some((value, i) => value !== baseline[i])) throw new Error("Hover failed to reset: " + item.id);
    const a = stage.getBoundingClientRect(), b = button.getBoundingClientRect();
    const measured = [(b.x - a.x) / a.width * 640, (b.y - a.y) / a.height * 480,
      b.width / a.width * 640, b.height / a.height * 480];
    if (measured.some((value, i) => Math.abs(value - [r.x, r.y, r.width, r.height][i]) > 0.1)) {
      throw new Error("Click rectangle differs from native placement: " + item.id);
    }
  }
  const first = data.destinations[0];
  buttons.get(first.id).focus();
  if (state.focused !== first.id) throw new Error("Keyboard highlight failed");
  buttons.get(first.id).click();
  if (!status.textContent.includes("Selected " + first.label)) throw new Error("Selection failed");
  buttons.get(first.id).blur();
  const report = {result: "PASS", destinations: data.destinations.length, exactExportedPatchPixels: true,
    unchangedSurroundingMap: true, exactHoverReset: true, logicalHitAreas: true,
    keyboardFocusAndClick: true, viewportWidth: window.innerWidth};
  window.mm8TownPortalReview.validation = report;
  document.documentElement.dataset.validation = "PASS";
  const output = document.getElementById("validation");
  output.hidden = false;
  output.textContent = JSON.stringify(report);
  window.scrollTo(0, 0);
}

window.mm8TownPortalReview = {data, state, draw, setMode, verifyPreview};
const paths = new Set(Object.values(data.versions).map(version => version.background));
for (const item of data.destinations) for (const key of ["hover", "installed", "original"]) paths.add(item[key]);
Promise.all([...paths].map(path => new Promise((resolve, reject) => {
  const image = new Image();
  image.onload = () => { images.set(path, image); resolve(); };
  image.onerror = () => reject(new Error("Could not load " + path));
  image.src = path;
}))).then(() => {
  const query = new URLSearchParams(location.search);
  if (["fit", "game", "actual"].includes(query.get("size"))) size.value = query.get("size");
  stage.dataset.size = size.value;
  state.ready = true;
  draw();
  if (query.get("verify") === "1") verifyPreview();
  setMode(query.get("mode") || "candidate");
  if (buttons.has(query.get("hover"))) state.hovered = query.get("hover");
  showAll.checked = query.get("all") === "1";
  draw();
}).catch(error => {
  status.textContent = "Preview error: " + error.message;
  document.documentElement.dataset.validation = "FAIL";
  const output = document.getElementById("validation");
  output.hidden = false;
  output.textContent = error.stack;
});
