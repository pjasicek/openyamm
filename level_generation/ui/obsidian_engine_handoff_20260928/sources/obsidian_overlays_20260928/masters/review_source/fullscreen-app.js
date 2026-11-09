"use strict";

const $ = selector => document.querySelector(selector);
const $$ = selector => [...document.querySelectorAll(selector)];
const query = new URLSearchParams(location.search);
const sharedAssets = "../hud_concepts_20260927/assets/";
const screens = {
  "2060": { name: "Inventory & equipment", sourceWidth: 1574, sourceHeight: 899, sourceX: 190,
    topHeight: 46, topWidth: 1200, baseTop: 690, inventory: true,
    preserved: [{ x: 8, y: 59, w: 849, h: 550, label: "ITEM GRID · SAME PLACEMENT" },
      { x: 876, y: 46, w: 324, h: 644, label: "PAPERDOLL · ORIGINAL ART" }] },
  "2061": { name: "A Lonely Knight · house occupants", sourceWidth: 1542, sourceHeight: 894, sourceX: 168,
    topHeight: 49, topWidth: 876, baseTop: 685, title: "A Lonely Knight",
    portraits: [{ x: 1070, y: 66 }, { x: 1213, y: 66 }, { x: 1070, y: 232 }, { x: 1213, y: 232 }],
    preserved: [{ x: 14, y: 50, w: 862, h: 635, label: "HOUSE VIDEO · EXISTING WINDOW" }] },
  "2062": { name: "The Knife Shoppe · merchant dialogue", sourceWidth: 1512, sourceHeight: 901, sourceX: 156,
    topHeight: 54, topWidth: 876, baseTop: 689, title: "The Knife Shoppe", shop: true,
    portraits: [{ x: 1129, y: 70 }],
    preserved: [{ x: 14, y: 55, w: 862, h: 634, label: "HOUSE VIDEO · EXISTING WINDOW" }] },
};
const treatments = {
  legacy: { label: "REFERENCE / CURRENT SCREENS", title: "The existing frame and ornament",
    note: "These screens are already distinct, fixed compositions. A new gameplay HUD does not require an immediate " +
      "inventory or dialogue redesign. The visual transition is noticeable, but their functions remain familiar." },
  bars: { label: "HISTORICAL / SHARED BARS", title: "A useful halfway comparison",
    note: "The resources and party dock now match Obsidian. The stone tabs and dialogue panel remain prominent, " +
      "so this shows why a party-bar swap alone does not quite unify the screen." },
  frames: { label: "PREVIOUS ATTEMPT / NOT ACCEPTED", title: "Too plain",
    note: "The earlier proposal removed too much of the frame’s material and ornament. It is retained here for " +
      "comparison with the two new treatments, following the user’s feedback." },
  carved: { label: "SELECTED DIRECTION / REVISION 06", title: "Carved Obsidian · portrait alignment",
    note: "Each party portrait, its selection and status indicators, and its health/mana bars are shifted " +
      "3 units right and 5 units down, following the final alignment request." },
  stone: { label: "REVISION 02 / WEATHERED STONE", title: "Keep the old craft visible",
    note: "The original green stone, raised scrollwork and panel frames carry the design. Deeper patina and warmer " +
      "brass accents accompany the revised portraits and type. This is the option closest to the existing game’s feel." },
};
const people = [
  { name: "Kareth", src: "assets/pc03-01.png", hp: 97, sp: 75 },
  { name: "Elara", src: sharedAssets + "pc04-01.png", hp: 75, sp: 82 },
  { name: "Mara", src: sharedAssets + "pc06-01.png", hp: 89, sp: 70 },
  { name: "Vaelis", src: sharedAssets + "pc15-01.png", hp: 88, sp: 79 },
  { name: "Tor", src: sharedAssets + "pc21-01.png", hp: 95, sp: 64 },
];
let screen = Object.hasOwn(screens, query.get("screen")) ? query.get("screen") : "2061";
let treatment = Object.hasOwn(treatments, query.get("treatment")) ? query.get("treatment") : "carved";
let partyCount = query.get("party") === "5" ? 5 : 1;
let selected = 0;
let speech = ["short", "long"].includes(query.get("speech")) ? query.get("speech") : "off";
let showPreserved = query.get("preserved") === "1";
let buttonFace = ["fondamento", "almendra", "endgame"].includes(query.get("buttons")) ? query.get("buttons") : "";

function buttonClass(extra = "") {
  return buttonFace && treatment === "carved" ? `obs-button ${extra}` : "";
}

function buttonLabel(label) {
  return buttonFace && treatment === "carved" ? `<span class="obs-label">${label}</span>` : label;
}

function sourceStyle(data, x, y) {
  return `background-image:url(assets/${screen}.png);background-size:${data.sourceWidth}px ${data.sourceHeight}px;` +
    `background-position:-${x}px -${y}px;`;
}

function image(src, className = "") {
  return `<img src="${src}" class="${className}" alt="" draggable="false">`;
}

function flourish(className) {
  return `<span class="frame-flourish ${className}" aria-hidden="true"><svg viewBox="0 0 240 26">
    <path d="M4 14h68c18 0 24-9 37-9m-67 9c8-13 29-13 34-2m-17-5c0-5-5-7-9-5m23 12c7 9 25 8 32 0
      M236 14h-68c-18 0-24-9-37-9m67 9c-8-13-29-13-34-2m17-5c0-5 5-7 9-5m-23 12c-7 9-25 8-32 0"/>
    <path d="m109 14 11-9 11 9-11 9Z"/><path d="m116 14 4-4 4 4-4 4Z"/>
  </svg></span>`;
}

function portrait(index) {
  if (index >= partyCount) {
    const crestId = String(Math.max(1, index)).padStart(2, "0");
    const crest = treatment === "carved" ? `assets/generated/carved-obsidian-empty-slot-${crestId}-v1.png`
      : `assets/ibshield${crestId}.png`;
    return `<div class="party-slot"><div class="empty-slot" title="Empty party slot">
      ${image(crest)}</div></div>`;
  }
  const person = people[index];
  return `<div class="party-slot"><button class="person" data-person="${index}" aria-pressed="${selected === index}"
      aria-label="Select ${person.name}, health ${person.hp}%, mana ${person.sp}%">
    <span class="selection-diamond"></span><span class="portrait-ring">${image(person.src)}</span>
    ${treatment === "carved" ? "" : `<span class="pc-name">${person.name}</span>`}
    <span class="meter" style="--fill:${person.hp}%"><i></i></span>
    <span class="meter sp" style="--fill:${person.sp}%"><i></i></span>
    <svg class="alert" viewBox="0 0 28 30" aria-hidden="true"><path d="M14 1 26 15 14 29 2 15Z" fill="#111820" stroke="#b2a28b" stroke-width=".8"/>
      <path d="M14 4 23 15 14 26 5 15Z" fill="#50df79"/><path d="M14 4 23 15H5Z" fill="#fff" opacity=".27"/>
      <path d="M14 15h9L14 26Z" fill="#07121c" opacity=".24"/></svg>
  </button>${index === 0 ? `<button class="personal-buff" data-preview="Kareth’s personal effects: Bless · 25m (example)"
      aria-label="Inspect Kareth’s personal effects">${image(sharedAssets + "generated/obsidian-personal-buffs-v1.png")}</button>` : ""}</div>`;
}

function carvedBasebar() {
  // Slice the existing frame at its rail/body seam; do not compress the portraits or the Close panel.
  const texture = `<image href="assets/generated/carved-obsidian-basebar-v2.png" width="2169" height="725"/>`;
  return `<svg class="basebar-art" viewBox="0 0 1200 214" preserveAspectRatio="none" aria-hidden="true">
    <svg x="0" y="0" width="910" height="28" viewBox="0 166.5 1644 67.5"
      preserveAspectRatio="none" overflow="hidden">${texture}</svg>
    <svg x="0" y="28" width="910" height="186" viewBox="0 234 1644 314.1"
      preserveAspectRatio="none" overflow="hidden">${texture}</svg>
    <svg x="910" y="0" width="290" height="214" viewBox="1644 166.5 525 381.6"
      preserveAspectRatio="none" overflow="hidden">${texture}</svg>
  </svg>`;
}

function sharedFrame(data) {
  return `<div class="topbar"><span class="resource">${image(sharedAssets + "scorebg_gold.png")}10,000</span>
    <span class="resource-separator"></span><span class="resource food">${image(sharedAssets + "scorebg_food.png")}7<small>food</small></span></div>
    <div class="bottom-dock">${treatment === "carved" ? carvedBasebar() : ""}
      <div class="dock-status" role="status"></div>
      <div class="party-slots">${Array.from({ length: 5 }, (_, i) => portrait(i)).join("")}</div>
      ${data.inventory ? "" : `${treatment === "carved" ? "" : flourish("close-flourish")}<button class="exit-button ${buttonClass()}"
        data-preview="Close returns to the gameplay HUD.">${buttonLabel("Close")}${treatment === "carved" ? "" : " <small>ESC</small>"}</button>`}
    </div>`;
}

function contentFrame(data) {
  if (data.inventory) {
    return `<div class="inventory-surface"></div><div class="crop inventory-grid"
      style="left:8px;top:59px;width:849px;height:550px;${sourceStyle(data, data.sourceX + 8, 59)}"></div>
      <div class="grid-outline"></div><nav class="inventory-tabs" aria-label="Character pages">
      ${["Stats", "Skills", "Inventory", "Awards", "Exit"].map(name => `<button
        class="${buttonClass()}" data-button-tab="${name}"
        ${name === "Exit" ? "" : `aria-pressed="${name === "Inventory"}"`}
        data-preview="${name === "Exit" ? "Exit returns to gameplay." : name + " opens its existing character page."}">${buttonLabel(name)}</button>`).join("")}</nav>`;
  }
  return `<div class="video-left-frame"></div><aside class="dialogue-panel ${data.shop ? "shop" : "occupants"}"><h2>${data.title}</h2>
    ${flourish("title-flourish")}${flourish("panel-flourish")}
    ${data.portraits.map((position, index) => `<button class="npc-card" data-npc="${index}" aria-pressed="false"
      aria-label="${data.shop ? "Speak with Caine" : `Speak with occupant ${index + 1}`}">
      <span class="crop" style="${sourceStyle(data, position.x, position.y)}"></span></button>`).join("")}
    ${data.shop ? `<div class="npc-identity"><b>Caine</b><small>Blacksmith</small></div>
      <nav class="topics" aria-label="Dialogue topics">${["Buy Standard", "Buy Special", "Display Equipment", "Learn Skills"].map(topic =>
        `<button class="${buttonClass("obs-topic")}" data-topic="${topic}" aria-pressed="false">${buttonLabel(topic)}</button>`).join("")}</nav>` : ""}</aside>`;
}

function speechPanel(data) {
  if (data.inventory || speech === "off") return "";
  const text = data.shop
    ? speech === "short" ? "Looking for a new blade? Take a look at my wares."
      : "A good weapon should feel right in your hand. Take your time and look over what I have in stock. " +
        "If you want something finer, ask to see the special selection. Bring me the equipment you no longer need, " +
        "and we can see what it is worth."
    : speech === "short" ? "Come in, traveller. There’s a place by the fire."
      : "Come in, traveller. There’s a place by the fire, and you’ll find a few people here who know the roads. " +
        "Some are looking for work, others have stories to tell. Speak with them before you leave; " +
        "a little local knowledge can make a long journey much easier.";
  return `<section class="speech-panel"><h3>${data.shop ? "Caine" : "The innkeeper"}</h3><p>${text}</p></section>`;
}

function scaleStage() {
  const host = $("#stage-host");
  const scale = Math.min(host.clientWidth / 1600, host.clientHeight / 900);
  $("#stage").style.transform = `scale(${scale})`;
  $("#stage").style.left = `${(host.clientWidth - 1600 * scale) / 2}px`;
  $("#stage").style.top = `${(host.clientHeight - 900 * scale) / 2}px`;
}

function feedback(text) { $("#feedback").textContent = text; }

function render() {
  const data = screens[screen];
  const stage = $("#stage");
  selected = Math.min(selected, partyCount - 1);
  const material = treatment === "carved" || treatment === "stone";
  stage.className = `stage view-${treatment}${material ? " material" : ""}`;
  if (buttonFace && treatment === "carved") stage.classList.add("button-theme", `font-${buttonFace}`);
  stage.style.setProperty("--top-height", `${data.topHeight}px`);
  stage.style.setProperty("--top-width", `${data.topWidth}px`);
  stage.style.setProperty("--base-top", `${data.baseTop}px`);
  stage.innerHTML = `${treatment === "legacy" ? `<img class="original-full" src="assets/${screen}.png"
      style="left:${200 - data.sourceX}px" alt="Original screenshot ${screen}">` : ""}
    <div class="workspace"><div class="source-layer" style="${sourceStyle(data, data.sourceX, 0)}"></div>
      ${treatment === "legacy" ? "" : sharedFrame(data)}
      ${treatment === "frames" || material ? contentFrame(data) : ""}
      ${treatment === "legacy" ? "" : speechPanel(data)}
      ${showPreserved ? data.preserved.map(area => `<div class="preserved-area"
        style="left:${area.x}px;top:${area.y}px;width:${area.w}px;height:${area.h}px"><span>${area.label}</span></div>`).join("") : ""}
    </div>`;
  $$("[data-screen]").forEach(button => button.setAttribute("aria-pressed", String(button.dataset.screen === screen)));
  $$("[data-treatment]").forEach(button => button.setAttribute("aria-pressed", String(button.dataset.treatment === treatment)));
  $("#party-count").value = String(partyCount);
  $("#party-count").disabled = treatment === "legacy";
  $("#speech").value = speech;
  $("#speech").disabled = data.inventory || treatment === "legacy";
  $("#preserved").checked = showPreserved;
  $("#button-font").value = buttonFace;
  $("#button-font").disabled = treatment !== "carved";
  $("#screen-caption").textContent = `${screen}.png · ${data.name}`;
  $("#treatment-label").textContent = treatments[treatment].label;
  $("#treatment-title").textContent = treatments[treatment].title;
  $("#treatment-note").textContent = treatments[treatment].note;
  feedback("");
  $$("[data-person]").forEach(button => button.addEventListener("click", () => {
    selected = Number(button.dataset.person);
    $$("[data-person]").forEach(other => other.setAttribute("aria-pressed", String(Number(other.dataset.person) === selected)));
    feedback(`${people[selected].name} selected. The grid and equipment in this visual study retain the captured character’s contents.`);
  }));
  $$("[data-preview]").forEach(button => button.addEventListener("click", () => feedback(button.dataset.preview)));
  $$(".obs-button[data-button-tab][aria-pressed]").forEach(button => button.addEventListener("click", () => {
    $$("[data-button-tab][aria-pressed]").forEach(other => other.setAttribute("aria-pressed", String(button === other)));
    feedback(`${button.dataset.buttonTab} selected for the button study. The captured inventory content remains visible.`);
  }));
  $$("[data-topic]").forEach(button => button.addEventListener("click", () => {
    $$("[data-topic]").forEach(other => other.setAttribute("aria-pressed", String(button === other)));
    feedback(`${button.dataset.topic}: the existing shop/service screen opens here.`);
  }));
  $$("[data-npc]").forEach(button => button.addEventListener("click", () => {
    $$("[data-npc]").forEach(other => other.setAttribute("aria-pressed", String(button === other)));
    feedback(data.shop ? "Caine’s topics are shown below his portrait." : "This portrait opens the occupant’s existing dialogue topics.");
  }));
  const search = new URLSearchParams(location.search);
  search.set("screen", screen); search.set("treatment", treatment); search.set("party", partyCount);
  search.set("speech", speech); showPreserved ? search.set("preserved", "1") : search.delete("preserved");
  buttonFace ? search.set("buttons", buttonFace) : search.delete("buttons");
  history.replaceState(null, "", `${location.pathname}?${search}`);
  scaleStage();
}

$$("[data-screen]").forEach(button => button.addEventListener("click", () => { screen = button.dataset.screen; render(); }));
$$("[data-treatment]").forEach(button => button.addEventListener("click", () => { treatment = button.dataset.treatment; render(); }));
$("#party-count").addEventListener("change", event => { partyCount = Number(event.target.value); render(); });
$("#speech").addEventListener("change", event => { speech = event.target.value; render(); });
$("#preserved").addEventListener("change", event => { showPreserved = event.target.checked; render(); });
$("#button-font").addEventListener("change", event => { buttonFace = event.target.value; render(); });
$("#fullscreen").addEventListener("click", () => $("#stage-host").requestFullscreen());
document.addEventListener("fullscreenchange", scaleStage);
window.addEventListener("resize", scaleStage);
if (query.get("export") === "1") document.body.classList.add("export");
render();
new ResizeObserver(scaleStage).observe($("#stage-host"));
