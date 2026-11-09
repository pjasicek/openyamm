"use strict";

const data = window.PC_ALPHA;
const folder = "review_v2_04";
const select = document.querySelector("#family");
let frameIndex = 0;
let timer = null;
const knownNotes = {
  "wets_": "Stone frame 12 now protects the full helmet. Its dark outer rim still needs a careful outline review.",
  "pc21": "Edge case: fine hair/horns and dark green patches need local mask corrections.",
  "pc25": "Edge case: some green backing remains beneath the jaw; inspect against the light backdrop.",
  "pc23": "Complex green outline: some poses still retain jaw patches. This family needs further local mask corrections.",
  "pc24": "Green skin is protected by the native guide. Inspect the ears and outline across tilted poses.",
  "7pc05": "Compare the pale earrings with the first pass. Their material is now retained independently of face colors.",
  "malea": "Check the band on Dark as well as Light: the bright band was mostly retained already; nearby hair was cut.",
};
document.querySelector("#summary").textContent =
  `Revision 2: ${data.candidate_count} candidate frames from ${data.families.length} characters. ` +
  `Every RGB pixel and canvas size verified unchanged; repeated masks match for ${data.verification.repeat_masks_identical} ` +
  `neutral/stone samples. No acceptance or runtime installation.`;
for (const family of data.families) {
  select.add(new Option(`${family.id} (${family.frames.length} frames)`, family.id));
}
const parameters = new URLSearchParams(location.search);
const initialFamily = parameters.get("family") || "7pc01";
select.value = data.families.some(family => family.id === initialFamily) ? initialFamily : data.families[0].id;

const contextImages = {};
for (const name of ["basebar", "facemask", "selring"]) {
  const image = new Image();
  image.onload = drawContext;
  image.src = `../../../../assets_dev/engine/icons_x2/${name}.png`;
  contextImages[name] = image;
}
document.querySelector("#candidate").onload = drawContext;

function drawContext() {
  const portrait = document.querySelector("#candidate");
  if (!portrait.complete || !portrait.naturalWidth ||
      !Object.values(contextImages).every(image => image.complete && image.naturalWidth)) return;
  const context = document.querySelector("#context").getContext("2d");
  context.clearRect(0, 0, 124, 164);
  context.drawImage(contextImages.basebar, 39, 55, 124, 164, 0, 0, 124, 164);
  // GameplayUiRenderer: 60x80 logical face frame; portrait inset 2;
  // selection ring one logical pixel left. This canvas uses two physical pixels per logical pixel.
  context.drawImage(portrait, 6, 6, 112, 152);
  context.drawImage(contextImages.facemask, 2, 2, 120, 160);
  if (document.querySelector("#showRing").checked) context.drawImage(contextImages.selring, 0, 2, 120, 160);
}

function currentFamily() {
  return data.families.find(family => family.id === select.value);
}

function render() {
  const family = currentFamily();
  const frame = family.frames[frameIndex];
  for (const [id, key] of [["before", "before"], ["prior", "prior"], ["candidate", "candidate"],
    ["alpha", "alpha"], ["native", "native_preview"]]) {
    document.querySelector(`#${id}`).src = `${folder}/${frame[key]}`;
  }
  document.querySelector("#frameLabel").textContent = `Frame ${String(frame.number).padStart(2, "0")}`;
  const policy = frame.stone_guide ? "Stone: neutral and stone guides protect the silhouette. " :
    frame.rounded_profile ? "Full oval: solid interior with a softened outer boundary. " : "Complex outline. ";
  document.querySelector("#note").textContent = policy +
    (knownNotes[family.id] || "Candidate; outline review is still required.");
  document.querySelector("#details").textContent =
    `${frame.target} · ${frame.metrics.transparent_pixels} transparent pixels · ` +
    `${frame.metrics.soft_outline_pixels} pixels of partial outline alpha · ` +
    `${frame.metrics.retained_accessory_components} nearby disconnected components preserved.`;
  document.querySelector("#download").href = `${folder}/${frame.candidate}`;
  document.querySelector("#maskLink").href = `${folder}/${frame.alpha}`;
  document.querySelectorAll("#frames button").forEach((button, index) => {
    button.classList.toggle("active", index === frameIndex);
  });
}

function changeFamily() {
  frameIndex = 0;
  const buttons = document.querySelector("#frames");
  buttons.replaceChildren();
  currentFamily().frames.forEach((frame, index) => {
    const button = document.createElement("button");
    button.textContent = String(frame.number).padStart(2, "0");
    button.onclick = () => { frameIndex = index; render(); };
    buttons.append(button);
  });
  render();
}

function step(delta) {
  const count = currentFamily().frames.length;
  frameIndex = (frameIndex + delta + count) % count;
  render();
}

select.onchange = changeFamily;
document.querySelector("#background").onchange = event => {
  document.querySelector("#cutout").className = `image ${event.target.value}`;
  document.querySelector("#priorBackdrop").className = `image ${event.target.value}`;
};
document.querySelector("#showRing").onchange = drawContext;
document.querySelector("#stone").onclick = () => {
  frameIndex = currentFamily().frames.findIndex(frame => frame.number === 12);
  render();
};
document.querySelector("#previous").onclick = () => step(-1);
document.querySelector("#next").onclick = () => step(1);
document.querySelector("#play").onclick = event => {
  if (timer) { clearInterval(timer); timer = null; }
  else timer = setInterval(() => step(1), 200);
  event.target.textContent = timer ? "Pause slideshow" : "Play frame slideshow";
};
changeFamily();
const initialFrame = Number(parameters.get("frame") || "12");
const initialIndex = currentFamily().frames.findIndex(frame => frame.number === initialFrame);
if (initialIndex >= 0) { frameIndex = initialIndex; render(); }
