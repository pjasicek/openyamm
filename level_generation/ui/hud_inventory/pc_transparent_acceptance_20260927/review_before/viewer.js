"use strict";

const data = window.PC_ALL;
const find = id => document.getElementById(id);
const parameters = new URLSearchParams(location.search);
const images = {};
const numberInRange = (value, min, max) => {
  const number = Number(value);
  return Number.isFinite(number) ? Math.max(min, Math.min(max, Math.round(number * 2) / 2)) : 0;
};
const offset = {
  x: numberInRange(parameters.get("offsetX"), -59, 59),
  y: numberInRange(parameters.get("offsetY"), -79, 79),
};
let family = data.families.find(item => item.id === parameters.get("family") && item.frames.length) ||
  data.families.find(item => item.frames.length);
let index = 0;
let timer = null;
let blinkIndex = 0;
const fresh = (path, frame) => `${path}?v=${frame.sha256.slice(0, 12)}`;

find("summary").textContent = `${data.candidate_frames.toLocaleString()} / ${data.expected_frames.toLocaleString()} ` +
  `portraits available · ${data.native_family_count} native families · ${data.counts.reviewed || 0} / ` +
  `${data.native_family_count * 2} sheets checked · staged for review`;
const heldSheets = data.families.flatMap(item => item.sheets
  .filter(sheet => sheet.status === "tool_hold")
  .map(sheet => ({family: item.id, sheet})));
if (heldSheets.length) {
  const missing = heldSheets.reduce((total, item) => total + item.sheet.frames.length, 0);
  find("heldSheets").hidden = false;
  find("heldSheets").append(`${missing} portraits are unavailable because imagegen rejected these requests: `);
  heldSheets.forEach(({family, sheet}, i) => {
    if (i) find("heldSheets").append(" · ");
    const link = document.createElement("a");
    link.href = `?family=${encodeURIComponent(family)}`;
    link.textContent = `${family} ${sheet.frames[0]}–${sheet.frames.at(-1)}`;
    link.onclick = event => {
      event.preventDefault();
      find("family").value = family;
      find("family").dispatchEvent(new Event("change"));
    };
    find("heldSheets").append(link);
  });
}
for (const item of data.families) {
  const option = new Option(`${item.id} · ${item.frames.length}/56`, item.id);
  option.disabled = !item.frames.length;
  find("family").add(option);
}
for (const name of ["basebar", "facemask", "selring"]) {
  const image = new Image();
  image.onload = drawContext;
  image.src = `../../../../assets_dev/engine/icons_x2/${name}.png`;
  images[name] = image;
}

function selectFamily(number = 1) {
  index = Math.max(0, family.frames.findIndex(frame => frame.number === number));
  find("family").value = family.id;
  find("frame").replaceChildren();
  find("gallery").replaceChildren();
  find("masterLinks").replaceChildren();
  find("reviewNotes").replaceChildren();
  find("sheetStatus").textContent = family.sheets.map(sheet =>
    `${sheet.id} · ${sheet.frames[0]}–${sheet.frames.at(-1)}: ${sheet.status.replaceAll("_", " ")}` +
    (sheet.status === "tool_hold" ? " (imagegen rejected this request; no substitute)" : "")).join(" · ");
  for (const sheet of family.sheets) {
    if (sheet.review) {
      const note = document.createElement("p");
      note.textContent = `Sheet ${sheet.id}: ${sheet.review.note}`;
      find("reviewNotes").append(note);
    }
    if (!sheet.raw) continue;
    for (const [path, label] of [[sheet.raw, `Master ${sheet.id}`], [sheet.comparison, `Comparison ${sheet.id}`]]) {
      const link = document.createElement("a");
      link.href = path;
      link.textContent = label;
      find("masterLinks").append(link);
    }
  }
  for (const [i, frame] of family.frames.entries()) {
    find("frame").add(new Option(frame.name.slice(0, -4), frame.number));
    const button = document.createElement("button");
    button.title = [...frame.notes, ...frame.issues].join(" ") || frame.name;
    const viewport = document.createElement("div");
    viewport.className = `thumbnail backdrop ${find("background").value}`;
    const thumbnail = new Image();
    thumbnail.alt = frame.name;
    thumbnail.src = fresh(frame.candidate, frame);
    thumbnail.loading = "lazy";
    viewport.append(thumbnail);
    const label = document.createElement("span");
    label.textContent = String(frame.number).padStart(2, "0") + (frame.issues.length ? " · check placement" : "");
    if (frame.issues.length) label.className = "flag";
    button.append(viewport, label);
    button.onclick = () => { index = i; render(); };
    find("gallery").append(button);
  }
  for (const [id, number] of [["stone", 12], ["lowered", 35], ["partial", 36]]) {
    find(id).disabled = !family.frames.some(frame => frame.number === number);
  }
  render();
}

function drawContext() {
  const candidate = find("candidate");
  if (!family || !candidate.complete || !candidate.naturalWidth) return;
  const aligned = find("aligned");
  const ctx = aligned.getContext("2d");
  ctx.clearRect(0, 0, aligned.width, aligned.height);
  ctx.drawImage(candidate, offset.x, offset.y);
  const frame = family.frames[index];
  const shifted = offset.x !== 0 || offset.y !== 0;
  find("download").href = shifted ? aligned.toDataURL("image/png") : fresh(frame.candidate, frame);
  find("download").download = shifted ? `${frame.name.slice(0, -4)}-offset-${offset.x}-${offset.y}.png` : frame.name;
  const native = find("native");
  if (!native.complete || !native.naturalWidth || Object.keys(images).length !== 3 ||
      !Object.values(images).every(image => image.complete && image.naturalWidth)) return;
  drawHud(find("originalContext"), native);
  drawHud(find("context"), aligned);
}

function drawHud(canvas, portrait) {
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, 124, 164);
  ctx.drawImage(images.basebar, 39, 55, 124, 164, 0, 0, 124, 164);
  let rect;
  if (find("layout").value === "gameplay") {
    rect = [6, 6, 112, 152];
    ctx.drawImage(portrait, ...rect);
    ctx.drawImage(images.facemask, 2, 2, 120, 160);
    if (find("showRing").checked) ctx.drawImage(images.selring, 0, 2, 120, 160);
  } else {
    rect = [3, 3, 118, 158];
    ctx.drawImage(portrait, ...rect);
    if (find("showRing").checked) ctx.drawImage(images.selring, 3, 3, 118, 158);
  }
  if (find("guides").checked) {
    const [x, y, width, height] = rect;
    ctx.strokeStyle = "#ffcf6dcc";
    ctx.lineWidth = .5;
    ctx.beginPath();
    ctx.moveTo(x + width / 2, y);
    ctx.lineTo(x + width / 2, y + height);
    ctx.moveTo(x, y + height - .25);
    ctx.lineTo(x + width, y + height - .25);
    ctx.stroke();
  }
}

function updateUrl() {
  const url = new URL(location.href);
  url.searchParams.set("family", family.id);
  url.searchParams.set("frame", family.frames[index].number);
  for (const axis of ["x", "y"]) {
    const name = `offset${axis.toUpperCase()}`;
    if (offset[axis]) url.searchParams.set(name, offset[axis]);
    else url.searchParams.delete(name);
  }
  history.replaceState(null, "", url);
}

function updateOffsets(activeInput = null) {
  for (const axis of ["x", "y"]) {
    const name = `offset${axis.toUpperCase()}`;
    for (const id of [name, `${name}Range`]) if (find(id) !== activeInput) find(id).value = offset[axis];
    find("gallery").style.setProperty(`--offset-${axis}`, `${offset[axis]}px`);
  }
  updateUrl();
  drawContext();
}

function measurements(bounds, anchor) {
  return `Height ${bounds[3] - bounds[1]} px · crown y=${bounds[1]} · bottom y=${bounds[3]} · contact x=${anchor[0].toFixed(1)}`;
}

function render() {
  const frame = family.frames[index];
  find("frame").value = frame.number;
  for (const id of ["native", "uncorrected", "candidate"]) find(id).src = fresh(frame[id], frame);
  find("alphaLink").href = fresh(frame.alpha, frame);
  find("note").textContent = [...frame.notes, ...frame.issues.map(issue => `Check: ${issue.replaceAll("_", " ")}.`)].join(" ");
  find("nativeMeasures").textContent = measurements(frame.native_box, frame.native_anchor);
  find("outputMeasures").textContent = measurements(frame.output_box, frame.output_anchor) + " · before global offset";
  find("details").textContent = `Master ${frame.sheet} · generated subject sampling ${frame.sampling[0].toFixed(2)}× / ` +
    `${frame.sampling[1].toFixed(2)}× native · X/Y downscale ${frame.scale[0].toFixed(4)} / ${frame.scale[1].toFixed(4)} · ` +
    `silhouette-center difference ${frame.center_error.toFixed(2)} px · ` +
    `${frame.transparent_pixels.toLocaleString()} fully transparent pixels.`;
  [...find("gallery").children].forEach((button, i) => button.classList.toggle("active", i === index));
  document.title = `${frame.name} · PC restoration review`;
  updateUrl();
  drawContext();
}

function step(delta) { index = (index + delta + family.frames.length) % family.frames.length; render(); }
function selectFrame(number) {
  const found = family.frames.findIndex(frame => frame.number === number);
  if (found >= 0) { index = found; render(); }
}

find("candidate").onload = drawContext;
find("native").onload = drawContext;
find("family").onchange = event => {
  const number = family.frames[index].number;
  family = data.families.find(item => item.id === event.target.value);
  selectFamily(number);
};
find("frame").onchange = event => selectFrame(Number(event.target.value));
find("previous").onclick = () => step(-1);
find("next").onclick = () => step(1);
find("stone").onclick = () => selectFrame(12);
find("lowered").onclick = () => selectFrame(35);
find("partial").onclick = () => selectFrame(36);
find("background").onchange = event => {
  document.querySelectorAll(".backdrop").forEach(element => {
    element.classList.remove("checker", "dark", "light", "green");
    element.classList.add(event.target.value);
  });
};
find("guides").onchange = event => {
  for (const id of ["panels", "gallery"]) find(id).classList.toggle("guides", event.target.checked);
  drawContext();
};
find("showRing").onchange = drawContext;
find("layout").onchange = drawContext;
for (const axis of ["x", "y"]) {
  const name = `offset${axis.toUpperCase()}`;
  for (const id of [name, `${name}Range`]) {
    find(id).oninput = event => {
      if (event.target.value === "") return;
      offset[axis] = numberInRange(event.target.value, Number(event.target.min), Number(event.target.max));
      updateOffsets(event.target);
    };
    find(id).onchange = () => updateOffsets();
  }
}
find("resetOffsets").onclick = () => { offset.x = 0; offset.y = 0; updateOffsets(); };
find("play").onclick = () => {
  if (timer) { clearInterval(timer); timer = null; }
  else timer = setInterval(() => {
    if (find("sequence").value === "blink") selectFrame([1, 1, 1, 13, 1, 1][blinkIndex++ % 6]);
    else step(1);
  }, 280);
  find("play").textContent = timer ? "Pause" : "Play";
};
document.addEventListener("keydown", event => {
  if (["INPUT", "SELECT"].includes(event.target.tagName)) return;
  if (event.key === "ArrowLeft") { event.preventDefault(); step(-1); }
  if (event.key === "ArrowRight") { event.preventDefault(); step(1); }
});
selectFamily(Number(parameters.get("frame")) || 1);
updateOffsets();
