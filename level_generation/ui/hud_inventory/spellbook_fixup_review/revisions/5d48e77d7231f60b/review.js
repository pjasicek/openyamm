"use strict";

const data = window.SPELLBOOK_REVIEW_DATA;
const $ = (id) => document.getElementById(id);
const canvas = $("book");
const context = canvas.getContext("2d");
const detailContext = $("detail").getContext("2d");
const images = new Map();
const storageKey = "openyamm-spellbook-fixup-" + data.revision;
const approvedDecisions = Object.fromEntries(data.approval.targets.map(id => [id, {
  decision: "approve", note: "Approved in conversation on " + data.approval.date + ".",
  updatedAt: data.approval.date, source: "conversation", approvalRevision: data.approval.revision,
}]));
const params = new URLSearchParams(location.search);
const state = {
  school: data.schools.find(s => s.key.toLowerCase() === (params.get("school") || "fire").toLowerCase()) || data.schools[0],
  mode: params.get("mode") === "installed" ? "installed" : "proposed",
  pointer: null, down: false, pressed: null, selected: null, quick: null, attack: null,
  closed: false, backgroundOnly: false, target: null, detailHighlight: false, alternateTimer: null,
  decisions: {}, ready: false, lastClick: null,
};

try {
  const saved = JSON.parse(localStorage.getItem(storageKey) || "{}");
  if (saved && typeof saved === "object" && !Array.isArray(saved)) state.decisions = saved;
} catch {
  $("saveStatus").textContent = "Saved review could not be read. Export new notes to preserve them.";
}

const schoolName = school => school.name;
const allTargets = new Map();
for (const school of data.schools) {
  allTargets.set(school.id, {kind: "page", item: school, school, name: schoolName(school) + " background"});
  allTargets.set(school.button.id, {kind: "school", item: school.button, school, name: schoolName(school) + " school button"});
  for (const spell of school.spells) allTargets.set(spell.id, {kind: "spell", item: spell, school, name: spell.name});
}
for (const control of data.controls) allTargets.set(control.id, {kind: "control", item: control, name: control.name});

function imageFor(artifact) {return images.get(artifact.path);}
function contains(rect, point) {
  return point && point.x >= rect.x && point.y >= rect.y && point.x < rect.x + rect.width && point.y < rect.y + rect.height;
}
function hitTarget(point) {
  for (const school of data.schools) if (contains(school.button.rect, point)) return allTargets.get(school.button.id);
  for (const control of data.controls) if (contains(control.rect, point)) return allTargets.get(control.id);
  if (!state.backgroundOnly) for (const spell of state.school.spells) if (contains(spell.rect, point)) return allTargets.get(spell.id);
  return null;
}
function buttonStates(item) {
  return state.mode === "proposed" && item.proposedStates ? item.proposedStates : item.states;
}
function stateArtifact(item, active = false) {
  const states = buttonStates(item);
  if (active) return states.pressed || states.highlighted || states.default;
  if (contains(item.rect, state.pointer)) {
    return (state.down ? states.pressed : states.highlighted) || states.default;
  }
  return states.default;
}
function spellArtifact(spell, highlighted) {
  return state.mode === "installed"
    ? (highlighted ? spell.states.highlighted : spell.states.default)
    : (highlighted ? spell.canonical : spell.proposedNormal);
}
function drawImage(artifact, rect, targetContext = context) {
  const image = imageFor(artifact);
  if (image) targetContext.drawImage(image, rect.x, rect.y, rect.width, rect.height);
}
function draw() {
  if (!state.ready) return;
  context.setTransform(2, 0, 0, 2, 0, 0);
  context.clearRect(0, 0, 640, 480);
  drawImage(state.school[state.mode], {x: 0, y: 0, width: 640, height: 480});
  // Keep the game renderer's draw order, including overlapping spell rectangles.
  for (const school of data.schools) drawImage(stateArtifact(school.button, school === state.school), school.button.rect);
  for (const control of data.controls) drawImage(stateArtifact(control), control.rect);
  if (!state.backgroundOnly) for (const spell of state.school.spells) {
    const highlighted = spell.id === state.selected || contains(spell.rect, state.pointer);
    drawImage(spellArtifact(spell, highlighted), spell.rect);
  }
  const selected = allTargets.get(state.selected);
  for (const label of data.labels) {
    const text = label.id === "SpellbookCasterName" ? "Ariel" : selected ? "Select " + selected.name : "";
    if (!text) continue;
    context.font = "17px BookLucida";
    context.textBaseline = "middle";
    context.textAlign = label.text.align_x;
    const x = label.rect.x + (label.text.align_x === "right" ? label.rect.width : 0);
    const y = label.rect.y + label.rect.height / 2;
    context.fillStyle = "#fff";
    context.fillText(text, x + 1, y + 1);
    context.fillStyle = "#28180c";
    context.fillText(text, x, y);
  }
}

function drawDetail() {
  if (!state.ready || !state.target) return;
  const target = allTargets.get(state.target);
  const item = target.item;
  detailContext.setTransform(1, 0, 0, 1, 0, 0);
  detailContext.fillStyle = "#cfb580";
  detailContext.fillRect(0, 0, 520, 360);
  if (target.kind === "page") {
    drawImage(item[state.mode], {x: 20, y: 0, width: 480, height: 360}, detailContext);
    $("detailLabel").textContent = state.mode === "proposed" ? "Shared book and medallion frame" : "Installed page";
  } else if (target.kind === "spell") {
    // Show an actual page crop, with the same declared draw rectangle in each state.
    const rect = item.rect;
    const scale = Math.min(480 / rect.width, 324 / rect.height, 2.4);
    const x = (520 - rect.width * scale) / 2, y = (360 - rect.height * scale) / 2;
    detailContext.save();
    detailContext.beginPath(); detailContext.rect(x - 12, y - 12, rect.width * scale + 24, rect.height * scale + 24); detailContext.clip();
    detailContext.translate(x - rect.x * scale, y - rect.y * scale);
    detailContext.scale(scale, scale);
    drawImage(target.school[state.mode], {x: 0, y: 0, width: 640, height: 480}, detailContext);
    drawImage(spellArtifact(item, state.detailHighlight), rect, detailContext);
    detailContext.restore();
    $("detailLabel").textContent = state.detailHighlight ? "Highlighted / selected" : "Normal";
  } else {
    const states = buttonStates(item);
    const artifact = state.detailHighlight ? states.pressed || states.highlighted : states.default;
    const scale = Math.min(260 / item.rect.width, 300 / item.rect.height, 5);
    drawImage(artifact, {x: (520 - item.rect.width * scale) / 2, y: (360 - item.rect.height * scale) / 2,
                         width: item.rect.width * scale, height: item.rect.height * scale}, detailContext);
    $("detailLabel").textContent = state.detailHighlight ? "Pressed / active" : "Normal / hovered";
  }
}

function fit() {
  const viewport = $("stageViewport");
  const mobile = window.innerWidth <= 780;
  let scale = Number($("zoom").value);
  if ($("zoom").value === "fit") {
    scale = Math.min(2, (viewport.clientWidth - 2) / 640,
      mobile ? 2 : (viewport.clientHeight - 2) / 480);
  }
  $("bookFrame").style.width = Math.max(100, 640 * scale) + "px";
  $("bookFrame").style.height = Math.max(75, 480 * scale) + "px";
}
function saveDecisions() {
  try {
    localStorage.setItem(storageKey, JSON.stringify(state.decisions));
    $("saveStatus").textContent = "Saved in this browser";
  } catch {
    $("saveStatus").textContent = "Browser storage unavailable — export to keep your review";
  }
}
function refreshDecision() {
  const decisions = {...approvedDecisions, ...state.decisions};
  const decision = decisions[state.target] || {};
  $("decisionState").textContent = decision.decision === "approve" ? "Looks good"
    : decision.decision === "flag" ? "Needs work" : "Unreviewed";
  $("decisionState").className = "badge " + (decision.decision === "approve" ? "good" : decision.decision === "flag" ? "flag" : "");
  $("approve").setAttribute("aria-pressed", String(decision.decision === "approve"));
  $("flag").setAttribute("aria-pressed", String(decision.decision === "flag"));
  $("note").value = decision.note || "";
  const values = Object.values(decisions);
  const reviewed = values.filter(d => d.decision).length;
  const flagged = values.filter(d => d.decision === "flag").length;
  $("progress").textContent = reviewed + " / " + allTargets.size + " reviewed" + (flagged ? " · " + flagged + " flagged" : "");
}
function selectTarget(id) {
  state.target = id;
  const target = allTargets.get(id);
  $("reviewTarget").value = id;
  $("targetName").textContent = target.name;
  $("targetDescription").textContent = target.kind === "page" ? "Check the paper, borders and school medallion while switching schools."
    : target.kind === "spell" ? "Check the drawing and glyphs as the colour changes. Hover the detail below, or alternate its states."
    : target.kind === "school" ? "One parchment bookmark and circular frame, with the retained school emblem. Hover the detail to see the selected state."
    : "Installed button artwork, shown with the game’s normal and pressed states.";
  $("alternate").hidden = target.kind === "page";
  state.detailHighlight = false;
  refreshDecision(); drawDetail();
}
function targetOptions() {
  $("reviewTarget").replaceChildren();
  const targets = [allTargets.get(state.school.id), allTargets.get(state.school.button.id),
    ...state.school.spells.map(spell => allTargets.get(spell.id)), ...data.controls.map(item => allTargets.get(item.id))];
  for (const target of targets) {
    const option = new Option(target.name, target.item.id);
    $("reviewTarget").add(option);
  }
}
function selectSchool(key) {
  state.school = data.schools.find(school => school.key === key);
  state.selected = null; state.pointer = null; state.down = false; state.pressed = null;
  $("schoolSelect").value = key;
  targetOptions(); selectTarget(state.school.button.id); draw();
  status(state.school.name + (state.school.key === "DarkElf" || state.school.key === "Dragon" || state.school.key === "Vampire" ? " abilities" : " magic"));
}
function mode(value) {
  state.mode = value;
  $("proposedMode").setAttribute("aria-pressed", String(value === "proposed"));
  $("installedMode").setAttribute("aria-pressed", String(value === "installed"));
  $("modeCaption").textContent = value === "proposed" ? "PROPOSED · One parchment bookmark, twelve emblems" : "INSTALLED · Existing page and icon pairs";
  draw(); drawDetail();
}
function status(text) {$("hoverStatus").textContent = text;}
function closeBook(message = "Spellbook closed") {
  state.closed = true; state.pointer = null; state.down = false; state.pressed = null;
  $("closedMessage").textContent = message; $("closedOverlay").hidden = false; draw();
}
function activate(target) {
  if (!target) {state.selected = null; draw(); return;}
  if (target.kind === "school") {selectSchool(target.school.key); return;}
  if (target.kind === "spell") {
    const now = performance.now();
    const doubleClick = state.lastClick?.id === target.item.id && now - state.lastClick.time <= 350;
    state.lastClick = {id: target.item.id, time: now};
    state.selected = target.item.id;
    selectTarget(target.item.id); status("Selected: " + target.name);
    if (doubleClick) closeBook("Cast " + target.name + " — preview");
    draw(); return;
  }
  selectTarget(target.item.id);
  if (target.item.id === "SpellbookCloseButton") {closeBook(); return;}
  const field = target.item.id === "SpellbookQuickCastButton" ? "quick" : "attack";
  const name = field === "quick" ? "Quick" : "Attack";
  if (!state.selected || state[field] === state.selected) {
    state[field] = null; state.selected = null; status(name + " spell cleared");
  } else {state[field] = state.selected; status(name + " spell set to " + allTargets.get(state.selected).name);}
  $(field + "Assignment").textContent = name + " spell: " + (state[field] ? allTargets.get(state[field]).name : "—");
  draw();
}
function pointFor(event) {
  const rect = canvas.getBoundingClientRect();
  return {x: (event.clientX - rect.left) * 640 / rect.width, y: (event.clientY - rect.top) * 480 / rect.height};
}
canvas.addEventListener("pointermove", event => {
  if (state.closed) return;
  state.pointer = pointFor(event);
  const target = hitTarget(state.pointer);
  canvas.style.cursor = target ? "pointer" : "default";
  status(target ? target.name : state.school.name + " spellbook");
  draw();
});
canvas.addEventListener("pointerleave", () => {state.pointer = null; draw();});
canvas.addEventListener("pointerdown", event => {
  if (state.closed || event.button !== 0) return;
  state.pointer = pointFor(event); state.down = true; state.pressed = hitTarget(state.pointer)?.item.id || null;
  canvas.setPointerCapture(event.pointerId); canvas.focus({preventScroll: true}); draw();
});
canvas.addEventListener("pointerup", event => {
  if (event.button !== 0 || state.closed) return;
  state.pointer = pointFor(event);
  const target = hitTarget(state.pointer);
  const clicked = (target?.item.id || null) === state.pressed;
  state.down = false; state.pressed = null;
  if (canvas.hasPointerCapture(event.pointerId)) canvas.releasePointerCapture(event.pointerId);
  if (clicked) activate(target);
  draw();
});
canvas.addEventListener("pointercancel", () => {state.down = false; state.pressed = null; state.pointer = null; draw();});
canvas.addEventListener("contextmenu", event => {
  event.preventDefault();
  const target = hitTarget(pointFor(event));
  if (target?.kind === "school" && target.school !== state.school) {
    selectSchool(target.school.key);
  }
  selectTarget(target?.item.id || state.school.id);
});
$("detail").addEventListener("pointerenter", () => {state.detailHighlight = true; drawDetail();});
$("detail").addEventListener("pointerleave", () => {state.detailHighlight = false; drawDetail();});
$("alternate").addEventListener("click", () => {
  if (state.alternateTimer) {clearInterval(state.alternateTimer); state.alternateTimer = null;}
  else state.alternateTimer = setInterval(() => {state.detailHighlight = !state.detailHighlight; drawDetail();}, 650);
  $("alternate").textContent = state.alternateTimer ? "Stop" : "Alternate";
});
$("proposedMode").onclick = () => mode("proposed");
$("installedMode").onclick = () => mode("installed");
$("schoolSelect").onchange = event => selectSchool(event.target.value);
$("zoom").onchange = fit;
$("backgroundOnly").onchange = event => {state.backgroundOnly = event.target.checked; draw();};
$("clearSelection").onclick = () => {state.selected = null; draw(); status("Selection cleared");};
$("focusMode").onclick = () => {
  document.body.classList.toggle("focus");
  $("focusMode").textContent = document.body.classList.contains("focus") ? "Show review" : "Focus view";
  fit();
};
$("reopen").onclick = () => {state.closed = false; $("closedOverlay").hidden = true; canvas.focus(); draw();};
$("reviewTarget").onchange = event => selectTarget(event.target.value);
for (const [id, decision] of [["approve", "approve"], ["flag", "flag"]]) $(id).onclick = () => {
  state.decisions[state.target] = {...state.decisions[state.target], decision, note: $("note").value, updatedAt: new Date().toISOString()};
  saveDecisions(); refreshDecision();
};
$("note").oninput = () => {
  state.decisions[state.target] = {...state.decisions[state.target], note: $("note").value, updatedAt: new Date().toISOString()};
  saveDecisions();
};
$("resetDecision").onclick = () => {delete state.decisions[state.target]; saveDecisions(); refreshDecision();};
function reviewExport() {
  return {schema: 1, kind: "spellbook_fixup_review", revision: data.revision,
    exportedAt: new Date().toISOString(), layout: data.sourceLayout, recipe: data.recipe,
    approval: data.approval,
    decisions: Object.fromEntries(Object.entries({...approvedDecisions, ...state.decisions}).map(([id, decision]) => {
      const target = allTargets.get(id);
      return [id, {...decision, name: target.name, kind: target.kind,
        artwork: target.kind === "page" ? {installed: target.item.installed, proposed: target.item.proposed}
          : target.kind === "spell" ? {canonical: target.item.canonical, proposedNormal: target.item.proposedNormal,
              glyphMask: target.item.glyphMask, normalPalette: target.item.normalPalette}
          : target.kind === "school" ? {installed: target.item.states, proposed: target.item.proposedStates,
              emblems: target.item.emblems, master: data.bookmarks.master, mask: data.bookmarks.emblemMask}
          : target.item.states}];
    }))};
}
$("exportReview").onclick = () => {
  const blob = new Blob([JSON.stringify(reviewExport(), null, 2) + "\n"], {type: "application/json"});
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a"); anchor.href = url;
  anchor.download = "spellbook-review-" + data.revision + ".json"; anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
};
$("importReview").onchange = async event => {
  const file = event.target.files[0]; if (!file) return;
  try {
    const incoming = JSON.parse(await file.text());
    if (incoming.kind !== "spellbook_fixup_review" || incoming.revision !== data.revision) {
      throw new Error("This review belongs to a different artwork revision.");
    }
    const valid = {};
    for (const [id, decision] of Object.entries(incoming.decisions || {})) {
      if (!allTargets.has(id) || !decision || typeof decision !== "object"
        || (decision.decision && !["approve", "flag"].includes(decision.decision))
        || (decision.note !== undefined && typeof decision.note !== "string")) throw new Error("Invalid review entry.");
      valid[id] = {decision: decision.decision, note: decision.note || "", updatedAt: decision.updatedAt || ""};
    }
    for (const [id, decision] of Object.entries(valid)) {
      if (!state.decisions[id] || (decision.updatedAt || "") >= (state.decisions[id].updatedAt || "")) state.decisions[id] = decision;
    }
    saveDecisions(); refreshDecision(); status("Review imported.");
  } catch (error) {status("Import failed: " + error.message);}
  event.target.value = "";
};
document.addEventListener("keydown", event => {
  if (["INPUT", "TEXTAREA", "SELECT"].includes(event.target.tagName) || event.ctrlKey || event.metaKey || event.altKey) return;
  if (event.key.toLowerCase() === "b") {mode(state.mode === "proposed" ? "installed" : "proposed"); event.preventDefault();}
  if (event.key === "Escape") {closeBook(); event.preventDefault();}
  if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
    const index = data.schools.indexOf(state.school);
    selectSchool(data.schools[(index + (event.key === "ArrowRight" ? 1 : -1) + data.schools.length) % data.schools.length].key);
    event.preventDefault();
  }
});
new ResizeObserver(fit).observe($("stageViewport"));
window.addEventListener("resize", fit);

async function initialize() {
  for (const school of data.schools) $("schoolSelect").add(new Option(school.name, school.key));
  $("schoolSelect").value = state.school.key;
  $("revision").textContent = "Candidate " + data.revision + " · 12 schools / 111 spells";
  $("previousPreview").href = data.previousPreview;
  targetOptions(); selectTarget(state.school.button.id); mode(state.mode); fit();
  const paths = new Set();
  for (const school of data.schools) {
    paths.add(school.installed.path); paths.add(school.proposed.path);
    for (const artifact of Object.values(school.button.states)) paths.add(artifact.path);
    for (const artifact of Object.values(school.button.proposedStates)) paths.add(artifact.path);
    for (const spell of school.spells) {
      for (const artifact of Object.values(spell.states)) paths.add(artifact.path);
      paths.add(spell.proposedNormal.path);
    }
  }
  for (const control of data.controls) for (const artifact of Object.values(control.states)) paths.add(artifact.path);
  await Promise.all([...paths].map(path => new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => {images.set(path, image); resolve();};
    image.onerror = () => reject(new Error("Could not load " + path));
    image.src = path;
  })));
  await document.fonts.load("17px BookLucida");
  state.ready = true;
  $("loading").hidden = true;
  draw(); drawDetail();
}

// Exposed state supports a small, real-browser interaction and rendering audit.
window.spellbookReview = {state, data, selectSchool, selectTarget, mode, draw, drawDetail, reviewExport, hitTarget};
initialize().catch(error => {$("loading").textContent = error.message; console.error(error);});
