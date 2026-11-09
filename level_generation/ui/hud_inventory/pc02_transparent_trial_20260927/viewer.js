"use strict";

const data = window.PC02_TRIAL;
const find = id => document.getElementById(id);
const images = {};
const parameters = new URLSearchParams(location.search);
const numberInRange = (value, min, max) => {
  const number = Number(value);
  return Number.isFinite(number) ? Math.max(min, Math.min(max, Math.round(number * 2) / 2)) : 0;
};
let index = Math.max(0, Math.min(55, Math.round(Number(parameters.get("frame")) || 1) - 1));
const offset = {
  x: numberInRange(parameters.get("offsetX"), -59, 59),
  y: numberInRange(parameters.get("offsetY"), -79, 79),
};
let timer = null;
let blinkIndex = 0;

find("summary").textContent = "56 portraits from two fresh transparent masters · fixed 118×158 canvases · trial for review";
for (const frame of data.frames) {
  find("frame").add(new Option(`pc02-${String(frame.number).padStart(2, "0")}`, frame.number));
  const button = document.createElement("button");
  button.title = frame.notes.join(" ") || frame.name;
  const thumbnail = document.createElement("img");
  thumbnail.alt = frame.name;
  thumbnail.src = frame.candidate;
  const viewport = document.createElement("div");
  viewport.className = "thumbnail backdrop checker";
  viewport.append(thumbnail);
  const label = document.createElement("span");
  label.textContent = String(frame.number).padStart(2, "0");
  if ([36, 38].includes(frame.number)) {
    label.className = "flag";
    label.textContent += " · check shape";
  }
  button.append(viewport, label);
  button.onclick = () => { index = frame.number - 1; render(); };
  find("gallery").append(button);
}

for (const name of ["basebar", "facemask", "selring"]) {
  const image = new Image();
  image.onload = drawContext;
  image.src = `../../../../assets_dev/engine/icons_x2/${name}.png`;
  images[name] = image;
}

function drawContext() {
  const candidate = find("candidate");
  if (!candidate.complete || !candidate.naturalWidth) return;
  // Translate inside a fixed-size transparent canvas before HUD scaling. This
  // clips at the icon boundary and keeps the ring/facemask at their fixed origin.
  const aligned = find("aligned");
  const alignedContext = aligned.getContext("2d");
  alignedContext.clearRect(0, 0, aligned.width, aligned.height);
  alignedContext.drawImage(candidate, offset.x, offset.y);
  const frame = data.frames[index];
  const shifted = offset.x !== 0 || offset.y !== 0;
  find("download").href = shifted ? aligned.toDataURL("image/png") : frame.candidate;
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
    // GameplayUiRenderer uses a 60x80 logical frame, 2px portrait inset,
    // then facemask and a selection ring offset one logical pixel left.
    rect = [6, 6, 112, 152];
    ctx.drawImage(portrait, ...rect);
    ctx.drawImage(images.facemask, 2, 2, 120, 160);
    if (find("showRing").checked) ctx.drawImage(images.selring, 0, 2, 120, 160);
  } else {
    // NewGameScreen uses the same portraitImageRect for portrait and ring.
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
  url.searchParams.set("frame", data.frames[index].number);
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
    for (const id of [name, `${name}Range`]) {
      if (find(id) !== activeInput) find(id).value = offset[axis];
    }
    find("gallery").style.setProperty(`--offset-${axis}`, `${offset[axis]}px`);
  }
  updateUrl();
  drawContext();
}

function render() {
  const frame = data.frames[index];
  find("frame").value = frame.number;
  for (const id of ["native", "uncorrected", "candidate"]) find(id).src = frame[id];
  find("alphaLink").href = frame.alpha;
  find("note").textContent = frame.notes.join(" ") || "";
  find("details").textContent = `Master ${frame.sheet} · actual subject sampling ${frame.sampling[0].toFixed(2)}× / ` +
    `${frame.sampling[1].toFixed(2)}× native · X/Y downscale ${frame.scale.toFixed(4)} / ${frame.scale_y.toFixed(4)} · ` +
    `scale correction ${frame.scale_adjustment_percent.toFixed(1)}% from the nominal sheet grid · ` +
    `bottom-center alpha ${frame.bottom_center_alpha}/255 · ${frame.transparent_pixels.toLocaleString()} fully transparent pixels.`;
  [...find("gallery").children].forEach((button, i) => button.classList.toggle("active", i === index));
  updateUrl();
  drawContext();
}

function step(delta) { index = (index + delta + data.frames.length) % data.frames.length; render(); }

find("candidate").onload = drawContext;
find("native").onload = drawContext;
find("frame").onchange = event => { index = Number(event.target.value) - 1; render(); };
find("previous").onclick = () => step(-1);
find("next").onclick = () => step(1);
find("stone").onclick = () => { index = 11; render(); };
find("lowered").onclick = () => { index = 34; render(); };
find("partial").onclick = () => { index = 35; render(); };
find("background").onchange = event => {
  document.querySelectorAll(".backdrop").forEach(element => {
    element.classList.remove("checker", "dark", "light", "green");
    element.classList.add(event.target.value);
  });
};
find("guides").onchange = event => {
  find("panels").classList.toggle("guides", event.target.checked);
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
    if (find("sequence").value === "blink") {
      index = [0, 0, 0, 12, 0, 0][blinkIndex++ % 6];
      render();
    } else step(1);
  }, 280);
  find("play").textContent = timer ? "Pause" : "Play";
};
document.addEventListener("keydown", event => {
  if (["INPUT", "SELECT"].includes(event.target.tagName)) return;
  if (event.key === "ArrowLeft") { event.preventDefault(); step(-1); }
  if (event.key === "ArrowRight") { event.preventDefault(); step(1); }
});
render();
updateOffsets();
