"use strict";

const $ = selector => document.querySelector(selector);
const $$ = selector => [...document.querySelectorAll(selector)];
const query = new URLSearchParams(location.search);
const screens = {
  inventory: ["Inventory", "32 × 32 LOGICAL PIXELS", "The same inventory, in carved stone.",
    "The 14 × 9 grid retains its exact size and position. Items have no hover overlay or hover label. Hold the right mouse button on an item to inspect it; releasing closes the window."],
  stats: ["Stats", "ORIGINAL GROUPS / SHARED COLOURS", "Familiar figures, quieter divisions.",
    "Six recessed groups have clearer stone-and-brass edges, retaining the original order and current/base formatting. Green denotes a bonus, red a reduction; low HP/SP uses amber. Hold RMB on a field to inspect it."],
  skills: ["Skills", "WHOLE-ROW UPGRADE", "Spend points directly on the skill.",
    "Click anywhere on an eligible blue row to raise that skill. Other rows retain ordinary text. The game's Lucida font and tighter 14-pixel row spacing are retained. Compare its 17-pixel size with a slightly smaller 16-pixel option. Hold RMB to inspect."],
  awards: ["Awards", "ORIGINAL LIST / ORIGINAL COLOURS", "The record needs room, not another frame.",
    "Arrus lettering and the original priority colours sit directly on the dark surface. No nested border, bullets or extra labels. These are actual strings from the merged awards table."],
  rest: ["Rest", "ORIGINAL COMPOSITION", "The familiar camp layout.",
    "Carved blocks group the rest actions, the nested wait controls and the hourglass with its compact date. The separate food-count label is removed; the food cost stays on Rest & Heal. Actions advance this preview’s clock."],
  quickref: ["Party quickref", "ORIGINAL FIELDS / LARGER TYPE", "Use the whole table.",
    "A wider description column and clearer vertical dividers separate the original rows and five character columns. HP and SP remain numbers. Reputation and Fame sit below. Try five members and the mixed colour example."],
  dialogue: ["Dialogue", "BODY ONLY / BOUNDED FONT FIT", "The words determine the height.",
    "A simple body with no speaker heading or Continue button. Arrus starts at its original size, can shrink slightly, then falls back to Create. The outside toolbar reports the chosen size. Only the extreme overflow specimen scrolls."],
  inspect: ["Inspect", "ORIGINAL CONTENT / ORIGINAL FONT ROLES", "A shared frame around familiar layouts.",
    "Item Value stays at the bottom with its divider, including when the artwork is taller than the description or long text scrolls. The title and original font roles remain. These stationary specimens are for review; inventory inspection requires held RMB."],
  buffs: ["Buff icons", "ALL 22 PARTY EFFECTS", "Illustrations in equal boxes.",
    "Existing spell illustrations, clipped to exclude the lettering, keep equal icon boxes. Four earliest expiries plus overflow remains the default; two rows are also available. Hold RMB on a catalogue icon for its description."],
  materials: ["Frame & surface", "TRANSPARENT BORDER / SEPARATE TEXTURE", "Fixed corners, repeating edges.",
    "The border has real alpha and no background baked into its centre. Four corners and four edge strips surround an independent texture. Dark obsidian is selected; the earlier vellum remains available as a comparison."],
  type: ["Fonts & colour", "SELECTED DIRECTION", "MM reading fonts. Fondamento buttons.",
    "The original font roles are retained: Create for character headings, Lucida for values, Arrus for awards and dialogue, Comic for item details, Smallnum for descriptions. Soft ivory is the ordinary text colour."],
};
const pick = (key, values, fallback) => values.includes(query.get(key)) ? query.get(key) : fallback;
const state = {
  screen: pick("screen", Object.keys(screens), "inventory"),
  fonts: pick("fonts", ["native", "refined"], "native"),
  palette: pick("palette", ["ivory", "white"], "ivory"),
  surface: pick("surface", ["stone", "vellum"], "stone"),
  party: pick("party", ["1", "5"], "1"), grid: pick("grid", ["engraved", "inset", "legacy"], "engraved"),
  colours: pick("colours", ["normal", "bonus", "penalty", "mixed"], "mixed"),
  points: Number(pick("points", ["38", "4", "0"], "38")),
  skillSize: pick("skillSize", ["17", "16"], "17"),
  environment: pick("environment", ["outdoor", "house"], "house"),
  length: pick("length", ["short", "medium", "long", "fallback", "overflow", "custom"], "medium"),
  inspect: pick("inspect", ["item", "monster", "stat", "skill", "spell", "buff"], "item"),
  itemExample: pick("itemExample", ["potion", "helm", "sword"], "potion"),
  detail: pick("detail", ["normal", "long"], "normal"),
  buffs: pick("buffs", ["0", "4", "12", "22"], "12"), layout: pick("layout", ["compact", "rows"], "compact"),
  catalog: query.get("catalog") !== "0", width: Math.min(1140, Math.max(440, Number(query.get("width")) || 840)),
  height: Math.min(600, Math.max(210, Number(query.get("height")) || 420)),
  slices: query.get("slices") === "1", alpha: query.get("alpha") === "1",
  minute: 9 * 60, food: 7, selected: 0,
};
const stage = $("#stage");
const layer = $("#screen-layer");
let modal = null;
let baseUrl = "";
let capturedPointer = null;
let layoutVersion = 0;

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"})[c]);
}
function image(name, alt = "", cls = "") {
  return `<img class="${cls}" src="assets/original/${name}.png" alt="${escapeHtml(alt)}" draggable="false">`;
}
function frame() {
  return `<span class="skin-border" aria-hidden="true">${["tl", "tr", "bl", "br", "top", "bottom", "left", "right"].map(x => `<i class="${x}"></i>`).join("")}</span>`;
}
function button(label, attributes = "", cls = "") {
  return `<button class="obs-button ${cls}" ${attributes}><span class="obs-label">${label}</span></button>`;
}
function select(key, label, options) {
  return `<label>${label}<select data-setting="${key}">${options.map(([value, text]) =>
    `<option value="${value}" ${String(state[key]) === value ? "selected" : ""}>${text}</option>`).join("")}</select></label>`;
}
function checkbox(key, label) {
  return `<label><input type="checkbox" data-setting="${key}" ${state[key] ? "checked" : ""}>${label}</label>`;
}
function slider(key, label, min, max) {
  return `<label>${label}<input type="range" data-setting="${key}" min="${min}" max="${max}" step="10" value="${state[key]}"><output data-output="${key}">${state[key]}</output></label>`;
}
function duration(seconds) {
  if (seconds < 60) return `0:${String(seconds).padStart(2, "0")}`;
  return seconds < 3600 ? `${Math.floor(seconds / 60)}m` : `${Math.floor(seconds / 3600)}h`;
}
function feedback(message) { $("#feedback").textContent = message; }
function coloured(value, cls) { return `<span class="${cls}">${escapeHtml(value)}</span>`; }
function comparison(value, base) { return coloured(value, value > base ? "good" : value < base ? "bad" : ""); }
function splitValue(value, base) { return `${comparison(value, base)} / ${base}`; }
function resource(value, max) { return coloured(value, value <= 0 ? "bad" : value * 2 < max ? "low" : ""); }
function fixtureValue(base, index = 0) {
  if (state.colours === "bonus" || state.colours === "mixed" && index % 3 === 0) return base + 15;
  if (state.colours === "penalty" || state.colours === "mixed" && index % 3 === 1) return Math.max(0, base - 6);
  return base;
}
const party = [
  { name: "Kareth", role: "Knight", level: 12, hp: [128,132], sp: [36,48], ac: 34, attack: "+21", melee: "17–26", shoot: "+12", ranged: "8–13", skills: 12, points: 38, condition: "Good", spell: "None" },
  { name: "Elara", role: "Cleric", level: 12, hp: [72,96], sp: [105,128], ac: 27, attack: "+13", melee: "9–16", shoot: "+10", ranged: "6–10", skills: 14, points: 26, condition: "Good", spell: "Heal" },
  { name: "Mara", role: "Druid", level: 11, hp: [91,102], sp: [64,92], ac: 29, attack: "+17", melee: "11–20", shoot: "+13", ranged: "8–14", skills: 15, points: 17, condition: "Good", spell: "Lightning Bolt" },
  { name: "Vaelis", role: "Sorcerer", level: 12, hp: [85,96], sp: [117,148], ac: 22, attack: "+11", melee: "6–12", shoot: "+14", ranged: "8–16", skills: 16, points: 0, condition: "Good", spell: "Fireball" },
  { name: "Tor", role: "Minotaur", level: 12, hp: [180,188], sp: [18,28], ac: 41, attack: "+27", melee: "23–38", shoot: "+11", ranged: "7–14", skills: 11, points: 22, condition: "Good", spell: "Bless" },
];
const skillGroups = {
  Weapons: [["Sword", 7, "Expert"], ["Bow", 5, "Expert"], ["Axe", 2, "Normal"], ["Mace", 3, "Normal"], ["Dagger", 1, "Normal"]],
  Armor: [["Plate", 4, "Expert"], ["Shield", 5, "Expert"], ["Chain", 3, "Normal"], ["Leather", 2, "Normal"]],
  Magic: [["Fire Magic", 4, "Expert"], ["Air Magic", 3, "Normal"], ["Water Magic", 2, "Normal"], ["Body Magic", 1, "Normal"]],
  Miscellaneous: [["Identify Item", 4, "Expert"], ["Repair Item", 5, "Expert"], ["Merchant", 3, "Normal"], ["Body Building", 6, "Expert"], ["Learning", 4, "Expert"], ["Perception", 2, "Normal"]],
};
// Logical footprints; each unit is exactly 32 pixels at the original 640 × 480 size.
const inventoryItems = [
  ["item138", 0, 0, 1, 1], ["item137", 1, 0, 1, 1],
  ["book1", 3, 0, 2, 2], ["book3", 5, 0, 2, 2], ["book4", 7, 0, 2, 2],
  ["item199", 10, 0, 3, 1], ["item202", 10, 1, 3, 1],
  ["item178", 0, 2, 1, 2], ["item177", 1, 2, 1, 2],
  ["item001", 3, 3, 1, 5], ["item004", 5, 3, 1, 5],
  ["item082", 8, 3, 2, 6], ["item200", 10, 3, 3, 1], ["item256", 11, 5, 2, 3],
];
const dialogueText = {
  short: ["The road north is open again. Keep to the river, and you should reach the village before nightfall."],
  medium: ["There are old paths through the hills, traveller, but not all of them lead where the maps promise. Follow the river until you reach the broken bridge. From there, the eastern trail will take you to the village.",
    "If you mean to travel after sunset, take a lantern. The watchmen have seen lights among the ruins, and no one who lives here is eager to find out who carries them."],
  long: ["I remember when the road was busy from dawn until dusk. Merchants would stop here with wagons of grain and cloth, and the children would run out to see the horses. That was before the bridge fell.",
    "There are still paths through the hills, traveller, but not all of them lead where the maps promise. Follow the river until you reach the broken bridge. From there, the eastern trail will take you to the village. Avoid the old quarry; the recent rain has loosened the stones.",
    "If you mean to travel after sunset, take a lantern. The watchmen have seen lights among the ruins, and no one who lives here is eager to find out who carries them. Ask at the inn when you arrive. Someone there may know more than I do."],
};
dialogueText.fallback = [...dialogueText.long, dialogueText.medium[1]];
dialogueText.overflow = [...dialogueText.long, ...dialogueText.medium, ...dialogueText.long];

function characterHeader(showPoints = true) {
  const person = party[state.selected];
  return `<div class="character-header"><h2>${person.name}${showPoints ? ` <span class="character-class">the ${person.role}</span>` : ""}</h2>
    ${showPoints ? `<button class="skill-points" data-inspect="stat" data-label="Skill Points">Skill Points: ${coloured(state.points, state.points > 0 ? "good" : "")}</button>` : ""}</div>`;
}
function characterNav() {
  return `<nav class="character-nav" aria-label="Character pages">${["stats", "skills", "inventory", "awards"].map(key =>
    button(screens[key][0], `data-view="${key}" aria-pressed="${state.screen === key}"`)).join("")}${button("Exit", 'data-action="exit"')}</nav>`;
}
function statRow(label, value, cls = "", inspectLabel = "") {
  const tag = inspectLabel ? "button" : "div";
  return `<${tag} class="stat-row ${cls}" ${inspectLabel ? `data-inspect="stat" data-label="${escapeHtml(inspectLabel)}"` : ""}>
    <span>${label}</span><span class="value">${value}</span></${tag}>`;
}
function statsPage() {
  const rows = list => list.map(([label, value, inspectLabel]) => statRow(label, value, "", inspectLabel || label)).join("");
  const hp = state.colours === "penalty" || state.colours === "mixed" ? 42 : 128;
  const sp = state.colours === "penalty" ? 0 : 36;
  const condition = state.colours === "penalty" ? coloured("Poisoned", "bad") : "Good";
  return `<section class="page-surface stone-surface stats-page">${characterHeader()}<div class="stat-columns"><div>
    <div class="stat-group">${rows([["Might",28],["Intellect",18],["Personality",16],["Endurance",25],["Accuracy",24],["Speed",21],["Luck",17]].map(([label,base],i) => [label,splitValue(fixtureValue(base,i),base)]))}</div>
    <div class="stat-group">${rows([["Hit Points",`${resource(hp,132)} / 132`],["Spell Points",`${resource(sp,48)} / 48`],["Armor Class",splitValue(fixtureValue(34,0),34)]])}</div>
    <div class="stat-group conditions">${rows([["Condition",condition],["Quick Spell","None"]])}</div>
    </div><div><div class="stat-group">${rows([["Age","27"],["Level","12 / 12"],["Experience","68,420"]])}</div>
    <div class="stat-group">${rows([["Attack","+21","Attack Bonus"],["Damage","17–26","Attack Damage"],["Shoot","+12","Shoot Bonus"],["Damage","8–13","Shoot Damage"]])}</div>
    <div class="stat-group resistances">${rows([["Fire",18],["Air",12],["Water",12],["Earth",15],["Mind",10],["Body",20]].map(([label,base],i) => [label,splitValue(fixtureValue(base,i+2),base)]))}</div>
    </div></div></section>${characterNav()}`;
}
function skillsPage() {
  const group = name => `<section class="skill-group"><h3>${name}</h3>${skillGroups[name].map(([label,rank,mastery]) => {
    const eligible = state.points >= rank + 1;
    return `<button class="skill-row ${eligible ? "eligible" : ""}" data-raise="${label}" data-inspect="skill" data-label="${label}"
      aria-disabled="${!eligible}" aria-label="${label}, ${mastery} ${rank}. ${eligible ? `Raise for ${rank+1} points` : "Not enough points"}">
      <span>${label}</span><span class="skill-level">${mastery === "Normal" ? "" : mastery} ${rank}</span></button>`;
  }).join("")}</section>`;
  return `<section class="page-surface stone-surface skills-page" style="--skill-size:${Number(state.skillSize)*1.875}px">${characterHeader()}<div class="skill-columns"><div>${group("Weapons")}${group("Magic")}</div>
    <div>${group("Armor")}${group("Miscellaneous")}</div></div></section>${characterNav()}`;
}
function inventoryPage() {
  if (state.grid === "legacy") return characterNav();
  return `<section class="page-surface stone-surface inventory-page"><div class="inventory-grid ${state.grid}" data-cell-logical="32">
    ${state.grid === "inset" ? Array.from({length:126}, (_,i) => `<i class="grid-cell" style="left:${i%14*60}px;top:${Math.floor(i/14)*60}px"></i>`).join("") : ""}
    ${inventoryItems.map(([art,x,y,w,h],i) => `<button class="inventory-item" data-item="${i}"
      aria-label="Hold right mouse button to inspect ${escapeHtml(originalContent.items[art].name)}"
      style="left:${x*60}px;top:${y*60}px;width:${w*60}px;height:${h*60}px">${image(art,originalContent.items[art].name)}</button>`).join("")}
    </div></section>${characterNav()}`;
}
function awardsPage() {
  // Keep the first four awards from 2082 together before additional wrapping/scroll specimens.
  const entries = [1,3,4,2,5,6,7,8].map(id => originalContent.awards.find(a => a.id === id));
  return `<section class="page-surface stone-surface awards-page">${characterHeader(false)}
    <div class="award-list" tabindex="0" aria-label="Character awards">${entries.map(a => `<p class="award-entry priority-${a.priority}">${escapeHtml(a.text)}</p>`).join("")}</div></section>${characterNav()}`;
}
function clockText() {
  const hours = Math.floor(state.minute/60)%24;
  return `${hours%12 || 12}:${String(state.minute%60).padStart(2,"0")} ${hours<12 ? "am" : "pm"}`;
}
function restPage() {
  return `<section class="full-page stone-surface rest-page">
    <div class="rest-sky">${image(state.minute%1440 >= 360 && state.minute%1440 < 1080 ? "terra0091" : "terra0000","Rest panorama")}</div>
    <section class="rest-actions-block carved-block" aria-label="Rest and wait">
      <button class="obs-button rest-eight" data-rest="480"><span class="obs-label">Rest &amp; Heal 8 Hours</span><span class="food-cost">${image("scorebg_food","Food required")}2</span></button>
      <section class="rest-wait-block carved-block" aria-label="Wait without healing"><div class="wait-label">Wait without healing</div><div class="rest-waits">
        ${button("Wait until Dawn",'data-rest="dawn"')}${button("Wait 1 Hour",'data-rest="60"')}${button("Wait 5 Minutes",'data-rest="5"')}
      </div></section>
    </section>
    <div class="rest-calendar carved-block">${image("hglas060","Hourglass","hourglass")}<div class="date-text"><div id="rest-time">${clockText()}</div>
      <div class="date-row"><span>Day</span><span id="rest-day">${1+Math.floor(state.minute/1440)}</span></div>
      <div class="date-row"><span>Month</span><span>1</span></div><div class="date-row"><span>Year</span><span>1168</span></div>
    </div></div>${button("Exit Rest",'data-action="exit"',"exit-rest")}</section>`;
}
function quickValue(person,key,i) {
  if (key === "hp" || key === "sp") {
    const [value,max] = person[key];
    const reduced = state.colours === "penalty" || state.colours === "mixed" && i === (key === "hp" ? 0 : 2);
    return resource(reduced ? (i === 0 && key === "hp" ? 42 : Math.floor(max*.3)) : value,max);
  }
  if (key === "condition" && (state.colours === "penalty" || state.colours === "mixed" && i === 3)) return coloured("Poisoned","bad");
  if (key === "points") {
    const points = i === 0 ? state.points : person.points;
    return coloured(points,points > 0 ? "good" : "");
  }
  if (key === "ac") return comparison(fixtureValue(person.ac,i),person.ac);
  return escapeHtml(person[key]);
}
function quickrefPage() {
  const fields = [["Level","level"],["Class","role"],["HP","hp"],["SP","sp"],["AC","ac"],["Attack","attack"],["Damage","melee"],["Shoot","shoot"],["Damage","ranged"],["Skills","skills"],["Points","points"],["Cond","condition"],["QSpell","spell"]];
  return `<section class="full-page stone-surface quick-page"><table class="quick-table"><thead><tr><th scope="col">Name</th>
    ${party.map((p,i) => `<th scope="col">${i < Number(state.party) ? p.name : ""}</th>`).join("")}</tr></thead><tbody>
    ${fields.map(([label,key],row) => `<tr class="${[2,5,9,11].includes(row) ? "group-start" : ""}"><th scope="row">${label}</th>
      ${party.map((p,i) => `<td>${i < Number(state.party) ? quickValue(p,key,i) : ""}</td>`).join("")}</tr>`).join("")}</tbody></table>
    <div class="quick-footer"><span>Reputation: <span class="${state.colours === "penalty" ? "bad" : ""}">${state.colours === "penalty" ? "Notorious" : "Average"}</span></span><span>Fame: 128</span>
    ${button("Exit",'data-action="exit"')}</div></section>`;
}
function dialoguePage() {
  const paragraphs = state.length === "custom" ? $("#custom-text").value.split(/\n\s*\n/).filter(Boolean) : dialogueText[state.length];
  return `<section class="skin ${state.surface} dialogue-sheet ${state.environment}">${frame()}
    <div class="dialogue-copy" tabindex="0">${paragraphs.map(text => `<p>${escapeHtml(text)}</p>`).join("")}</div></section>`;
}
function fitDialogue() {
  const copy = $(".dialogue-copy");
  if (!copy) return;
  const maximum = state.environment === "house" ? 563 : 578;
  // Original 19px Arrus first; at most 1px smaller, then the original 18px Create face.
  const candidates = state.fonts === "native" ? [["Native Arrus",35.625,30],["Native Arrus",33.75,28.125],
    ["Native Create",33.75,28.125],["Native Create",31.875,26.25]] : [["Source Serif",29,35],["Source Serif",27,32]];
  let chosen;
  copy.style.maxHeight = "none";
  copy.style.overflowY = "visible";
  for (const [face,size,leading] of candidates) {
    copy.style.fontFamily = `"${face}", serif`;
    copy.style.fontSize = `${size}px`; copy.style.lineHeight = `${leading}px`;
    chosen = {face,size};
    if (copy.scrollHeight <= maximum) break;
  }
  const overflow = copy.scrollHeight > maximum;
  copy.style.maxHeight = `${maximum}px`;
  copy.style.overflowY = overflow ? "auto" : "visible";
  copy.dataset.font = chosen.face; copy.dataset.size = chosen.size; copy.dataset.overflow = overflow;
  $(".dialogue-sheet").dataset.font = chosen.face;
  const note = $("#dialogue-fit");
  if (note) note.textContent = `${chosen.face.replace("Native ","")} · ${Number((chosen.size/1.875).toFixed(1))} logical px${overflow ? " · extreme text scrolls" : " · fits"}`;
}

function inspectBody(type,label,itemIndex) {
  const longText = state.detail === "long" ? `<p class="inspect-description">${dialogueText.long.map(escapeHtml).join("<br><br>")}</p>` : "";
  if (type === "item") {
    const art = itemIndex === undefined ? {potion:"item178",helm:"item256",sword:"item004"}[state.itemExample] : inventoryItems[itemIndex][0];
    const item = originalContent.items[art];
    const details = art === "item256" ? "Armor: +15" : art === "item004" ? "Attack: +8 &nbsp; Damage: 3d3 + 8" : art === "item001" ? "Attack: +0 &nbsp; Damage: 3d3" : art === "item082" ? "Attack: +4 &nbsp; Damage: 2d4 + 4" : "";
    return {title:item.name,width:721.875,footer:`<div class="inspect-value">Value: ${item.value}</div>`,
      body:`<div class="item-inspect">${image(art,item.name)}<div class="item-copy">
      <div class="inspection-type">Type: ${escapeHtml(item.type)}</div>${details ? `<div class="item-details">${details}</div>` : ""}
      <p class="inspect-description">${escapeHtml(item.description)}</p>${longText}
      </div></div>`};
  }
  if (type === "monster") return {title:"Goblin",width:693.75,body:`<div class="monster-hp" role="meter" aria-label="Monster hit points" aria-valuenow="42" aria-valuemin="0" aria-valuemax="42"><i></i></div>
    <div class="actor-inspect"><div><div class="actor-preview">${image("goblin","Goblin")}</div><h3>Effects</h3><div class="effects">None</div></div><div>
    ${[["Hit Points","42 / 42"],["Armor Class",12],["Attack","Physical"],["Damage","2–8"],["Spell","None"]].map(x => statRow(...x)).join("")}
    <h3>Resistances</h3><div class="actor-resistances">${["Fire","Air","Water","Earth","Mind","Spirit","Body","Light","Dark","Physical"].map(x => statRow(x,"None")).join("")}</div>
    </div></div>${longText}`};
  if (type === "stat") {
    const name = label || "Endurance";
    return {title:name,width:796.875,body:`<p class="inspect-description">${escapeHtml(originalContent.stats[name])}</p>${longText}`};
  }
  if (type === "skill") {
    const name = label || "Sword";
    const key = name.replace(" Magic","").replace("Repair Item","Repair").replace("Body Building","Bodybuilding");
    const skill = originalContent.skills[key];
    return {title:name,width:796.875,body:`<p class="inspect-description">${escapeHtml(skill.description)}</p>
      <dl class="mastery">${["Normal","Expert","Master","Grandmaster"].map((rank,i) => `<dt>${rank}</dt><dd>${escapeHtml(skill.mastery[i])}</dd>`).join("")}</dl>
      <p class="skill-bonus">Skill bonus: <span class="good">+2</span></p>${longText}`};
  }
  if (type === "spell") return {title:"Fly",width:937.5,body:`<div class="spell-inspect"><div>${glyphFreeBuff("sba10a","","Fly")}<div class="spell-cost">Air Magic<br>Cost: 25</div></div><div>
    <p class="inspect-description">Allows the party to fly while outdoors. Flight consumes spell points while the party is in the air.</p>
    <dl class="mastery"><dt class="bad">Normal</dt><dd class="bad">Not available</dd><dt class="bad">Expert</dt><dd class="bad">Not available</dd><dt>Master</dt><dd>Duration: 1 hour per point of skill</dd><dt>Grandmaster</dt><dd>Flight does not consume spell points</dd></dl>${longText}</div></div>`};
  const buff = partyBuffCatalog.find(x => x.id === label) || partyBuffCatalog.find(x => x.id === "Shield");
  return {title:buff.name,width:618.75,body:`<p class="inspect-description">${escapeHtml(buff.detail)}</p><p class="inspect-description">Time remaining: ${duration(buff.seconds)}</p>${longText}`};
}
function renderInspector() {
  // The approved HUD is a separate iframe. Keep held-input ownership in this document until release.
  stage.classList.toggle("holding-inspect", Boolean(modal?.held));
  if (!modal) { $("#modal-layer").innerHTML = ""; return; }
  const content = inspectBody(modal.type,modal.label,modal.item);
  $("#modal-layer").innerHTML = `<section class="skin ${state.surface} inspector inspect-${modal.type} ${modal.held ? "held-inspector" : ""}"
    role="dialog" aria-modal="false" aria-label="${escapeHtml(content.title)}" style="width:${content.width}px">${frame()}
    <h2>${escapeHtml(content.title)}</h2><div class="inspect-content">${content.body}</div>${content.footer || ""}</section>`;
}
function closeHeldInspector() {
  if (!modal?.held) return;
  modal = null; renderInspector();
  if (capturedPointer) {
    const {target,id} = capturedPointer;
    capturedPointer = null;
    if (target.hasPointerCapture(id)) target.releasePointerCapture(id);
  }
}
function buffsPage() {
  if (!state.catalog) return "";
  return `<section class="skin stone buff-browser">${frame()}<h2>Party enchantments</h2><div class="buff-grid">${partyBuffCatalog.map(buff =>
    `<button class="buff-specimen" data-inspect="buff" data-label="${buff.id}" aria-label="Hold RMB to inspect ${buff.name}">${glyphFreeBuff(buff.art,"",buff.name)}<span>${buff.name}</span></button>`).join("")}</div></section>`;
}
function materialsPage() {
  return `<div class="materials-backdrop"></div><div class="material-caption"><span>Transparent border · separate reading surface</span><span>${state.width} × ${state.height}</span></div>
    <section class="skin ${state.surface} materials-panel ${state.slices ? "show-slices" : ""} ${state.alpha ? "alpha-demo" : ""}"
    style="--panel-width:${state.width}px;--panel-height:${state.height}px">${frame()}<div class="sample-contents"><h2>A traveller’s journal</h2>
    <p>Some roads are best followed slowly. At dusk, the pale stone of the watchtower catches the last light, and the valley below begins to disappear into the mist.</p>
    <div class="sample-meta">Corners stay the same size.<br>Surface grain keeps its scale.</div></div></section>`;
}
function typePage() {
  return `<section class="type-page"><h2>The familiar letterforms, on obsidian</h2><div class="type-panels"><section class="skin stone">${frame()}
    <div class="font-specimen native-create">Kareth <span class="character-class">the Knight</span><small>Create · character headings</small></div>
    <div class="font-specimen native-lucida">Might &nbsp; ${splitValue(43,28)}<small>Lucida · character values</small></div>
    <div class="font-specimen native-arrus">The road north is open again.<small>Arrus · dialogue, awards, quick reference</small></div>
    <div class="font-specimen native-comic">Type: Artifact Helm<small>Comic · item type, details and value</small></div>
    <div class="font-specimen native-smallnum">Endurance is a measure of a character's physical toughness and durability.<small>Smallnum · inspector descriptions</small></div>
    </section><section class="skin stone">${frame()}<h3>Colour has a purpose</h3>
    <div class="colour-specimen">Normal &nbsp; 28 / 28<small>Soft ivory · #e5dcc7</small></div>
    <div class="colour-specimen good">Bonus &nbsp; 43 / <span class="neutral">28</span><small>Jade · #85df8b · bonuses and available points</small></div>
    <div class="colour-specimen available">Sword &nbsp; Expert 7<small>Blue · #8ebcfa · an upgradeable skill row</small></div>
    <div class="colour-specimen bad">Reduced &nbsp; 22 / <span class="neutral">28</span><small>Coral · #ee8275 · also harmful conditions / zero HP</small></div>
    <div class="colour-specimen low">Low HP / SP &nbsp; 42 / <span class="neutral">132</span><small>Amber · #e6c36c · below half, above zero</small></div>
    <div class="type-buttons">${button("Inventory",'data-view="inventory"')}${button("Skills",'data-view="skills" aria-pressed="true"')}</div>
    <p class="type-button-note">Fondamento stays on buttons.</p></section></div>
    <p class="type-summary">Existing font roles and current/base formatting. Original award-priority colours remain separate.</p></section>`;
}

function renderControls() {
  const colourControl = () => select("colours","Values",[["normal","Ordinary"],["bonus","Bonuses"],["penalty","Penalties"],["mixed","Mixed example"]]);
  const pointControl = () => {
    const options = [["38","38 · available"],["4","4 · some available"],["0","0 · none available"]];
    if (![38,4,0].includes(state.points)) options.unshift([String(state.points),`${state.points} · current`]);
    return select("points","Skill points",options);
  };
  let controls = "";
  switch (state.screen) {
    case "inventory": controls = select("grid","Cells",[["engraved","Engraved lines"],["inset","Subtle inset"],["legacy","Original comparison"]]) + "<span>14 × 9 · 32 × 32 logical pixels each · hold RMB to inspect</span>"; break;
    case "stats": controls = colourControl() + pointControl() + "<span>Hold RMB on a field to inspect.</span>"; break;
    case "skills": controls = pointControl() + select("skillSize","Skill text",[["17","Lucida · runtime size (17)"],["16","Lucida · slightly smaller (16)"]]) + '<button data-action="reset-skills">Reset skills</button><span>Click a blue row to raise it · hold RMB to inspect</span>'; break;
    case "awards": controls = "<span>Original priority colours · scroll for more entries</span>"; break;
    case "rest": controls = '<button data-action="reset-rest">Reset time</button><span>Original placements · actions advance the sample clock</span>'; break;
    case "quickref": controls = colourControl() + "<span>Use the Party selector above for the full five-column example.</span>"; break;
    case "dialogue": controls = select("environment","Setting",[["house","House / indoor NPC"],["outdoor","Outdoor NPC"]]) + select("length","Text",[["short","Short"],["medium","Medium"],["long","Long"],["fallback","Longer · font fallback"],["overflow","Extreme overflow"],["custom","Write your own"]]) + '<span id="dialogue-fit"></span>'; break;
    case "inspect": controls = select("inspect","Inspect",[["item","Item"],["monster","Monster"],["stat","Stat"],["skill","Skill"],["spell","Spell"],["buff","Buff"]]) +
      (state.inspect === "item" ? select("itemExample","Item",[["potion","Cure Wounds · 2078"],["helm","Drogg’s Helm · 2085"],["sword","Templar’s Sword"]]) : "") +
      select("detail","Text",[["normal","Original length"],["long","Overflow stress test"]]) + "<span>Stationary review specimen · inventory uses held RMB</span>"; break;
    case "buffs": controls = select("buffs","Active effects",[["0","None"],["4","4"],["12","12"],["22","22 · all types"]]) + select("layout","Strip",[["compact","4 + overflow"],["rows","2 rows + overflow"]]) + checkbox("catalog","Show catalogue"); break;
    case "materials": controls = slider("width","Width",440,1140) + slider("height","Height",210,600) + checkbox("slices","Show 8 slices") + checkbox("alpha","Alpha checkerboard"); break;
    case "type": controls = "<span>Selected font roles and proposed semantic colours · button states respond to hover / press</span>"; break;
  }
  $("#context-controls").innerHTML = controls;
  $("#custom-copy").hidden = state.screen !== "dialogue" || state.length !== "custom";
}
function setBase() {
  const gameplay = ["buffs","inspect"].includes(state.screen) || state.screen === "dialogue" && state.environment === "outdoor";
  const url = gameplay ? `../hud_concepts_20260927/index.html?concept=obsidian&party=${state.party}&buffs=${state.buffs}&buffLayout=${state.layout}&bars=shaded&status=off&buffArt=clean&export=1`
    : `../hud_overlay_study_20260927/index.html?screen=${state.screen === "dialogue" ? "2062" : "2060"}&treatment=carved&party=${state.party}&buttons=fondamento&export=1&status=${encodeURIComponent(query.get("status") || "off")}`;
  $("#base-frame").hidden = ["materials","type"].includes(state.screen);
  if (url !== baseUrl) { $("#base-frame").src = url; baseUrl = url; }
}
function persist() {
  const next = new URLSearchParams();
  for (const key of ["screen","fonts","palette","surface","party","grid","colours","points","skillSize","environment","length","inspect","itemExample","detail","buffs","layout","width","height"]) next.set(key,state[key]);
  for (const key of ["catalog","slices","alpha"]) next.set(key,state[key] ? "1" : "0");
  if (query.get("export") === "1") next.set("export","1");
  if (query.has("status")) next.set("status",query.get("status"));
  history.replaceState(null,"",`?${next}`);
}
function fitContents() {
  fitDialogue();
  // Native Arrus has unusually wide capital letters. Only long quick-spell/class cells may step down.
  $$(".quick-table td").forEach(cell => {
    cell.style.fontSize = "";
    for (const size of [33.75,31.875,30,28.125,26.25]) {
      if (cell.scrollWidth <= cell.clientWidth) break;
      cell.style.fontSize = `${size}px`;
    }
  });
}
function renderContent() {
  const renderers = {stats:statsPage,skills:skillsPage,inventory:inventoryPage,awards:awardsPage,rest:restPage,
    quickref:quickrefPage,dialogue:dialoguePage,inspect:() => "",buffs:buffsPage,materials:materialsPage,type:typePage};
  layer.innerHTML = renderers[state.screen](); renderInspector(); fitContents();
  const version = ++layoutVersion;
  document.fonts.ready.then(() => { if (version === layoutVersion) fitContents(); });
}
function render() {
  stage.className = `stage button-theme font-fondamento font-${state.fonts} palette-${state.palette}`;
  $("#screen-tabs").innerHTML = Object.entries(screens).map(([key,data]) => `<button data-view="${key}" aria-pressed="${state.screen === key}">${data[0]}</button>`).join("");
  for (const key of ["fonts","palette","surface","party"]) $(`#${key}`).value = state[key];
  const note = screens[state.screen];
  $("#note-label").textContent = note[1]; $("#note-title").textContent = note[2]; $("#note-body").textContent = note[3];
  $("#caption").textContent = `${note[0]} · Revision 03 · ${state.fonts === "native" ? "Recreated MM fonts" : "Earlier Source-font comparison"} · Fondamento buttons`;
  setBase(); renderControls(); renderContent(); persist();
}
function showScreen(key) {
  closeHeldInspector(); state.screen = key; modal = key === "inspect" ? {type:state.inspect} : null;
  feedback(""); render();
}
function changeSetting(key,value) {
  closeHeldInspector();
  state[key] = ["width","height","points"].includes(key) ? Number(value) : value;
  if (state.screen === "inspect") modal = {type:state.inspect};
  render();
}
document.addEventListener("change",event => {
  const target = event.target;
  if (target.dataset.setting) changeSetting(target.dataset.setting,target.type === "checkbox" ? target.checked : target.value);
  else if (["fonts","palette","surface","party"].includes(target.id)) changeSetting(target.id,target.value);
});
document.addEventListener("input",event => {
  const target = event.target;
  if (target.type === "range" && target.dataset.setting) {
    state[target.dataset.setting] = Number(target.value);
    $(`[data-output="${target.dataset.setting}"]`).textContent = target.value;
    renderContent(); persist();
  }
  if (target.id === "custom-text") renderContent();
});
layer.addEventListener("pointerdown",event => {
  if (event.button !== 2) return;
  const target = event.target.closest("[data-item], [data-inspect]");
  if (!target) return;
  event.preventDefault();
  capturedPointer = {target,id:event.pointerId}; target.setPointerCapture(event.pointerId);
  modal = target.dataset.item !== undefined ? {type:"item",item:Number(target.dataset.item),held:true}
    : {type:target.dataset.inspect,label:target.dataset.label,held:true};
  renderInspector();
});
window.addEventListener("pointerup",event => { if (event.button === 2 || !(event.buttons & 2)) closeHeldInspector(); });
window.addEventListener("pointercancel",closeHeldInspector);
window.addEventListener("blur",closeHeldInspector);
layer.addEventListener("lostpointercapture",closeHeldInspector);
window.addEventListener("pointermove",event => { if (modal?.held && !(event.buttons & 2)) closeHeldInspector(); });
stage.addEventListener("contextmenu",event => event.preventDefault());
document.addEventListener("click",event => {
  const target = event.target.closest("button");
  if (!target) return;
  if (target.dataset.view) { showScreen(target.dataset.view); return; }
  if (target.dataset.raise) {
    const skill = Object.values(skillGroups).flat().find(x => x[0] === target.dataset.raise);
    if (skill && state.points >= skill[1]+1) {
      const cost = skill[1]+1; state.points -= cost; skill[1]++;
      feedback(`${skill[0]} raised to ${skill[1]}; spent ${cost} skill points. Preview only.`); renderControls(); renderContent(); persist();
    }
    return;
  }
  if (target.dataset.rest) {
    const rest = target.dataset.rest;
    if (rest === "480" && state.food < 2) { feedback("Not enough food to rest."); return; }
    const amount = rest === "dawn" ? (360-state.minute%1440+1440)%1440 || 1440 : Number(rest);
    state.minute += amount; if (rest === "480") state.food -= 2;
    renderContent(); feedback(`Preview clock advanced ${amount} minutes${rest === "480" ? "; 2 food consumed" : ""}.`); return;
  }
  switch (target.dataset.action) {
    case "exit": state.catalog = false; showScreen("buffs"); break;
    case "reset-rest": state.minute = 540; state.food = 7; renderContent(); feedback("Time and food reset."); break;
    case "reset-skills": location.href = `?screen=skills&fonts=${state.fonts}&surface=${state.surface}&party=${state.party}`; break;
  }
});
document.addEventListener("keydown",event => { if (event.key === "Escape") closeHeldInspector(); });
$("#fullscreen").addEventListener("click",() => $("#stage-host").requestFullscreen());
function fitStage() {
  const host = $("#stage-host");
  const scale = Math.min(host.clientWidth/1600,host.clientHeight/900);
  stage.style.transform = `scale(${scale})`;
  stage.style.left = `${(host.clientWidth-1600*scale)/2}px`;
  stage.style.top = `${(host.clientHeight-900*scale)/2}px`;
}
new ResizeObserver(fitStage).observe($("#stage-host"));
if (query.get("export") === "1") document.body.classList.add("export");
if (state.screen === "inspect") modal = {type:state.inspect};
render(); fitStage();
