"use strict";

const data = window.TOWN_PORTAL_REVIEW;
const canvas = document.querySelector("#map");
const ctx = canvas.getContext("2d", {willReadFrequently: true});
const stage = document.querySelector("#stage");
const status = document.querySelector("#status");
const caption = document.querySelector("#caption");
const showAll = document.querySelector("#showAll");
const colorStrength = document.querySelector("#colorStrength");
const colorValue = document.querySelector("#colorValue");
const images = new Map();
const paletteImages = new Map();
const state = {version: "candidate", hovered: null, focused: null, ready: false,
  colorStrength: data.palette.defaultStrength};
const buttons = new Map();

function applyPalette(pixels, percent) {
  if (percent === 100) return;
  const strength = percent / 100;
  const weights = data.palette.luminanceWeights;
  const neutral = data.palette.neutralRgb;
  const normalization = neutral.reduce((sum, value, i) => sum + value * weights[i], 0);
  const warm = neutral.map(value => value / normalization);
  for (let i = 0; i < pixels.length; i += 4) {
    const luma = pixels[i] * weights[0] + pixels[i + 1] * weights[1] + pixels[i + 2] * weights[2];
    for (let channel = 0; channel < 3; ++channel) {
      pixels[i + channel] = Math.round(luma * warm[channel] * (1 - strength) + pixels[i + channel] * strength);
    }
  }
}

function displayedImage(path, version) {
  if (!version.palette || state.colorStrength === 100) return images.get(path);
  if (paletteImages.has(path)) return paletteImages.get(path);
  const source = images.get(path);
  const surface = document.createElement("canvas");
  surface.width = source.naturalWidth;
  surface.height = source.naturalHeight;
  const context = surface.getContext("2d", {willReadFrequently: true});
  context.drawImage(source, 0, 0);
  const pixels = context.getImageData(0, 0, surface.width, surface.height);
  applyPalette(pixels.data, state.colorStrength);
  context.putImageData(pixels, 0, 0);
  paletteImages.set(path, surface);
  return surface;
}

function draw() {
  if (!state.ready) return;
  const version = data.versions[state.version];
  ctx.drawImage(displayedImage(version.background, version), 0, 0, 1280, 960);
  const active = state.hovered || state.focused;
  for (const item of data.destinations) {
    if (!showAll.checked && item.id !== active) continue;
    const r = item.rect;
    ctx.drawImage(displayedImage(item[version.hoverKey], version), r.x * 2, r.y * 2, r.width * 2, r.height * 2);
  }
  const selected = data.destinations.find(item => item.id === active);
  status.textContent = selected ? `Town Portal: ${selected.label}` : "Hover a destination to highlight it.";
  caption.textContent = `${version.label} · ${version.palette ? state.colorStrength + "% color strength" : version.statusLabel}`;
}

function setVersion(version) {
  if (!data.versions[version]) return;
  state.version = version;
  state.hovered = null;
  state.focused = null;
  for (const button of document.querySelectorAll("button[data-view]")) {
    button.setAttribute("aria-pressed", String(button.dataset.view === version));
  }
  draw();
}

function setColorStrength(value, updateUrl = true) {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return;
  state.colorStrength = Math.max(0, Math.min(100, Math.round(parsed)));
  colorStrength.value = String(state.colorStrength);
  colorValue.textContent = `${state.colorStrength}%`;
  for (const button of document.querySelectorAll("button[data-color]")) {
    button.setAttribute("aria-pressed", String(Number(button.dataset.color) === state.colorStrength));
  }
  paletteImages.clear();
  setVersion("candidate");
  if (updateUrl) {
    const url = new URL(location.href);
    url.searchParams.set("color", String(state.colorStrength));
    url.searchParams.delete("version");
    history.replaceState(null, "", url);
  }
}

colorStrength.addEventListener("input", event => setColorStrength(event.target.value));
for (const button of document.querySelectorAll("button[data-color]")) {
  button.addEventListener("click", () => setColorStrength(button.dataset.color));
}

for (const item of data.destinations) {
  const button = document.createElement("button");
  button.className = "destination";
  button.type = "button";
  button.dataset.destination = item.id;
  button.setAttribute("aria-label", `Town Portal to ${item.label}`);
  button.title = item.label;
  const r = item.rect;
  Object.assign(button.style, {
    left: `${r.x / 640 * 100}%`, top: `${r.y / 480 * 100}%`,
    width: `${r.width / 640 * 100}%`, height: `${r.height / 480 * 100}%`,
  });
  button.addEventListener("pointerenter", () => {state.hovered = item.id; draw();});
  button.addEventListener("pointerleave", () => {state.hovered = null; draw();});
  button.addEventListener("focus", () => {
    state.focused = button.matches(":focus-visible") ? item.id : null;
    draw();
  });
  button.addEventListener("blur", () => {state.focused = null; draw();});
  button.addEventListener("pointerdown", () => {state.focused = null; state.hovered = item.id; draw();});
  button.addEventListener("click", () => {
    draw();
    status.textContent = `Selected ${item.label} — preview only`;
  });
  document.querySelector("#destinations").append(button);
  buttons.set(item.id, button);
}
for (const button of document.querySelectorAll("button[data-view]")) {
  button.addEventListener("click", () => setVersion(button.dataset.view));
}
showAll.addEventListener("change", draw);
document.querySelector("#showAreas").addEventListener("change", event => {
  stage.classList.toggle("show-areas", event.target.checked);
});

async function verifyPreview() {
  const initialStrength = state.colorStrength;
  const expectedCanvas = document.createElement("canvas");
  expectedCanvas.width = 1280;
  expectedCanvas.height = 960;
  const expected = expectedCanvas.getContext("2d", {willReadFrequently: true});
  let statesChecked = 0;
  const checks = Object.keys(data.versions).filter(name => name !== "candidate").map(name => [name, 100]);
  checks.push(...[0, 15, 35, 100].map(value => ["candidate", value]));
  for (const [versionName, strength] of checks) {
    if (versionName === "candidate") setColorStrength(strength, false);
    setVersion(versionName);
    const version = data.versions[versionName];
    const baseline = ctx.getImageData(0, 0, 1280, 960).data;
    for (const item of data.destinations) {
      const button = buttons.get(item.id);
      button.dispatchEvent(new PointerEvent("pointerenter"));
      if (state.hovered !== item.id) throw new Error("Hover did not select " + item.id);
      const r = item.rect;
      expected.drawImage(images.get(version.background), 0, 0, 1280, 960);
      expected.drawImage(images.get(item[version.hoverKey]), r.x * 2, r.y * 2, r.width * 2, r.height * 2);
      if (version.palette) {
        const pixels = expected.getImageData(0, 0, 1280, 960);
        applyPalette(pixels.data, state.colorStrength);
        expected.putImageData(pixels, 0, 0);
      }
      const wanted = expected.getImageData(0, 0, 1280, 960).data;
      const actual = ctx.getImageData(0, 0, 1280, 960).data;
      let changes = 0;
      for (let i = 0; i < actual.length; i += 4) {
        if (actual[i] !== wanted[i] || actual[i + 1] !== wanted[i + 1] || actual[i + 2] !== wanted[i + 2]) {
          throw new Error("Hover pixels differ from the exported patch: " + item.id);
        }
        if (actual[i] !== baseline[i] || actual[i + 1] !== baseline[i + 1] || actual[i + 2] !== baseline[i + 2]) {
          ++changes;
          const x = (i / 4) % 1280, y = Math.floor(i / 4 / 1280);
          if (x < r.x * 2 || x >= (r.x + r.width) * 2 || y < r.y * 2 || y >= (r.y + r.height) * 2) {
            throw new Error("Hover changed pixels outside its rectangle: " + item.id);
          }
        }
      }
      if (!changes) throw new Error("Hover did not change the map: " + item.id);
      button.dispatchEvent(new PointerEvent("pointerleave"));
      const cleared = ctx.getImageData(0, 0, 1280, 960).data;
      if (cleared.some((value, i) => value !== baseline[i])) throw new Error("Hover did not clear: " + item.id);
      const a = stage.getBoundingClientRect(), b = button.getBoundingClientRect();
      if (Math.abs((b.x - a.x) / a.width * 640 - r.x) > 0.1
        || Math.abs((b.y - a.y) / a.height * 480 - r.y) > 0.1
        || Math.abs(b.width / a.width * 640 - r.width) > 0.1
        || Math.abs(b.height / a.height * 480 - r.height) > 0.1) {
        throw new Error("Click area does not match logical placement: " + item.id);
      }
      ++statesChecked;
    }
  }
  setColorStrength(initialStrength, false);
  const first = data.destinations[0];
  buttons.get(first.id).focus();
  if (state.focused !== first.id) throw new Error("Keyboard focus failed");
  buttons.get(first.id).click();
  if (!status.textContent.includes("Selected " + first.label)) throw new Error("Selection failed");
  buttons.get(first.id).blur();
  window.scrollTo(0, 0);
  const report = {result: "PASS", destinations: 6, hoverStatesChecked: statesChecked,
    exactExportedPatchPixels: true, hoverConfinedToDestination: true, resetRestoresMap: true,
    logicalHitAreas: true, keyboardFocusAndClick: true, viewportWidth: window.innerWidth,
    paletteStrengthsChecked: [0, 15, 35, 100], wholeFrameAndSeparatePatchesMatch: true};
  window.townPortalReview.validation = report;
  const output = document.querySelector("#validation");
  output.hidden = false;
  output.textContent = JSON.stringify(report);
  document.documentElement.dataset.validation = "PASS";
}

window.townPortalReview = {data, state, draw, setVersion, setColorStrength, verifyPreview};
const paths = new Set(Object.values(data.versions).map(version => version.background));
for (const item of data.destinations) {
  for (const key of ["default", "hover", "original", "installed"]) paths.add(item[key]);
}
Promise.all([...paths].map(path => new Promise((resolve, reject) => {
  const image = new Image();
  image.onload = () => {images.set(path, image); resolve();};
  image.onerror = () => reject(new Error("Could not load " + path));
  image.src = path;
}))).then(async () => {
  state.ready = true;
  draw();
  const query = new URLSearchParams(location.search);
  if (query.has("color")) setColorStrength(query.get("color"), false);
  if (query.get("verify") === "1") await verifyPreview();
  if (data.versions[query.get("version")]) setVersion(query.get("version"));
  if (query.get("all") === "1") showAll.checked = true;
  if (buttons.has(query.get("hover"))) state.hovered = query.get("hover");
  draw();
}).catch(error => {
  status.textContent = "Preview error: " + error.message;
  document.documentElement.dataset.validation = "FAIL";
  const output = document.querySelector("#validation");
  output.hidden = false;
  output.textContent = error.stack;
});
