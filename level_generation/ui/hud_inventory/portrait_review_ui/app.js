"use strict";
const data = window.PORTRAITS;
const $ = id => document.getElementById(id);
const storageKey = "openyamm-portrait-transparent-v2-feedback";
let votes = {}, current = null, timer = null, generation = 0;
try { votes = JSON.parse(localStorage.getItem(storageKey) || "{}"); }
catch { $("notice").textContent = "Local storage unavailable; export feedback before closing."; }
const keyFor = f => `${f.id}:${f.attempts.find(a => a.id === f.selected)?.raw_sha256 || "none"}`;
const attemptFor = f => f.attempts.find(a => a.id === f.selected);
function persist() {
  try { localStorage.setItem(storageKey, JSON.stringify(votes)); }
  catch { $("notice").textContent = "Cannot save locally. Export feedback before closing."; }
}
function list() {
  const query = $("search").value.toLowerCase();
  $("families").replaceChildren();
  for (const family of data.families) {
    if (!$("unfinished").checked && family.state !== "ready_for_user") continue;
    if (!JSON.stringify([family.id, family.characters]).toLowerCase().includes(query)) continue;
    const button = document.createElement("button");
    const vote = votes[keyFor(family)];
    button.textContent = family.id + (vote ? ` · ${vote.verdict}` : "");
    const label = document.createElement("small"); label.textContent = family.state;
    button.append(label); button.classList.toggle("active", current?.id === family.id);
    button.onclick = () => select(family); $("families").append(button);
  }
  if (!$("families").children.length) $("families").textContent = "No ready families yet. Enable unfinished to inspect progress.";
}
function stop() { clearInterval(timer); timer = null; $("play").textContent = "Play numeric sequence"; }
function select(family) {
  stop(); current = family; generation++; $("frame").value = 1;
  $("title").textContent = family.prefix;
  $("status").textContent = `${family.state}\n${family.characters.map(c => `Character ${c.character_id}: ${c.notes || ""}`).join("; ")}`;
  if (family.state !== "ready_for_user") $("status").textContent += "\nUNFINISHED: not yet offered for aesthetic acceptance.";
  const vote = votes[keyFor(family)] || {};
  $("notes").value = vote.notes || "";
  for (const button of document.querySelectorAll("[data-vote]")) {
    button.disabled = family.state !== "ready_for_user";
    button.setAttribute("aria-pressed", String(vote.verdict === button.dataset.vote));
  }
  $("notes").disabled = family.state !== "ready_for_user";
  const attempt = attemptFor(family);
  $("links").replaceChildren();
  function link(text, href) { const a = document.createElement("a"); a.textContent = text; a.href = href; a.target = "_blank"; a.rel = "noopener"; $("links").append(a); }
  link("Previous family gallery", `../portrait_families/${family.id}/index.html`);
  if (attempt) {
    if (attempt.master_paths) {
      for (const [i, path] of attempt.master_paths.entries()) {
        const half = i === 0 ? "A" : "B";
        link(`Full-resolution master ${half}`, `${family.id}/${path}`);
        link(`Measurements ${half}`, `${family.id}/${path.replace("raw.png", "checks.json")}`);
      }
      if (family.state === "ready_for_user" || family.state === "technical_hold") link("Visual technical review", `${family.id}/technical_review.json`);
    } else {
      link("Full-resolution master", `${family.id}/${attempt.id}/raw.png`);
      link("Technical measurements", `${family.id}/${attempt.id}/checks.json`);
      if (family.state === "ready_for_user" || family.state === "technical_hold") link("Visual technical review", `${family.id}/${attempt.id}/review.json`);
    }
    $("sheet").src = `${family.id}/${attempt.id}/contact_x2.png`; $("sheet").hidden = false;
  } else { $("sheet").removeAttribute("src"); $("sheet").hidden = true; }
  $("evidence").textContent = JSON.stringify({state:family.state, reason:family.reason, attempt, references:family.references, native_only_reference_cells:family.native_only_reference_cells}, null, 2);
  list(); draw();
}
function loadImage(path) { return new Promise((resolve, reject) => { const image = new Image(); image.onload = () => resolve(image); image.onerror = reject; image.src = path; }); }
async function draw() {
  if (!current) return;
  const token = ++generation, family = current, frame = Number($("frame").value), attempt = attemptFor(family);
  $("frameLabel").textContent = frame;
  $("frameStatus").textContent = family.frames[frame - 1]?.name || "Missing native frame";
  for (const id of ["native", "prior", "new"]) $(id).getContext("2d").clearRect(0, 0, 118, 158);
  const draws = [
    ["native", `${family.id}/native_layout.png`, [(frame - 1) % 8 * 126 + 4, Math.floor((frame - 1) / 8) * 166 + 4, 118, 158]],
    ["prior", `../portrait_families/${family.id}/candidate_x2.png`, [(frame - 1) % 8 * 134 + 8, Math.floor((frame - 1) / 8) * 190 + 24, 118, 158]],
  ];
  if (attempt) draws.push(["new", `${family.id}/${attempt.id}/frames/${String(frame).padStart(2, "0")}.png`, [0, 0, 118, 158]]);
  await Promise.allSettled(draws.map(async ([id, path, rect]) => {
    try { const image = await loadImage(path); if (token !== generation) return; const ctx = $(id).getContext("2d"); ctx.imageSmoothingEnabled = id !== "native"; ctx.drawImage(image, ...rect, 0, 0, 118, 158); }
    catch { if (token === generation) { const ctx = $(id).getContext("2d"); ctx.fillStyle = "#ed786f"; ctx.fillText("Unavailable", 12, 75); } }
  }));
}
function saveVote(verdict) {
  if (!current || current.state !== "ready_for_user") return;
  const key = keyFor(current);
  votes[key] = {family:current.id, raw_sha256:attemptFor(current).raw_sha256,
    verdict:verdict || votes[key]?.verdict || "undecided", notes:$("notes").value, updated:new Date().toISOString()};
  persist(); list();
  for (const button of document.querySelectorAll("[data-vote]")) button.setAttribute("aria-pressed", String(votes[key].verdict === button.dataset.vote));
}
for (const button of document.querySelectorAll("[data-vote]")) button.onclick = () => saveVote(button.dataset.vote);
$("notes").oninput = () => saveVote();
$("search").oninput = list; $("unfinished").onchange = list;
$("frame").oninput = draw;
function step(delta) { $("frame").value = (Number($("frame").value) - 1 + delta + 56) % 56 + 1; draw(); }
$("previous").onclick = () => step(-1); $("next").onclick = () => step(1);
$("play").onclick = () => { if (timer) stop(); else { timer = setInterval(() => step(1), 250); $("play").textContent = "Stop"; } };
$("background").onchange = () => { for (const c of document.querySelectorAll("canvas")) c.dataset.bg = $("background").value; };
$("export").onclick = () => {
  const blob = new Blob([JSON.stringify({schema:1, run:"portrait_transparent_v2", votes:Object.values(votes)}, null, 2)], {type:"application/json"});
  const url = URL.createObjectURL(blob), a = document.createElement("a"); a.href = url; a.download = "portrait-feedback.json"; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
};
$("import").onchange = async event => {
  try {
    const imported = JSON.parse(await event.target.files[0].text());
    if (imported.schema !== 1 || imported.run !== "portrait_transparent_v2" || !Array.isArray(imported.votes)) throw Error("Wrong feedback format");
    const accepted = [];
    for (const vote of imported.votes) {
      const family = data.families.find(f => f.id === vote.family);
      if (!family || !family.attempts.some(a => a.raw_sha256 === vote.raw_sha256) || !["like","dislike","undecided"].includes(vote.verdict) || typeof vote.notes !== "string") throw Error("Unknown family/output or invalid vote; nothing imported");
      accepted.push(vote);
    }
    for (const vote of accepted) votes[`${vote.family}:${vote.raw_sha256}`] = vote;
    persist(); list(); if (current) select(current); $("notice").textContent = `Imported ${accepted.length} votes.`;
  } catch (error) { $("notice").textContent = error.message; }
};
$("summary").textContent = Object.entries(data.summary).map(([state, count]) => `${count} ${state}`).join(" · ");
list(); const first = data.families.find(f => f.state === "ready_for_user"); if (first) select(first);
