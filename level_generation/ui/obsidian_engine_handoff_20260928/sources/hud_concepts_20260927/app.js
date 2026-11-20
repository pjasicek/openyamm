"use strict";

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
const params = new URLSearchParams(location.search);
const concepts = {
  verdigris: {
    number: "01", name: "Verdigris", kicker: "01 / EVOLUTION",
    description: "Keep the green patina, brass and oval faces. Replace the stacked stone blocks with a low, connected " +
      "plinth, give every edge the same fine brass treatment, and bring gold and food together. Familiar HP/SP columns " +
      "remain; buff timers and readiness get more breathing room.",
    tradeoff: "The closest fit for the existing game. The solid lower edge still occupies more scenery than option 02.",
    annotations: [
      { x: 31, y: 165, title: "One resource strip", text: "Gold and food share a compact brass-edged tray. Rest remains one click away." },
      { x: 536, y: 533, title: "Keep the faces", text: "Same art, thinner oval frames. HP and SP retain their familiar vertical pairing." },
      { x: 1126, y: 492, title: "One material language", text: "Fine brass edges replace the repeated thick green frames around every group." },
    ],
  },
  obsidian: {
    number: "02", name: "Obsidian", kicker: "02 / REFINED DIRECTION",
    description: "Charcoal, pale brass and floating portraits. Bright green, yellow and red jewels carry the alert " +
      "signal; the portrait rim and diamond carry selection. A matching set of sculpted icons serves the commands, " +
      "followers and personal enchantments. Timed party buffs stay in a bounded strip, soonest expiries first.",
    tradeoff: "Four effects + overflow is the default; try two rows for more at-a-glance information. Bars use static " +
      "shading, with a brief trail only when damaged. Status text sits just above the portraits.",
    annotations: [
      { x: 40, y: 330, title: "Bounded buff strip", text: "Four soonest expiries, then +N hidden effects. The two-row alternative uses the same width." },
      { x: 622, y: 480, title: "A stronger selection", text: "A brighter double rim and a larger diamond. The alert jewel alone carries the ready/danger signal." },
      { x: 1132, y: 397, title: "Quiet by default", text: "Shaded bars stay still. A short damage trail explains a hit; the low-health pulse is optional." },
    ],
  },
  journal: {
    number: "03", name: "Field journal", kicker: "03 / RECOMPOSITION",
    description: "Treat the interface as a traveller’s kit: leather bindings, a vellum chart, aged brass and quiet " +
      "oxblood accents. The party moves into a readable left rail. Named effects sit beside the map, and a small " +
      "tool tray leaves the lower centre of the world largely open.",
    tradeoff: "The strongest change in feel and the easiest stats to read. The party rail uses left-side vision and changes scanning habits.",
    annotations: [
      { x: 320, y: 269, title: "A party rail", text: "Original portraits sit beside named, numbered HP/SP bars. Ready and recovering states remain separate." },
      { x: 1045, y: 89, title: "A travelling chart", text: "A warm vellum mount gives the actual square minimap a physical, in-world character." },
      { x: 1086, y: 645, title: "Name the effects", text: "The full effect name and duration stay visible. Original body/skull tableaux remain inspectable." },
    ],
  },
  current: {
    number: "00", name: "Current HUD", kicker: "00 / ORIGINAL REFERENCE",
    description: "The untouched test_img/2000.png reference. The green framed strips, stacked party base, body/skull " +
      "buff panels and lower-right map establish the current visual language. This particular screenshot has one " +
      "party member; the three concepts can be switched between one, four and five.",
    tradeoff: "The concepts use a tighter, identical crop of this scene to expose the world behind their new frames. This is a visual study, not a runtime capture.",
    annotations: [],
  },
};
const people = [
  { name: "Kareth", art: "pc02-01", hp: 128, maxHp: 132, sp: 36, maxSp: 48 },
  { name: "Elara", art: "pc04-01", hp: 72, maxHp: 96, sp: 105, maxSp: 128 },
  { name: "Mara", art: "pc06-01", hp: 91, maxHp: 102, sp: 64, maxSp: 92 },
  { name: "Vaelis", art: "pc15-01", hp: 85, maxHp: 96, sp: 117, maxSp: 148 },
  { name: "Tor", art: "pc21-01", hp: 180, maxHp: 188, sp: 18, maxSp: 28 },
];
const buffs = [
  { name: "Shield", art: "sba06a", duration: "12m", detail: "Party protection against incoming ranged attacks." },
  { name: "Wizard Eye", art: "sba01a", duration: "38m", detail: "Minimap awareness. Marker visibility still follows the spell’s mastery." },
  { name: "Haste", art: "sbf05a", duration: "0:42", detail: "Shorter action recovery. An amber edge flags the approaching expiry.", expiring: true },
  { name: "Fly", art: "sba10a", duration: "24m", detail: "Flight is available. The movement controls and spell-point cost keep their existing behaviour." },
];
const personalBuffs = {
  0: [{ name: "Bless", art: "sbs02a", seconds: 1500,
    detail: "Improves this character’s attack accuracy." }],
};
let concept = Object.hasOwn(concepts, params.get("concept")) ? params.get("concept") : "obsidian";
let sceneState = ["explore", "nearby", "combat"].includes(params.get("state")) ? params.get("state") : "explore";
let partyCount = [1, 4, 5].includes(Number(params.get("party"))) ? Number(params.get("party")) : 5;
let selected = 0;
let turnPhase = [0, 1, 2, 3].includes(Number(params.get("turn"))) ? Number(params.get("turn")) : 0;
let buffLayout = params.get("buffLayout") === "rows" ? "rows" : "compact";
let buffCount = [0, 4, 12, 22].includes(Number(params.get("buffs"))) && params.has("buffs")
  ? Number(params.get("buffs")) : 12;
let barStyle = ["flat", "shaded", "pulse"].includes(params.get("bars")) ? params.get("bars") : "shaded";
let statusPreview = ["off", "short", "long", "wrapped", "custom"].includes(params.get("status"))
  ? params.get("status") : "off";
let customStatus = (params.get("text") || "").slice(0, 400);
let damageSample = null;
let damageTimers = [];
let messageTimer = null;
let mapZoom = 1;
let compareMode = false;
let returnFocus = null;
const phaseNames = ["Real time", "Turn based", "Turn based", "Turn based"];
const phaseDetails = ["", "ATTACK PHASE · Select a ready character", "MOVEMENT PHASE · 3 steps remaining", "WAITING · Enemies are acting"];
const stage = $("#stage");
const hud = $("#hud");
const stateLabels = { explore: "Area clear", nearby: "Enemies nearby", combat: "Melee danger" };
const stateAssets = { explore: "statg", nearby: "staty", combat: "statr" };

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, character => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[character]);
}

function activePartyBuffs() {
  const ids = partyBuffPresets[buffCount];
  return partyBuffCatalog.map((buff, order) => ({ ...buff, order }))
    .filter(buff => ids.includes(buff.id) && buff.seconds > 0)
    .sort((a, b) => a.seconds - b.seconds || a.order - b.order);
}

function formatDuration(seconds) {
  if (seconds < 60) return `0:${String(Math.ceil(seconds)).padStart(2, "0")}`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
  const minutes = Math.floor(seconds % 3600 / 60);
  return `${Math.floor(seconds / 3600)}h${minutes ? ` ${minutes}m` : ""}`;
}

function partyBuffChip(buff) {
  const duration = formatDuration(buff.seconds);
  return `<button class="buff-chip ${buff.seconds < 60 ? "expiring" : ""}" data-buff-id="${buff.id}"
    title="${buff.name} · ${duration} remaining" aria-label="${buff.name}, ${duration} remaining">
    ${art(buff.art)}<span class="buff-name">${buff.name}</span><span class="duration">${duration}</span>
  </button>`;
}

function partyBuffStrip() {
  const active = activePartyBuffs();
  const limit = buffLayout === "rows" ? 8 : 4;
  const hidden = Math.max(0, active.length - limit);
  return `<div class="buffs ${buffLayout}" aria-label="${active.length} active party buffs, soonest expiry first"
      ${active.length ? "" : "hidden"}>
    ${active.slice(0, limit).map(partyBuffChip).join("")}
    ${hidden ? `<button class="buff-more" data-action="buff-overflow" aria-expanded="false"
      aria-controls="buff-overflow-panel" aria-label="Show ${hidden} more active party buffs"
      title="${hidden} more active party buffs"><span class="stack-symbol" aria-hidden="true">◇</span>
      <strong>+${hidden}</strong><small>MORE</small></button>` : ""}
  </div>`;
}

function alertSigil(kind, muted = false) {
  return `<svg class="alert-sigil ${muted ? "unlit" : kind}" viewBox="0 0 28 30" aria-hidden="true">
    <path class="sigil-bezel" d="M14 1 26 15 14 29 2 15Z"/>
    <path class="sigil-core" d="M14 4 23 15 14 26 5 15Z"/>
    <path class="sigil-shine" d="M14 4 23 15H5Z"/>
    <path class="sigil-shadow" d="M14 15h9L14 26Z"/>
  </svg>`;
}

function previewStatusText() {
  const examples = {
    off: "", short: "Iron Sword", long: "Elara cannot cast this spell while she is recovering.",
    wrapped: "You cannot rest while enemies are nearby. Find a safe place, then make camp to restore your party’s health and spell points.",
    custom: customStatus,
  };
  return examples[statusPreview];
}

function art(name, className = "", alt = "") {
  if (params.get("buffArt") === "clean" && typeof glyphFreeBuff === "function") {
    const clipped = glyphFreeBuff(name, className, alt);
    if (clipped) return clipped;
  }
  return `<img class="${className}" src="assets/${name}.png" alt="${alt}" draggable="false">`;
}

function ornament() {
  return `<span class="ornament top" aria-hidden="true"><svg viewBox="0 0 116 24">
    <path d="M0 13h34l8-8h9l7-5 7 5h9l8 8h34M13 17h29l9-8h14l9 8h29M45 19l13-9 13 9M58 0v23"/>
    <path d="m53 11 5-5 5 5-5 5z"/></svg></span>`;
}

function personState(index) {
  const p = { ...people[index], condition: "Ready", recovering: false, incapacitated: false };
  if (sceneState === "combat") {
    p.hp = [84, 18, 62, 0, 154][index];
    p.sp = [20, 72, 24, 82, 9][index];
    if (index === 1) p.condition = "Low health";
    if (index === 2) { p.condition = "Recovering · 1.8s"; p.recovering = true; }
    if (index === 3) { p.condition = "Unconscious"; p.incapacitated = true; }
  }
  if (damageSample?.index === index) p.hp = damageSample.hp;
  return p;
}

function portrait(index, direction) {
  const p = personState(index);
  const hpPercent = Math.round(p.hp / p.maxHp * 100);
  const spPercent = Math.round(p.sp / p.maxSp * 100);
  const classes = ["pc", selected === index ? "selected" : "", p.recovering ? "recovering" : "",
    p.incapacitated ? "incapacitated" : "", hpPercent <= 50 ? "injured" : "", hpPercent <= 25 ? "critical" : ""];
  const readiness = p.recovering
    ? '<span class="recovery-arc"></span><span class="recovery-value">1.8</span>'
    : direction === "obsidian" ? alertSigil(sceneState, p.incapacitated)
    : p.incapacitated ? '<span class="condition-symbol">—</span>' : art(stateAssets[sceneState]);
  const condition = direction === "obsidian" && p.condition === "Ready" ? "" : p.condition;
  const label = `${p.name}. HP ${p.hp} of ${p.maxHp}. SP ${p.sp} of ${p.maxSp}. ${p.condition}. ${stateLabels[sceneState]}.`;
  const button = `<button class="${classes.join(" ")}" data-person="${index}" aria-label="${label}"
      aria-pressed="${selected === index}" title="${label} Click to select; double-click to inspect.">
    <span class="selection-mark" aria-hidden="true"></span>
    ${direction === "obsidian" ? "" : `<span class="pc-number">${index + 1}</span>`}
    <span class="portrait-frame">${art(p.art, "portrait", p.name)}</span>
    <span class="pc-name">${p.name}</span><span class="pc-state">${condition}</span>
    <span class="vitals" aria-hidden="true">
      <span class="meter hp" style="--fill:${hpPercent}%"><span>HP</span>
        <i class="damage-echo"></i><i class="fill"></i><em>${p.hp}/${p.maxHp}</em></span>
      <span class="meter sp" style="--fill:${spPercent}%"><span>SP</span><i class="fill"></i><em>${p.sp}/${p.maxSp}</em></span>
    </span>
    <span class="readiness" aria-hidden="true">${readiness}</span>
    ${index === 0 && direction !== "obsidian"
      ? `<span class="personal-buff" title="Bless — personal buff">${art("ib_spelico")}</span>` : ""}
  </button>`;
  if (direction !== "obsidian") return button;
  const effects = personalBuffs[index] || [];
  return `<div class="pc-slot">${button}${effects.length ?
    `<button class="personal-buff" data-personal-buffs="${index}" aria-expanded="false"
      aria-controls="personal-buffs-panel" aria-label="${p.name}: ${effects.length} active personal buff${effects.length === 1 ? "" : "s"}"
      title="${p.name} · inspect personal buffs">${art("generated/obsidian-personal-buffs-v1")}</button>` : ""}</div>`;
}

function hudMarkup(direction = concept) {
  const refined = direction === "obsidian";
  const commands = [
    ["books", "butn1u", "Books", "Open the existing journal and books"],
    ["reference", "butn3u", "Party", "Open the existing quick reference"],
    ["rest", "butn2u", "Rest", "Open the existing rest screen"],
    ["options", "butn4u", "Options", "Open the existing options screen"],
  ];
  const commandArt = { books: "books-v2", reference: "party-v1", rest: "rest-v1", options: "options-v1" };
  return `<div class="baseplate" aria-hidden="true"><div class="engraving"></div></div>
    <div class="resources panel" aria-label="Gold 10,027. Food 7">
      ${ornament()}
      <span class="resource">${art("scorebg_gold")}<strong>10,027</strong></span>
      <span class="resource-divider"></span>
      <span class="resource food">${art("scorebg_food")}<strong>7<small>food</small></strong></span>
    </div>
    ${refined ? (turnPhase ? `<button class="turn-dock" data-action="mode" aria-label="${phaseDetails[turnPhase]}">
      <span class="turn-dock-icon" aria-hidden="true">${turnPhase === 1 ? "◇" : turnPhase === 2 ? "››" : "◷"}</span>
      <span>${["", "Your turn", "Movement", "Waiting"][turnPhase]}
        <small>${["", "ATTACK", "3 STEPS LEFT", "ENEMY TURN"][turnPhase]}</small></span></button>` : "")
      : `<div class="world-state"><span class="threat-mark" aria-hidden="true"></span>
      <span class="threat-label">${stateLabels[sceneState]}</span>
      <button class="mode-button" data-action="mode" title="Preview real time, attack, movement and wait phases">
        <span class="turn-icon">${turnPhase ? "◷" : "▷"}</span>${phaseNames[turnPhase]}
      </button>
    </div>${turnPhase ? `<div class="turn-phase">${phaseDetails[turnPhase]}</div>` : ""}
    <div class="party-heading">The company <span>· ${partyCount}</span></div>`}
    <div class="party" aria-label="Party portraits">${Array.from({ length: partyCount }, (_, i) => portrait(i, direction)).join("")}</div>
    <div class="commands panel" aria-label="Game screens">${commands.map(([action, icon, text, label]) =>
      `<button class="command" data-action="${action}" title="${label}" aria-label="${label}">
        ${art(refined ? `generated/obsidian-${commandArt[action]}` : icon)}<span>${text}</span></button>`).join("")}</div>
    ${refined ? "" : `<div class="buff-totems" aria-label="Original buff tableaux">
      <button class="totem" data-action="buffs" title="Inspect body buffs" aria-label="Inspect body buffs">
        ${art("asil00")}${art("asil07")}${art("asil09")}<small>WARD</small>
      </button>
      <button class="totem" data-action="buffs" title="Inspect mind and utility buffs" aria-label="Inspect utility buffs">
        ${art("asir00")}${art("asir02")}<small>SIGHT</small>
      </button>
    </div>`}
    ${refined ? partyBuffStrip() : `<div class="buffs" aria-label="Active party buffs">${buffs.map((b, i) =>
      `<button class="buff-chip ${b.expiring ? "expiring" : ""}" data-buff="${i}"
        title="${b.name} · ${b.duration} remaining" aria-label="${b.name}, ${b.duration} remaining">
        ${art(b.art)}<span class="buff-name">${b.name}</span><span class="duration">${b.duration}</span>
      </button>`).join("")}</div>`}
    <div class="minimap panel" aria-label="New Sorpigal minimap">
      ${ornament()}<span class="map-label">New Sorpigal</span>
      <div class="map-viewport"><button class="map-open" data-action="map" title="Open full map" aria-label="Open full map">
        <img class="map-art" src="assets/new-sorpigal.bmp" alt="Original New Sorpigal minimap" style="--map-zoom:${mapZoom}">
        <span class="map-vignette"></span><span class="map-arrow" aria-hidden="true"></span>
      </button></div>
      <span class="map-north" aria-hidden="true">N</span>
      <div class="map-controls"><button data-zoom="-1" aria-label="Zoom minimap out" ${mapZoom <= .75 ? "disabled" : ""}>−</button>
        <span>ENROTH</span><button data-zoom="1" aria-label="Zoom minimap in" ${mapZoom >= 1.75 ? "disabled" : ""}>+</button>
      </div>
    </div>
    <button class="followers-button" data-action="followers" aria-expanded="false">
      ${art(refined ? "generated/obsidian-followers-v1" : "npcopenup")} Followers <span>2</span>
    </button>
    <div class="status-message" role="status">${refined ? escapeHtml(previewStatusText()) : ""}</div>
    <div class="popover-slot"></div>`;
}

function scaleStages() {
  $$(".stage-host, .mini-host").forEach(host => {
    if (document.fullscreenElement && host.classList.contains("stage-host")) {
      const width = Math.min(innerWidth, innerHeight * 16 / 9);
      host.style.width = `${width}px`;
      host.style.maxWidth = "none";
    } else {
      host.style.width = "";
      host.style.maxWidth = "";
    }
    const child = $(".stage", host);
    if (child) child.style.transform = `scale(${host.clientWidth / 1600})`;
  });
}

function setUrl() {
  const search = new URLSearchParams(location.search);
  search.set("concept", concept);
  search.set("state", sceneState);
  search.set("party", partyCount);
  $("#dusk").checked ? search.set("dusk", "1") : search.delete("dusk");
  $("#notes").checked ? search.set("notes", "1") : search.delete("notes");
  search.set("buffLayout", buffLayout);
  search.set("buffs", buffCount);
  search.set("bars", barStyle);
  search.set("status", statusPreview);
  search.set("turn", turnPhase);
  statusPreview === "custom" && customStatus ? search.set("text", customStatus) : search.delete("text");
  history.replaceState(null, "", `${location.pathname}?${search}`);
}

function renderComparison() {
  $("#comparison").innerHTML = Object.entries(concepts).filter(([key]) => key !== "current").map(([key, data]) =>
    `<figure><div class="mini-host"><div class="stage ${key} ${$("#dusk").checked ? "dusk" : ""}"
      data-state="${sceneState}" data-bars="${barStyle}" style="--roster-heading:${107 + partyCount * 110 + 11}px">
      <div class="scenery"></div><div class="ambient-shade"></div>${hudMarkup(key)}
      <div class="stage-caption">CONCEPT ${data.number} · ${data.name.toUpperCase()}</div>
    </div></div><figcaption><strong>${data.number} · ${data.name}</strong>
      <button data-open-concept="${key}">Inspect →</button></figcaption></figure>`).join("");
  $$("[data-open-concept]").forEach(button => button.addEventListener("click", () => {
    compareMode = false;
    concept = button.dataset.openConcept;
    render();
  }));
  // Thumbnails are visual comparisons. Their full-sized controls are available after Inspect.
  $$(".mini-host button").forEach(button => button.tabIndex = -1);
}

function render() {
  clearTimeout(messageTimer);
  damageTimers.forEach(clearTimeout);
  damageTimers = [];
  damageSample = null;
  const data = concepts[concept];
  selected = Math.min(selected, partyCount - 1);
  if (personState(selected).incapacitated) selected = 0;
  stage.className = `stage ${concept}${$("#dusk").checked ? " dusk" : ""}${$("#notes").checked ? " show-notes" : ""}`;
  stage.dataset.state = sceneState;
  stage.dataset.bars = barStyle;
  stage.dataset.buffLayout = buffLayout;
  stage.style.setProperty("--roster-heading", `${107 + partyCount * 110 + 11}px`);
  hud.innerHTML = hudMarkup();
  $("#stage-number").textContent = data.number;
  $("#direction-kicker").textContent = data.kicker;
  $("#direction-title").textContent = data.name;
  $("#direction-description").textContent = data.description;
  $("#direction-tradeoff").textContent = data.tradeoff;
  $("#review-hint").textContent = concept === "current"
    ? "Original reference image. The scene-state controls apply to the three proposed HUDs."
    : concept === "obsidian"
      ? "Click the portrait’s star jewel for personal buffs; +N shows more party effects. Try status text, two rows and Play damage."
      : "Click a portrait, inspect a buff, try the minimap zoom or change the combat state. All game statistics shown are examples.";
  $("#annotation-layer").innerHTML = data.annotations.map(note =>
    `<div class="annotation" style="left:${note.x}px;top:${note.y}px"><b>${note.title}</b>${note.text}</div>`).join("");
  $$("[data-concept]").forEach(button => {
    button.classList.toggle("active", button.dataset.concept === concept);
    button.setAttribute("aria-pressed", String(button.dataset.concept === concept));
  });
  $$("[data-state]").filter(button => button.tagName === "BUTTON").forEach(button =>
    button.setAttribute("aria-pressed", String(button.dataset.state === sceneState)));
  $("#party-count").value = String(partyCount);
  $("#buff-count").value = String(buffCount);
  $("#buff-layout").value = buffLayout;
  $("#bar-style").value = barStyle;
  $("#status-preview").value = statusPreview;
  $("#turn-preview").value = String(turnPhase);
  $("#custom-status").value = customStatus;
  $("#custom-status-control").hidden = statusPreview !== "custom";
  $("#refinement-controls").hidden = concept !== "obsidian" && !compareMode;
  $("#damage-demo").disabled = compareMode || concept !== "obsidian";
  document.body.classList.toggle("refining", concept === "obsidian" || compareMode);
  const referenceOnly = concept === "current" && !compareMode;
  $$("#state-controls button, #party-count, #dusk, #notes").forEach(control => control.disabled = referenceOnly);
  $("#stage-host").hidden = compareMode;
  $("#comparison").hidden = !compareMode;
  $("#compare").setAttribute("aria-pressed", String(compareMode));
  $("#compare").textContent = compareMode ? "Single view" : "Compare all";
  if (compareMode) renderComparison();
  wireHud();
  scaleStages();
  setUrl();
}

function showMessage(message) {
  if (concept === "obsidian" && statusPreview !== "off") return;
  clearTimeout(messageTimer);
  $(".status-message", hud).textContent = message;
  messageTimer = setTimeout(() => {
    if (statusPreview === "off") $(".status-message", hud).textContent = "";
  }, 4500);
}

function closePopover() {
  $(".popover-slot", hud).innerHTML = "";
  $(".followers-button", hud).setAttribute("aria-expanded", "false");
  $(".buff-more", hud)?.setAttribute("aria-expanded", "false");
  $$("[data-personal-buffs]", hud).forEach(button => button.setAttribute("aria-expanded", "false"));
  if (returnFocus?.isConnected) returnFocus.focus({ preventScroll: true });
  returnFocus = null;
}

function showPopover(title, content, className = "") {
  if (!$(".preview-popover", hud)) returnFocus = document.activeElement;
  $(".buff-more", hud)?.setAttribute("aria-expanded", "false");
  $(".followers-button", hud).setAttribute("aria-expanded", "false");
  $$("[data-personal-buffs]", hud).forEach(button => button.setAttribute("aria-expanded", "false"));
  $(".popover-slot", hud).innerHTML = `<section class="preview-popover ${className}" role="dialog"
      aria-label="${title}" aria-modal="false"><button class="popover-close" aria-label="Close">×</button>
      <h2>${title}</h2>${content}</section>`;
  $(".popover-close", hud).addEventListener("click", closePopover);
  $(".popover-close", hud).focus({ preventScroll: true });
}

function showBuffOverflow() {
  if ($("#buff-overflow-panel", hud)) { closePopover(); return; }
  const active = activePartyBuffs();
  const hidden = active.slice(buffLayout === "rows" ? 8 : 4);
  showPopover(`${hidden.length} more enchantments`,
    `<small>${active.length} active · soonest expiry first</small>
    <div class="buff-overflow-grid">${hidden.map(buff => `<button class="buff-overflow-entry"
      data-inspect-buff="${buff.id}" title="Inspect ${buff.name}">${art(buff.art)}
      <span><b>${buff.name}</b><small>${formatDuration(buff.seconds)} remaining</small></span></button>`).join("")}</div>`,
    `buff-overflow-popup ${buffLayout}`);
  $(".preview-popover", hud).id = "buff-overflow-panel";
  $(".buff-more", hud)?.setAttribute("aria-expanded", "true");
  $$("[data-inspect-buff]", hud).forEach(button => button.addEventListener("click", () =>
    inspectPartyBuff(button.dataset.inspectBuff, true)));
}

function inspectPartyBuff(id, fromOverflow = false) {
  const buff = partyBuffCatalog.find(entry => entry.id === id);
  showPopover(buff.name, `<div class="buff-detail-row">${art(buff.art)}
    <span>${formatDuration(buff.seconds)} remaining · party effect</span></div><p>${buff.detail}</p>
    ${fromOverflow ? '<button class="buff-back" data-action="back-to-buffs">← More enchantments</button>' : ""}
    <small>Example duration · existing spell icon</small>`, `buff-detail-popup ${buffLayout}`);
  $("[data-action='back-to-buffs']", hud)?.addEventListener("click", showBuffOverflow);
}

function playDamage() {
  if (concept !== "obsidian") return;
  damageTimers.forEach(clearTimeout);
  damageSample = null;
  render();
  const index = selected;
  const person = personState(index);
  if (person.incapacitated) return;
  const hp = Math.max(1, person.hp - Math.round(person.maxHp * .22));
  damageSample = { index, hp };
  const button = $(`[data-person="${index}"]`, hud);
  const meter = $(".meter.hp", button);
  const echo = $(".damage-echo", meter);
  const before = Math.round(person.hp / person.maxHp * 100);
  const after = Math.round(hp / person.maxHp * 100);
  echo.style.transition = "none";
  echo.style.width = `${before}%`;
  echo.classList.add("visible");
  // Read layout once so the existing fill interpolates to the new, authoritative value.
  meter.getBoundingClientRect();
  echo.style.transition = "";
  meter.style.setProperty("--fill", `${after}%`);
  button.classList.toggle("injured", after <= 50);
  button.classList.toggle("critical", after <= 25);
  button.classList.add("damage-hit");
  button.setAttribute("aria-label", `${person.name}. HP ${hp} of ${person.maxHp}. SP ${person.sp} of ${person.maxSp}.`);
  button.title = `${person.name}. HP ${hp} of ${person.maxHp}. SP ${person.sp} of ${person.maxSp}.`;
  $("em", meter).textContent = `${hp}/${person.maxHp}`;
  if (after <= 25) $(".pc-state", button).textContent = "Low health";
  showMessage(`${person.name} takes ${person.hp - hp} damage.`);
  damageTimers.push(setTimeout(() => { echo.style.width = `${after}%`; }, 250));
  damageTimers.push(setTimeout(() => { echo.classList.remove("visible"); button.classList.remove("damage-hit"); }, 1150));
  damageTimers.push(setTimeout(render, 3600));
}

function buffRows() {
  return buffs.map(b => `<div class="buff-detail-row">${art(b.art)}<div><b>${b.name}</b>
    <span>${b.duration} remaining${b.expiring ? " · expiring soon" : ""}</span></div></div>`).join("");
}

function inspectPerson(index) {
  const p = personState(index);
  showPopover(p.name, `<p>Health <strong>${p.hp} / ${p.maxHp}</strong><br>
    Spell points <strong>${p.sp} / ${p.maxSp}</strong><br>${p.condition}${index === 0 ? " · Bless active" : ""}</p>
    <p>Double-clicking this portrait hands off to the existing character screen. Portrait expressions,
    spell flashes and condition overlays keep their current runtime sources.</p><small>Example character data · HUD proposal only</small>`);
}

function inspectPersonalBuffs(index, button) {
  if ($("#personal-buffs-panel", hud)?.dataset.owner === String(index)) { closePopover(); return; }
  const effects = personalBuffs[index] || [];
  showPopover(`${people[index].name} · enchantments`,
    effects.map(effect => `<div class="buff-detail-row">${art(effect.art)}<div><b>${effect.name}</b>
      <span>${formatDuration(effect.seconds)} remaining</span></div></div><p>${effect.detail}</p>`).join("") +
    '<small>Personal effects · example duration</small>', "personal-buffs-popup");
  const panel = $(".preview-popover", hud);
  panel.id = "personal-buffs-panel";
  panel.dataset.owner = String(index);
  button.setAttribute("aria-expanded", "true");
}

function wireHud() {
  $$("[data-personal-buffs]", hud).forEach(button => button.addEventListener("click", () =>
    inspectPersonalBuffs(Number(button.dataset.personalBuffs), button)));
  $$("[data-person]", hud).forEach(button => {
    const index = Number(button.dataset.person);
    button.addEventListener("click", () => {
      const person = personState(index);
      if (person.incapacitated || person.recovering) {
        showMessage(`${person.name} is ${person.incapacitated ? "unconscious" : "recovering"}. Inspect the portrait for details.`);
        return;
      }
      selected = index;
      $$("[data-person]", hud).forEach(other => {
        other.classList.toggle("selected", Number(other.dataset.person) === selected);
        other.setAttribute("aria-pressed", String(Number(other.dataset.person) === selected));
      });
      showMessage(`${person.name} selected · ${person.hp}/${person.maxHp} HP · ${person.sp}/${person.maxSp} SP`);
    });
    button.addEventListener("dblclick", () => inspectPerson(index));
    button.addEventListener("contextmenu", event => { event.preventDefault(); inspectPerson(index); });
  });
  $$("[data-buff]", hud).forEach(button => button.addEventListener("click", () => {
    const b = buffs[Number(button.dataset.buff)];
    showPopover(b.name, `<div class="buff-detail-row">${art(b.art)}<span>${b.duration} remaining · party effect</span></div>
      <p>${b.detail}</p><small>Example duration · original spell icon</small>`);
  }));
  $$("[data-buff-id]", hud).forEach(button => button.addEventListener("click", () =>
    inspectPartyBuff(button.dataset.buffId)));
  $$("[data-zoom]", hud).forEach(button => button.addEventListener("click", () => {
    mapZoom = Math.max(.75, Math.min(1.75, mapZoom + Number(button.dataset.zoom) * .25));
    $(".map-art", hud).style.setProperty("--map-zoom", mapZoom);
    $("[data-zoom='-1']", hud).disabled = mapZoom <= .75;
    $("[data-zoom='1']", hud).disabled = mapZoom >= 1.75;
  }));
  $$("[data-action]", hud).forEach(button => button.addEventListener("click", () => {
    const action = button.dataset.action;
    if (action === "mode") {
      turnPhase = (turnPhase + 1) % 4;
      render();
      const modeButton = $(".mode-button, .turn-dock", hud) || $("#turn-preview");
      modeButton.focus({ preventScroll: true });
      return;
    }
    if (action === "buff-overflow") { showBuffOverflow(); return; }
    if (action === "buffs") {
      const rows = concept === "obsidian" ? activePartyBuffs().map(buff =>
        `<div class="buff-detail-row">${art(buff.art)}<div><b>${buff.name}</b>
        <span>${formatDuration(buff.seconds)} remaining</span></div></div>`).join("") : buffRows();
      showPopover("Active enchantments", `<div class="all-buffs-list">${rows || "<p>No active party buffs.</p>"}</div>` +
        '<p>Personal effects remain with their character. Party effects appear once in the shared strip.</p>');
      return;
    }
    if (action === "map") {
      showPopover("New Sorpigal", '<img src="assets/new-sorpigal.bmp" alt="Full original New Sorpigal map">' +
        '<small>Original MM6 map art · full map preview; runtime journal map stays as it is</small>', "full-map");
      return;
    }
    if (action === "followers") {
      showPopover("Your companions", `<div class="buff-detail-row">${art("follower-1")}<div><b>Hireling I</b>
        <span>Talk · profession · services</span></div></div><div class="buff-detail-row">${art("follower-2")}
        <div><b>Hireling II</b><span>Talk · profession · services</span></div></div>
        <p>The follower panel keeps its own slots and scrolling; these stay separate from the playable party.</p>
        <small>Example follower portraits · existing dialogue unchanged</small>`);
      button.setAttribute("aria-expanded", "true");
      return;
    }
    const screens = { books: ["Books & journal", "journal"], reference: ["Party reference", "quick-reference"],
      rest: ["Make camp", "rest"], options: ["Options", "options"] };
    const [title, screenName] = screens[action];
    showPopover(title, `<p>This control opens the existing ${screenName} screen. Its artwork and layout stay as they are.</p>
      ${action === "rest" && sceneState !== "explore" ? '<p><strong>Enemies nearby:</strong> the existing safe-rest restrictions still apply.</p>' : ""}
      <small>Navigation handoff · visual mockup</small>`);
  }));
}

$$("[data-concept]").forEach(button => button.addEventListener("click", () => {
  concept = button.dataset.concept;
  compareMode = false;
  render();
}));
$$("#state-controls button").forEach(button => button.addEventListener("click", () => {
  sceneState = button.dataset.state;
  render();
}));
$("#party-count").addEventListener("change", event => { partyCount = Number(event.target.value); render(); });
$("#buff-layout").addEventListener("change", event => { buffLayout = event.target.value; render(); });
$("#buff-count").addEventListener("change", event => { buffCount = Number(event.target.value); render(); });
$("#bar-style").addEventListener("change", event => { barStyle = event.target.value; render(); });
$("#status-preview").addEventListener("change", event => { statusPreview = event.target.value; render(); });
$("#turn-preview").addEventListener("change", event => { turnPhase = Number(event.target.value); render(); });
$("#damage-demo").addEventListener("click", playDamage);
$("#custom-status").addEventListener("input", event => {
  customStatus = event.target.value;
  $(".status-message", hud).textContent = customStatus;
  if (compareMode) renderComparison();
  setUrl();
});
$("#dusk").checked = params.get("dusk") === "1";
$("#notes").checked = params.get("notes") === "1";
$("#dusk").addEventListener("change", render);
$("#notes").addEventListener("change", render);
$("#compare").addEventListener("click", () => { compareMode = !compareMode; render(); });
$("#fullscreen").addEventListener("click", async () => {
  if (document.fullscreenElement) await document.exitFullscreen();
  else await $("#presentation").requestFullscreen();
});
document.addEventListener("fullscreenchange", scaleStages);
window.addEventListener("resize", scaleStages);
document.addEventListener("keydown", event => {
  if (event.key === "Escape") closePopover();
});
stage.addEventListener("pointerdown", event => {
  if (!event.target.closest("button, .preview-popover") && $(".preview-popover", hud)) closePopover();
});
if (params.get("export") === "1") document.body.classList.add("export");
render();
new ResizeObserver(scaleStages).observe($("#stage-host"));
