// Attack/cast timing review: every 3D actor's attack and cast clips against the native billboard timing.
// The game applies an attack when its sprite's contact frame appears (rendering/sprite_attack_timing.yml), or when
// the sprite animation ends (MM8) for a sprite without one; the action still lasts the whole sprite animation.
// The "In game" mode reproduces WorldFxSystem's action fit: the clip's wind-up [0, impact] spans the time to that
// moment, the rest plays at its own speed (through the rest of the action, then as follow-through) and state changes
// crossfade over 0.12 s.
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';

const $ = id => document.getElementById(id);
const BLEND = 0.12;                 // WorldFxSystem default crossfade between actor states
const WINDUP_OK = [0.85, 1.2];      // wind-up speed factors that read as authored
const POSE_TOLERANCE = 0.06;        // start/end pose distance from Standing frame 0, fraction of skeleton height
const ROLES = ['attack_melee', 'attack_ranged', 'cast'];
const ROLE_LABEL = {attack_melee: 'Melee', attack_ranged: 'Ranged', cast: 'Cast'};
const ROLE_SHORT = {attack_melee: 'M', attack_ranged: 'R', cast: 'C'};
const ACTIONS = {
  resolve_source: 'Resolve the source/runtime clip mismatch first',
  add_marker: 'Add an impact marker',
  trim_windup: 'Shorten the wind-up (trim the start or retime the anticipation)',
  add_anticipation: 'Lengthen the wind-up (add anticipation before the strike)',
  trim_follow: 'Shorten the follow-through',
  ease_end: 'Ease the end into Standing frame 0',
  ease_start: 'Start from Standing frame 0',
  replace_clip: 'Replace the clip',
};

let data;
let decisions = {};
let serverSaves = true;
let decisionsVersion = null;          // ETag of decisions.json as this page last loaded or saved it
const deletedKeys = new Set();       // decisions removed on this page, so a merge does not bring them back
let saveTimer;
const LOCAL_KEY = 'openyamm:timing-review';
const sel = {model: null, role: null, tier: 0};
let view = null;                    // the loaded model, see loadModel()
let loadSerial = 0;
let playing = false;
let gameTime = 0;
let clipTime = 0;
let lastTick = performance.now();
let curves = null;                  // tracked point curves of the selected clip
let poseCheck = null;               // start/end pose distances of the selected clip
const spriteImages = new Map();

// ---------------------------------------------------------------- scene
const canvas = $('model');
const renderer = new THREE.WebGLRenderer({canvas, antialias: true});
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
const scene = new THREE.Scene();
scene.background = new THREE.Color('#4d5156');
scene.add(new THREE.HemisphereLight(0xf2f5ff, 0x4a4a44, 2.2));
for (const [position, power] of [[[3, 4, 4], 2.8], [[-4, 2, 1], 1.2], [[1, 3, -3], 1.6]]) {
  const light = new THREE.DirectionalLight(0xffffff, power);
  light.position.set(...position);
  scene.add(light);
}
const grid = new THREE.GridHelper(1, 20, 0x9aa1a9, 0x737a82);
grid.material.transparent = true;
grid.material.opacity = 0.35;
scene.add(grid);
const camera = new THREE.PerspectiveCamera(32, 1, 0.01, 200);
const controls = new OrbitControls(camera, canvas);
const stage = $('stage');
new ResizeObserver(() => {
  const rect = stage.getBoundingClientRect();
  renderer.setSize(rect.width, rect.height, false);
  camera.aspect = rect.width / Math.max(1, rect.height);
  camera.updateProjectionMatrix();
}).observe(stage);

function showError(text) {
  $('error').textContent = text;
  $('error').hidden = !text;
}

// ---------------------------------------------------------------- data helpers
const fmt = (value, digits = 2) => Number.isFinite(value) ? value.toFixed(digits) : '–';
const modelLabel = model => model.model.replace(/\.glb$/, '');
const decisionKey = (model, role) => `${model.model}|${role}`;
const decisionOf = (model, role) => decisions[decisionKey(model, role)] || {};
const clipKey = (model, clip) => `clip|${model.model}|${clip}`;
const clipDecision = (model, clip) => decisions[clipKey(model, clip)] || {};
const spriteKey = sequence => `sprite|${sequence.signature}`;

function rolesOf(model) {
  return ROLES.filter(role => model.descriptors.some(descriptor => descriptor.roles[role]));
}

function tiersOf(model, role) {
  return model.descriptors.map((descriptor, index) => ({descriptor, index})).filter(t => t.descriptor.roles[role]);
}

function roleUsed(model, role) {
  return model.descriptors.some(descriptor => descriptor.roles[role]?.used);
}

function currentMarker(model, role, tier) {
  return model.descriptors[tier].roles[role]?.impact ?? null;
}

// The 3D impact belongs to the clip, shared by every role bound to it: the review's pick, else the installed marker.
function effectiveImpact(model, role, tier) {
  const decision = clipDecision(model, model.descriptors[tier].roles[role].clip);
  return Number.isFinite(decision.impact) ? decision.impact : currentMarker(model, role, tier);
}

// Melee uses the melee attack sprite; missiles and spells the ranged one (as the MM8 starters do).
function attackSprite(descriptor, role) {
  return descriptor.sprites[role === 'attack_melee' ? 'melee' : 'ranged'];
}

const spriteHasFrames = sequence => Boolean(sequence?.frames.some(frame => frame.image));

// Contact frame of an attack sprite: the review's pick, else sprite_attack_timing.yml; null applies at the end.
function contactFrame(sequence) {
  if (!sequence) {
    return null;
  }
  const decision = decisions[spriteKey(sequence)];
  return decision && 'frame' in decision ? decision.frame : sequence.contactFrame ?? null;
}

function contactSeconds(sequence, frame = contactFrame(sequence)) {
  if (!sequence || !Number.isInteger(frame) || frame < 1 || frame >= sequence.frames.length) {
    return null;
  }
  return sequence.frames.slice(0, frame).reduce((sum, f) => sum + f.seconds, 0);
}

// Clip warp preview (retime_clip.py): the first `end` s play `speed` times faster, easing back to 1x over `ramp` s.
function warpTime(time, warp) {
  if (!warp || warp.speed === 1 || warp.end <= 0) {
    return time;
  }
  const ramp = Math.min(Math.max(warp.ramp ?? 0.1, 0), warp.end);
  const rampStart = warp.end - ramp;
  if (time <= rampStart) {
    return time / warp.speed;
  }
  const slope = (1 - warp.speed) / ramp;
  const span = Math.min(time, warp.end) - rampStart;
  return rampStart / warp.speed + Math.log((warp.speed + slope * span) / warp.speed) / slope
    + Math.max(0, time - warp.end);
}

function unwarpTime(time, warp) {
  if (!warp) {
    return time;
  }
  let low = 0;
  let high = time * Math.max(1, warp.speed) + 1;
  for (let i = 0; i < 40; i++) {
    const middle = (low + high) / 2;
    warpTime(middle, warp) < time ? low = middle : high = middle;
  }
  return (low + high) / 2;
}

// A warp previewed on the clip (not yet baked into the model).
const clipWarp = (model, clip) => clipDecision(model, clip).warp || null;

// Attack sound delay of a sprite: the review's value, else sprite_attack_timing.yml; 0 plays it as the attack starts.
function soundDelayOf(sequence) {
  if (!sequence) {
    return 0;
  }
  const decision = decisions[spriteKey(sequence)];
  return decision && 'soundDelay' in decision ? decision.soundDelay : sequence.soundDelay || 0;
}

// Every sprite (any model, any tier) drawn with the same frames as `sequence`; they share contact and sound delay.
function spriteNamesSharing(sequence) {
  return [...new Set(data.models.flatMap(model => model.descriptors).flatMap(descriptor =>
    ['melee', 'ranged'].map(key => descriptor.sprites[key]))
    .filter(other => other?.signature === sequence.signature).map(other => other.name))].sort();
}

// Timing of one tier's attack: the native action, the moment the game applies it, the recovery and the clip.
function metrics(model, role, tier, impact = effectiveImpact(model, role, tier)) {
  const descriptor = model.descriptors[tier];
  const binding = descriptor.roles[role];
  const warp = clipWarp(model, binding.clip);
  // Clip times below are on the (previewed) warped clock; the picks are stored on the clip's own clock.
  const clipLength = warpTime(model.clips[binding.clip]?.seconds ?? 0, warp);
  const native = binding.nativeSeconds ?? 0.3;
  const sprite = attackSprite(descriptor, role);
  const authoredContact = contactSeconds(sprite);
  const contact = authoredContact ?? native;
  const recovery = descriptor.recoverySeconds.length ? Math.min(...descriptor.recoverySeconds) : 1;
  const melee = role === 'attack_melee';
  // Cooldowns start with the action and are scaled by 0.9-1.2 (startAttack): melee waits the recovery (at least
  // the action + 0.25 s), ranged attacks and spells the recovery plus the action.
  const nextAttack = melee ? Math.max(0.9 * recovery, native + 0.25) : 0.9 * (recovery + native);
  const marked = Number.isFinite(impact) && impact > 0;
  if (marked) {
    impact = warpTime(impact, warp);
  }
  const follow = marked ? Math.max(0, clipLength - impact) : 0;
  const clipEnd = marked ? contact + follow : Math.min(clipLength, native);
  return {
    descriptor, binding, sprite, clip: binding.clip, clipLength, native, contact, recovery, melee, marked, warp,
    // The attack sound plays this long after the attack starts (clamped to the action, as the engine does).
    soundAt: Math.min(Math.max(soundDelayOf(sprite), 0), native),
    contactAuthored: authoredContact != null,
    impact: marked ? impact : null,
    ratio: marked ? impact / contact : null,
    follow,
    clipEnd,
    // From the hit or release to the earliest next attack.
    window: nextAttack - contact,
    nextAttack,
    // The model shows the clip until it ends (holding its last frame until the action ends); an unmarked clip is cut
    // when the action ends.
    presentEnd: marked ? Math.max(native, clipEnd) : native,
    used: binding.used,
  };
}

function clipTimeForGame(game, m) {
  if (m.marked) {
    return Math.min(m.clipLength, game < m.contact ? game / m.contact * m.impact : m.impact + game - m.contact);
  }
  return Math.min(game, m.clipLength);
}

function gameTimeForClip(time, m) {
  if (m.marked) {
    return time < m.impact ? time / m.impact * m.contact : m.contact + time - m.impact;
  }
  return time;
}

function gameLength(m) {
  return Math.max(m.presentEnd + 0.6, m.nextAttack + 0.3, m.native + 0.6);
}

// Both picks made for every tier that plays the role: the billboard contact frame (or an explicit "at the end") and
// the 3D impact (a new one or the installed marker confirmed). Sprites without native frames keep the end.
function roleDone(model, role) {
  return tiersOf(model, role).filter(t => t.descriptor.roles[role].used).every(t => {
    const sprite = attackSprite(t.descriptor, role);
    const spriteDone = !spriteHasFrames(sprite) || 'frame' in (decisions[spriteKey(sprite)] || {});
    const clip = clipDecision(model, t.descriptor.roles[role].clip);
    return spriteDone && (Number.isFinite(clip.impact) || clip.confirmed === true);
  });
}

// Worst state of a role over its used tiers, from the data alone (the list and the summary).
function assess(model, role) {
  const tiers = tiersOf(model, role);
  const decided = roleDone(model, role);
  if (!tiers.some(t => t.descriptor.roles[role].used)) {
    return {sev: 'off', label: 'unused', decided};
  }
  const clip = tiers[0].descriptor.roles[role].clip;
  if (model.source.differingClips.includes(clip)) {
    return {sev: 'bad', label: 'source', decided};
  }
  let sev = 'ok';
  let label = '';
  for (const {index} of tiers.filter(t => t.descriptor.roles[role].used)) {
    const m = metrics(model, role, index);
    if (!m.marked) {
      return {sev: 'bad', label: 'no marker', decided};
    }
    if (m.ratio < WINDUP_OK[0] || m.ratio > WINDUP_OK[1]) {
      sev = 'warn';
      label = `×${fmt(m.ratio)}`;
    } else if (m.follow > m.window + 0.02 && sev === 'ok') {
      sev = 'warn';
      label = 'long tail';
    }
    if (!m.contactAuthored && spriteHasFrames(m.sprite) && sev === 'ok') {
      sev = 'info';
      label = 'at end';
    }
  }
  return {sev, label, decided};
}

// ---------------------------------------------------------------- suggestions
function suggestionsFor(model, role, tier) {
  const m = metrics(model, role, tier);
  const items = [];
  const add = (sev, tag, text, action) => items.push({sev, tag, text, action});
  const what = {attack_melee: 'melee attack', attack_ranged: 'missile attack', cast: 'spell'}[role];
  const hit = m.melee ? 'blow' : 'release';

  if (!m.used) {
    add('info', 'skip', m.descriptor.wimp
      ? 'Wimp AI: the monster never attacks, so this clip is never played in game.'
      : `No ${what} in the monster data for ${m.descriptor.name}: this clip is never played in game.`);
    return items;
  }
  if (m.binding.spellsUseThisClip) {
    add('info', 'note', 'No cast clip is bound, so its spells also play this clip with this marker.');
  }
  if (!model.source.exists) {
    add('bad', 'blocker', 'No accepted source in assets_source for this model.', 'resolve_source');
  } else if (model.source.differingClips.includes(m.clip)) {
    add('bad', 'blocker', `The installed ${m.clip} differs from the accepted source (the runtime copy is newer). `
      + 'Decide which version is accepted and reinstall it before marking.', 'resolve_source');
  }
  for (const project of model.source.newerProjectExports.filter(p => p.clips.includes(m.clip))) {
    add('info', 'note', `A newer project export (${project.path}, +${project.hoursNewer} h) has a different `
      + `${m.clip}. If it is going to be installed, review that clip instead.`);
  }

  // When the game applies the attack: the billboard's contact frame, or the end of the sprite animation.
  if (!spriteHasFrames(m.sprite)) {
    add('info', 'billboard', 'No native frames for this sprite: it keeps the original timing (applied when the '
      + `${fmt(m.native)} s animation ends).`);
  } else if (!m.contactAuthored) {
    add('warn', 'billboard', `Pick the billboard frame that first shows the ${hit}. Until then the game applies it `
      + `when the sprite animation ends (${fmt(m.native)} s), as MM8 does.`);
  } else {
    add('ok', 'billboard', `The game applies the ${what} at ${fmt(m.contact)} s (frame ${contactFrame(m.sprite)}); `
      + `the attack then runs on for ${fmt(m.native - m.contact)} s to the end of the ${fmt(m.native)} s sprite.`);
  }

  // The 3D impact marker.
  const candidate = curves && curves.clip === m.clip ? ` (tracked point: S ${fmt(curves.peakSpeed)} s, `
    + `95 % reach ${fmt(curves.reach95)} s)` : '';
  const clipDecided = clipDecision(model, m.clip);
  if (!m.marked) {
    add('bad', '3D', `No impact marker: the clip plays at its own speed, so the ${hit} at ${fmt(m.contact)} s falls on `
      + 'whatever the clip shows then' + (m.clipLength > m.native + 0.02 ? ` and the clip is cut at ${fmt(m.native)} s`
      : '') + `. Set the impact (I) on the clip's ${hit} frame${candidate}.`, 'add_marker');
  } else if (!Number.isFinite(clipDecided.impact) && clipDecided.confirmed !== true) {
    const comment = m.descriptor.markerComment;
    add('info', '3D', `Marker ${fmt(m.impact, 3)} s is not confirmed yet`
      + (comment ? ` (recorded: “${comment}”).` : ', and no measurement is recorded for it.')
      + ' The wind-up and follow-through advice below follows from it.');
  }
  if (model.history) {
    add('info', 'history', model.history);
  }

  // Wind-up: the clip's [0, impact] is fitted to the time until the game applies the attack.
  if (m.marked) {
    if (m.ratio > WINDUP_OK[1]) {
      add('warn', 'wind-up', `Wind-up ${fmt(m.impact)} s plays ${fmt(m.ratio)}× faster to reach the ${hit} at `
        + `${fmt(m.contact)} s. Trim about ${fmt(m.impact - m.contact * 1.05)} s before the strike (or retime the `
        + 'anticipation), and move the marker with it.', 'trim_windup');
    } else if (m.ratio < WINDUP_OK[0]) {
      add('warn', 'wind-up', `Wind-up ${fmt(m.impact)} s is stretched ${fmt(1 / m.ratio)}× to reach the ${hit} at `
        + `${fmt(m.contact)} s, so it plays in slow motion. Add about ${fmt(m.contact * 0.95 - m.impact)} s of `
        + 'anticipation before the strike, or use a slower clip.', 'add_anticipation');
    } else {
      add('ok', 'wind-up', `Wind-up fits: ${fmt(m.impact)} s plays as ${fmt(m.contact)} s (${fmt(m.ratio)}×).`);
    }
    const contacts = [...new Set(tiersOf(model, role).filter(t => t.descriptor.roles[role].used)
      .map(t => metrics(model, role, t.index).contact))];
    if (contacts.length > 1) {
      add('info', 'note', `Tiers apply the ${hit} at different times (${contacts.map(c => fmt(c)).join(' / ')} s); `
        + `one marker gives ${contacts.map(c => '×' + fmt(m.impact / c)).join(' / ')}.`);
    }
  }

  // After the hit: the rest of the action (whole body), then follow-through (presentation only).
  if (m.marked) {
    const next = m.melee ? 'swing' : (role === 'cast' ? 'spell' : 'shot');
    const inside = Math.min(m.follow, m.native - m.contact);
    const after = Math.max(0, m.clipEnd - m.native);
    if (m.follow > m.window + 0.02) {
      add('warn', 'after hit', `The clip runs ${fmt(m.follow)} s after the ${hit}, but the next ${next} can start `
        + `${fmt(m.window)} s after it` + (m.melee ? ' (a melee cooldown runs from the start of the swing)' : '')
        + `. When the monster attacks again at once, the rest is cut by a ${BLEND} s crossfade. Trim it to about `
        + `${fmt(m.window)} s, easing into Standing.`, 'trim_follow');
    } else if (m.clipEnd < m.native - 0.1) {
      add('warn', 'after hit', `The clip ends ${fmt(m.native - m.clipEnd)} s before the attack does and holds its `
        + `last frame until ${fmt(m.native)} s. Let the clip run at least ${fmt(m.native - m.contact)} s past its `
        + `${hit} frame.`, 'trim_follow');
    } else {
      add('ok', 'after hit', `${fmt(m.follow)} s after the ${hit}: ${fmt(inside)} s while the attack runs on (whole `
        + `body), ${fmt(after)} s after it over standing or walking; fits the ${fmt(m.window)} s before the next `
        + `${next}.`);
    }
  }

  // Start and end poses against Standing frame 0 (the crossfades are only 0.12 s).
  if (poseCheck && poseCheck.clip === m.clip) {
    const endTime = m.marked ? m.clipLength : Math.min(m.clipLength, m.native);
    const end = poseCheck.distanceAt(unwarpTime(endTime, m.warp));
    const start = poseCheck.start;
    const endWord = !m.marked && m.clipLength > m.native + 0.02 ? 'is cut' : 'ends';
    if (end.distance > POSE_TOLERANCE) {
      add('warn', 'pose', `The clip ${endWord} ${Math.round(end.distance * 100)} % of the skeleton height away from `
        + `Standing frame 0 (worst: ${end.node}), so the ${BLEND} s crossfade pops. Ease the last ~0.25 s into `
        + 'Standing frame 0.', 'ease_end');
    } else {
      add('ok', 'pose', `The clip ${endWord} close to Standing frame 0 (${Math.round(end.distance * 100)} %).`);
    }
    if (start.distance > POSE_TOLERANCE) {
      add('warn', 'pose', `The clip starts ${Math.round(start.distance * 100)} % away from Standing frame 0 `
        + `(worst: ${start.node}), so every attack starts with a pop. Start from Standing frame 0.`, 'ease_start');
    }
  } else {
    add('info', 'pose', 'Pose checks appear once the model has loaded.');
  }
  const spec = chargeConfig(model).roles[role];
  if ((role === 'attack_ranged' || role === 'cast') && !spec?.glow.length && !spec?.release) {
    add('info', 'note', 'No glow or release socket: the missile or spell leaves from the body (section 3).');
  }
  return items;
}

// ---------------------------------------------------------------- decisions
function readLocalDecisions() {
  try {
    return JSON.parse(localStorage.getItem(LOCAL_KEY) || '{}');
  } catch {
    return {};
  }
}

// Per key, the copy changed last wins (`updated`); keys deleted on this page stay deleted.
function mergeDecisions(base, changes) {
  const merged = {...base};
  let taken = 0;
  for (const [key, value] of Object.entries(changes)) {
    if (!deletedKeys.has(key) && (!merged[key] || (value.updated || '') > (merged[key].updated || ''))) {
      merged[key] = value;
      taken += 1;
    }
  }
  for (const key of deletedKeys) {
    delete merged[key];
  }
  return {merged, taken};
}

async function fetchServerDecisions() {
  const response = await fetch('/api/decisions');
  if (!response.ok) {
    throw new Error(response.statusText);
  }
  return {version: response.headers.get('ETag'), decisions: await response.json()};
}

// The browser keeps a copy of every change (written before each save), so picks whose save failed are merged back
// into decisions.json on the next load instead of being shadowed by the older server copy.
let recoveredOnLoad = 0;
async function loadDecisions() {
  const local = readLocalDecisions();
  try {
    localStorage.setItem(LOCAL_KEY + ':previous', JSON.stringify(local));
  } catch {}
  try {
    const server = await fetchServerDecisions();
    decisionsVersion = server.version;
    const {merged, taken} = mergeDecisions(server.decisions, local);
    decisions = merged;
    recoveredOnLoad = taken;
  } catch {
    serverSaves = false;
    decisions = local;
  }
}

function setDecision(key, changes) {
  if (changes === null) {
    delete decisions[key];
    deletedKeys.add(key);
  } else {
    decisions[key] = {...(decisions[key] || {}), ...changes, updated: new Date().toISOString()};
    deletedKeys.delete(key);
  }
  clearTimeout(saveTimer);
  if ($('saveState')) {
    $('saveState').textContent = 'Saving…';
  }
  saveTimer = setTimeout(saveDecisions, 400);
  renderList();
}

// Notes and planned changes of one model role.
function updateDecision(model, role, changes) {
  setDecision(decisionKey(model, role), changes);
}

function putDecisions() {
  return fetch('/api/decisions',
    {method: 'PUT', body: JSON.stringify(decisions), headers: {'If-Match': decisionsVersion || ''}});
}

async function saveDecisions() {
  try {
    localStorage.setItem(LOCAL_KEY, JSON.stringify(decisions));
  } catch {}
  let text = 'Saved in this browser only (start serve.py to save decisions.json).';
  if (serverSaves) {
    try {
      let response = await putDecisions();
      if (response.status === 409) {
        // decisions.json changed outside this page (apply_decisions.py, another tab): merge per key and retry.
        const server = await fetchServerDecisions();
        decisions = mergeDecisions(server.decisions, decisions).merged;
        decisionsVersion = server.version;
        response = await putDecisions();
        renderList();
      }
      if (response.ok) {
        decisionsVersion = response.headers.get('ETag');
        text = `Saved to decisions.json at ${new Date().toLocaleTimeString()}.`;
      } else {
        text = `Saving failed (${response.status}); kept in this browser.`;
      }
    } catch {
      text = 'Saving failed; kept in this browser.';
    }
  }
  if ($('saveState')) {
    $('saveState').textContent = text;
  }
}

// ---------------------------------------------------------------- list
function renderList() {
  const filter = $('filter').value;
  const search = $('search').value.trim().toLowerCase();
  const hideWimps = $('hideWimps').checked;
  const list = $('list');
  list.replaceChildren();
  let attention = 0;
  let usedRoles = 0;
  let decided = 0;
  for (const model of data.models) {
    const states = rolesOf(model).map(role => ({role, ...assess(model, role)}));
    const used = states.filter(s => s.sev !== 'off');
    usedRoles += used.length;
    decided += used.filter(s => s.decided).length;
    const needs = used.some(s => (s.sev === 'bad' || s.sev === 'warn') && !s.decided);
    attention += needs ? 1 : 0;
    const text = (model.model + ' ' + model.descriptors.map(d => d.name + ' ' + d.monsters.join(' ')).join(' '))
      .toLowerCase();
    if ((filter === 'attention' && !needs) || (filter === 'open' && used.every(s => s.decided))
      || (search && !text.includes(search)) || (hideWimps && model.descriptors.every(d => d.wimp))) {
      continue;
    }
    const item = document.createElement('div');
    item.className = 'item' + (sel.model === model ? ' selected' : '');
    const allDone = used.length && used.every(s => s.decided);
    item.innerHTML = `<div class="name"><b>${modelLabel(model)}</b>${allDone ? '<span class="done">✓</span>' : ''}</div>`
      + `<div class="tiers">${[...new Set(model.descriptors.map(d => d.name.replace(/ [ABC]$/, '')))].join(', ')}</div>`;
    const chips = document.createElement('div');
    chips.className = 'chips';
    for (const s of states) {
      const chip = document.createElement('span');
      chip.className = `chip sev-${s.sev}`;
      chip.textContent = `${ROLE_SHORT[s.role]}${s.label ? ' ' + s.label : ''}${s.decided && s.sev !== 'off' ? ' ✓' : ''}`;
      chip.title = `${ROLE_LABEL[s.role]}: ${s.sev === 'off' ? 'never played' : s.label || 'fits'}`
        + (s.decided && s.sev !== 'off' ? ' · both frames picked' : '');
      chips.append(chip);
    }
    item.append(chips);
    item.onclick = () => selectModel(model);
    list.append(item);
  }
  $('summary').textContent = `${data.models.length} models · ${usedRoles} attack/cast roles played in game · `
    + `${decided}/${usedRoles} with both frames picked · ${attention} models need attention`
    + (serverSaves ? '' : ' · not saving to disk (open through serve.py)')
    + (recoveredOnLoad ? ` · recovered ${recoveredOnLoad} picks that had only been saved in this browser` : '');
}

// ---------------------------------------------------------------- selection
async function selectModel(model) {
  sel.model = model;
  const roles = rolesOf(model);
  sel.role = roles.find(role => roleUsed(model, role)) || roles[0];
  sel.tier = defaultTier(model, sel.role);
  renderList();
  renderControls();
  renderPanel();
  playing = false;
  $('play').textContent = 'Play';
  gameTime = 0;
  clipTime = 0;
  curves = null;
  poseCheck = null;
  await loadModel(model);
  history.replaceState(null, '', '#' + encodeURIComponent(model.model));
}

function defaultTier(model, role) {
  const tiers = tiersOf(model, role);
  return (tiers.find(t => t.descriptor.roles[role].used) || tiers[0])?.index ?? 0;
}

function selectRole(role) {
  sel.role = role;
  if (!sel.model.descriptors[sel.tier].roles[role]?.used) {
    sel.tier = defaultTier(sel.model, role);
  }
  gameTime = 0;
  clipTime = 0;
  renderControls();
  analyseClip();
  renderPanel();
}

function renderControls() {
  const model = sel.model;
  const roles = $('roles');
  roles.replaceChildren();
  for (const role of rolesOf(model)) {
    const button = document.createElement('button');
    const state = assess(model, role);
    button.textContent = ROLE_LABEL[role] + (state.sev === 'off' ? ' (unused)' : '');
    button.className = role === sel.role ? 'active' : '';
    button.onclick = () => selectRole(role);
    roles.append(button);
  }
  const tier = $('tier');
  tier.replaceChildren();
  for (const {descriptor, index} of tiersOf(model, sel.role)) {
    const option = new Option(descriptor.name + (descriptor.roles[sel.role].used ? '' : ' (unused)'), index);
    tier.append(option);
  }
  tier.value = sel.tier;
  preloadSprites();
}

// ---------------------------------------------------------------- panel
function renderPanel() {
  const model = sel.model;
  const role = sel.role;
  const panel = $('panel');
  if (!model || !role) {
    return;
  }
  const m = metrics(model, role, sel.tier);
  const decision = decisionOf(model, role);
  const clipDecided = clipDecision(model, m.clip);
  const tiers = tiersOf(model, role);
  const hit = m.melee ? 'blow' : 'release';
  const other = ROLES.filter(r => r !== role && model.descriptors[sel.tier].roles[r]?.clip === m.clip);
  let html = `<h2>${modelLabel(model)} · ${ROLE_LABEL[role]}</h2>`;
  html += `<p>${[...new Set(model.descriptors.flatMap(d => d.monsters))].join(', ')}</p>`;
  const d = m.descriptor;
  html += `<p>Clip <b>${m.clip}</b> (${fmt(m.clipLength, 3)} s)`
    + (other.length ? `, also bound to ${other.map(r => ROLE_LABEL[r]).join(' and ')}` : '')
    + '. '
    + `Data: ${d.missiles.length ? 'missiles ' + d.missiles.join(', ') : 'no missiles'}`
    + `${d.spells.length ? ' · spells ' + d.spells.join('; ') : ''} · attack sound ${d.attackSound.name || 'none'}.</p>`;
  if (model.source.differingClips.length) {
    html += `<div class="warnbox">Runtime clips differing from assets_source: ${model.source.differingClips.join(', ')}.</div>`;
  }
  for (const project of model.source.newerProjectExports) {
    html += `<div class="notebox">Newer project export ${project.path} (+${project.hoursNewer} h) differs in `
      + `${project.clips.join(', ')}.</div>`;
  }

  // 1. Billboard contact frame.
  html += `<h3>1 · Billboard ${hit} frame</h3>`;
  if (!m.used) {
    html += '<p class="hint">This tier never plays this attack.</p>';
  } else if (!spriteHasFrames(m.sprite)) {
    html += '<p class="hint">No native frames for this sprite: it keeps the original timing (at the end).</p>';
  } else {
    const sharing = model.descriptors.filter(t => attackSprite(t, role)?.signature === m.sprite.signature)
      .map(t => t.name);
    const frame = contactFrame(m.sprite);
    const picked = 'frame' in (decisions[spriteKey(m.sprite)] || {});
    html += `<p class="hint">Click the first frame that shows the ${hit}; the game applies it as that frame appears. `
      + `Sprite ${m.sprite.name}${sharing.length > 1 ? ` (frames shared by ${sharing.join(', ')})` : ''}.`
      + (picked ? '' : m.sprite.contactFrame != null ? ' Installed pick shown; click to confirm or change.' : '')
      + '</p><div class="film">';
    let start = 0;
    m.sprite.frames.forEach((f, index) => {
      html += `<button class="frame${index === frame ? ' selected' : ''}" data-frame="${index}"${index === 0 ? ' disabled' : ''}>`
        + `<canvas data-image="${f.image}"></canvas>`
        + `<span>${index} · ${fmt(start)}</span></button>`;
      start += f.seconds;
    });
    html += `</div><div class="row"><button id="contactEnd" class="${picked && frame === null ? 'active' : ''}">`
      + `Original: at the end (${fmt(m.native)} s)</button>`
      + (picked ? '<button id="contactClear">Clear pick</button>' : '') + `<span class="hint">${picked
        ? frame === null ? 'Picked: at the end.' : `Picked: frame ${frame} at ${fmt(m.contact)} s.` : 'Not picked yet.'}</span></div>`;
  }

  if (m.used && m.sprite) {
    const delayPicked = 'soundDelay' in (decisions[spriteKey(m.sprite)] || {});
    html += '<div class="row"><label>Attack sound delay <input id="soundDelay" type="number" step="0.01" min="0" '
      + `max="${fmt(m.native)}" value="${soundDelayOf(m.sprite)}" style="width:72px"> s</label><span class="hint">`
      + `0 plays it as the attack starts (default)${delayPicked ? '' : m.sprite.soundDelay ? ' · installed' : ''}. `
      + 'Shared by the tiers above; the waveform below moves with it.</span></div>';
  }

  // 2. 3D impact.
  const marker = currentMarker(model, role, sel.tier);
  html += `<h3>2 · 3D ${hit} frame</h3><div class="metric">`
    + `<span>Installed marker</span><span class="marker">${marker != null ? fmt(marker, 3) + ' s' : 'none'}</span>`;
  if (d.markerComment) {
    html += `<span>Recorded</span><span>${escapeHtml(d.markerComment)}</span>`;
  }
  html += `<span>Reviewed</span><span class="proposed">${Number.isFinite(clipDecided.impact)
    ? fmt(clipDecided.impact, 3) + ' s' : clipDecided.confirmed ? 'marker confirmed' : '–'}</span>`;
  if (curves && curves.clip === m.clip) {
    html += `<span>Tracked: ${escapeHtml(curves.pointName)}</span><span>S ${fmt(curves.peakSpeed, 3)} · R ${fmt(curves.maxReach, 3)} · 95 % ${fmt(curves.reach95, 3)} s</span>`;
  }
  html += '</div><p class="hint">In Raw clip mode, step (←/→) to the clip\'s ' + hit + ' frame and press I. The '
    + `marker is shared by every role and tier bound to ${m.clip}.</p><div class="row">`
    + '<button id="setImpact" title="I">Set at playhead (I)</button>'
    + `<input id="impactInput" type="number" step="0.001" min="0" max="${m.clipLength}" value="${Number.isFinite(clipDecided.impact) ? clipDecided.impact : (marker ?? '')}">`
    + '<button id="applyImpact">Apply</button>'
    + (marker != null ? '<button id="keepMarker">Marker is right</button>' : '')
    + (Number.isFinite(clipDecided.impact) || clipDecided.confirmed ? '<button id="clearImpact">Clear</button>' : '')
    + '</div>';

  const warp = m.warp;
  html += '<div class="row"><label>Speed up the first <input id="warpEnd" type="number" step="0.05" min="0" '
    + `value="${warp?.end ?? 0.4}" style="width:62px"> s by <input id="warpSpeed" type="number" step="0.25" min="0.1" `
    + `value="${warp?.speed ?? 2}" style="width:56px">×, easing over <input id="warpRamp" type="number" step="0.05" `
    + `min="0" value="${warp?.ramp ?? 0.1}" style="width:56px"> s</label><button id="warpPreview">Preview warp</button>`
    + (warp ? '<button id="warpRemove">Remove</button>' : '') + '</div>';
  if (warp) {
    const ownLength = model.clips[m.clip]?.seconds ?? 0;
    const ownImpact = effectiveImpact(model, role, sel.tier);
    html += `<p class="hint">Warp preview: ${m.clip} ${fmt(ownLength)} → ${fmt(m.clipLength)} s`
      + (Number.isFinite(ownImpact) ? `, its impact ${fmt(ownImpact, 3)} → ${fmt(m.impact, 3)} s` : '')
      + '. Preview only: baking it into the model is a retime (retime_clip.py) and a reinstall.</p>';
  }

  if (CHARGE_ROLES.includes(role)) {
    html += chargeSection(model, role, tiers);
  }

  html += '<h3>Timing per tier</h3><table><tr><th>Tier</th><th>Native</th><th>Hit at</th><th>Recovery</th>'
    + '<th>Wind-up</th><th>After hit</th><th>Window</th></tr>';
  for (const {descriptor, index} of tiers) {
    const t = metrics(model, role, index);
    const ratioClass = !t.used ? 'sev-off' : !t.marked ? 'sev-bad'
      : t.ratio < WINDUP_OK[0] || t.ratio > WINDUP_OK[1] ? 'sev-warn' : 'sev-ok';
    const followClass = !t.used ? 'sev-off' : t.follow > t.window + 0.02 ? 'sev-warn' : 'sev-ok';
    html += `<tr class="${index === sel.tier ? 'selected' : ''}${t.used ? '' : ' sev-off'}"><td>${descriptor.name}</td>`
      + `<td>${fmt(t.native)} s</td><td>${fmt(t.contact)} s${t.contactAuthored ? '' : ' (end)'}</td>`
      + `<td>${descriptor.recoverySeconds.map(r => fmt(r)).join('/')} s</td>`
      + `<td class="${ratioClass}">${t.marked ? '×' + fmt(t.ratio) : 'no marker'}</td>`
      + `<td class="${t.marked ? followClass : ''}">${t.marked ? fmt(t.follow) + ' s' : '–'}</td>`
      + `<td>${fmt(t.window)} s</td></tr>`;
  }
  html += '</table><p class="hint">Hit at = when the game applies the attack (the billboard pick, else the end of '
    + 'the sprite). Wind-up = 3D impact ÷ hit time (1 = the clip plays at its own speed). Window = from the hit '
    + 'until the next attack may start.</p>';

  html += '<h3>Suggestions</h3><ul id="suggestions">';
  for (const item of suggestionsFor(model, role, sel.tier)) {
    const ticked = (decision.actions || []).includes(item.action);
    html += `<li class="${item.sev}"><span class="tag">${item.tag}</span>${escapeHtml(item.text)}`
      + (item.action ? `<button data-action="${item.action}">${ticked ? '✓ in plan' : '+ plan'}</button>` : '')
      + '</li>';
  }
  html += '</ul><h3>Notes</h3>'
    + `<textarea id="note" rows="3" placeholder="Notes for this role">${escapeHtml(decision.note || '')}</textarea>`
    + '<details><summary class="hint">Planned clip changes</summary><div id="actions">'
    + Object.entries(ACTIONS).map(([value, label]) =>
      `<label><input type="checkbox" value="${value}"${(decision.actions || []).includes(value) ? ' checked' : ''}> ${label}</label>`).join('')
    + '</div></details><div id="saveState"></div>';
  panel.innerHTML = html;

  for (const button of panel.querySelectorAll('.film .frame')) {
    button.onclick = () => pickContact(Number(button.dataset.frame));
  }
  drawFilm(m.sprite);
  if ($('contactEnd')) {
    $('contactEnd').onclick = () => pickContact(null);
  }
  if ($('contactClear')) {
    $('contactClear').onclick = () => {
      // Keeps a sound delay picked for the same sprite.
      const decision = {...decisions[spriteKey(m.sprite)]};
      delete decision.frame;
      delete decision.seconds;
      setDecision(spriteKey(m.sprite), null);
      if ('soundDelay' in decision) {
        setDecision(spriteKey(m.sprite), decision);
      }
      renderPanel();
    };
  }
  if ($('soundDelay')) {
    $('soundDelay').onchange = () => {
      const delay = Math.max(0, Number($('soundDelay').value) || 0);
      setDecision(spriteKey(m.sprite), {soundDelay: Math.round(delay * 1000) / 1000,
        sprites: spriteNamesSharing(m.sprite)});
      renderPanel();
    };
  }
  if ($('warpPreview')) {
    $('warpPreview').onclick = () => {
      const warp = {end: Number($('warpEnd').value), speed: Number($('warpSpeed').value),
        ramp: Number($('warpRamp').value)};
      if (warp.end > 0 && warp.speed > 0 && warp.ramp >= 0) {
        setDecision(clipKey(model, m.clip), {warp, model: model.model, clip: m.clip});
        renderPanel();
      }
    };
  }
  if ($('warpRemove')) {
    $('warpRemove').onclick = () => {
      const decision = {...clipDecision(model, m.clip)};
      delete decision.warp;
      setDecision(clipKey(model, m.clip), null);
      if (Number.isFinite(decision.impact) || decision.confirmed) {
        setDecision(clipKey(model, m.clip), decision);
      }
      renderPanel();
    };
  }
  $('setImpact').onclick = () => setImpact(clipTime);
  $('applyImpact').onclick = () => setImpact(Number($('impactInput').value));
  if ($('keepMarker')) {
    $('keepMarker').onclick = () => {
      setDecision(clipKey(model, m.clip), {impact: null, confirmed: true, model: model.model, clip: m.clip});
      renderPanel();
    };
  }
  if ($('clearImpact')) {
    $('clearImpact').onclick = () => {
      setDecision(clipKey(model, m.clip), null);
      renderPanel();
    };
  }
  for (const button of panel.querySelectorAll('#suggestions button')) {
    button.onclick = () => {
      const actions = new Set(decisionOf(model, role).actions || []);
      actions.has(button.dataset.action) ? actions.delete(button.dataset.action) : actions.add(button.dataset.action);
      updateDecision(model, role, {actions: [...actions]});
      renderPanel();
    };
  }
  for (const box of panel.querySelectorAll('#actions input')) {
    box.onchange = () => updateDecision(model, role,
      {actions: [...panel.querySelectorAll('#actions input:checked')].map(b => b.value)});
  }
  $('note').oninput = () => updateDecision(model, role, {note: $('note').value});
  if (CHARGE_ROLES.includes(role)) {
    bindChargeSection(model, role);
  }
  $('saveState').textContent = serverSaves ? '' : 'Saving in this browser only (open through serve.py).';
}

const swatch = rgb => `<span style="display:inline-block;width:10px;height:10px;border-radius:2px;vertical-align:-1px;`
  + `background:rgb(${rgb.join(',')})"></span>`;
const hexColour = rgb => '#' + rgb.map(c => c.toString(16).padStart(2, '0')).join('');

function chargeSection(model, role, tiers) {
  const config = chargeConfig(model);
  const spec = config.roles[role] || {glow: [], release: null, glowScale: 1, color: null};
  const picked = Boolean(decisions[fxKey(model)]);
  const melee = role === 'attack_melee';
  let html = melee ? '<h3>3 · Glow</h3>' : '<h3>3 · Charge and release</h3>';
  html += melee
    ? '<p class="hint">Optional: the blow charges at the glow sockets during the wind-up (a fist, a weapon, the eyes) '
      + 'and goes out with sparks as it lands. A melee attack launches nothing, so the glow needs its colour. Shared '
      + 'by every tier of the model.</p>'
    : '<p class="hint">The projectile\'s element charges at the glow sockets during the wind-up and goes out at '
      + 'the release; it leaves the release socket, else the one glow socket or the middle of several. One hand: glow '
      + 'and release on it · both hands: glow on both, release between · staff, eye, mouth: one socket. Shared by '
      + 'every tier of the model.</p>';
  if (melee && spec.glow.length && !spec.color) {
    html += '<div class="warnbox">A melee glow needs a colour (tick Colour below); the game refuses it without one.</div>';
  }
  html += '<div class="metric">';
  for (const {descriptor} of melee ? [] : tiers) {
    const sources = descriptor.roles[role].charge;
    html += `<span>${descriptor.name}</span><span>${sources.length ? sources.map(c => `${swatch(c.rgb)} `
      + `${escapeHtml(c.label)}${c.glows ? '' : ' (no charge)'}`).join(' · ') : 'unused'}</span>`;
  }
  html += melee ? '</div>' : '</div><p class="hint">Colours approximate the game\'s (projectile recipe, spell school, '
    + 'enhanced flight light).</p>';
  const effects = Object.entries(model.descriptors.find(d => d.roles[role])?.roles[role].effects || {});
  if (effects.length) {
    html += `<div class="notebox">Named effects replace the glow: ${effects.map(([e, id]) => `${e} → ${escapeHtml(id)}`)
      .join(', ')} (kept as installed).</div>`;
  }
  html += `<table><tr><th>Socket</th><th>Node</th><th>Glow</th>${melee ? '' : '<th>Release</th>'}<th></th></tr>`;
  for (const [name, socket] of Object.entries(config.sockets)) {
    const offset = typeof socket === 'string' ? '' : ` + [${socket.offset.map(v => fmt(v, 3)).join(', ')}]`;
    const missing = !view?.byOriginalName.has(socketNode(socket));
    html += `<tr><td>${escapeHtml(name)}</td><td class="${missing ? 'sev-bad' : ''}">${escapeHtml(socketNode(socket))}`
      + `${offset}${missing ? ' (missing)' : ''}</td>`
      + `<td><input type="checkbox" data-glow="${name}"${spec.glow.includes(name) ? ' checked' : ''}></td>`
      + (melee ? '' : `<td><input type="radio" name="release" data-release="${name}"`
        + `${spec.release === name ? ' checked' : ''}></td>`)
      + `<td><button data-remove="${name}" title="Remove the socket">✕</button></td></tr>`;
  }
  html += melee ? '</table>' : `<tr><td colspan="3" class="hint">Release from the glow socket(s)</td><td><input `
    + `type="radio" name="release" data-release=""${spec.release ? '' : ' checked'}></td><td></td></tr></table>`;
  const glbSockets = [...(view?.nodeNames || [])].filter(name => /socket/i.test(name)
    && !Object.values(config.sockets).some(socket => socketNode(socket) === name));
  html += `<div class="row"><button id="pickSocket" class="${pickingSocket ? 'active' : ''}">`
    + `${pickingSocket ? 'Click the model… (Esc)' : 'Add socket: click the model'}</button>`
    + glbSockets.map(name => `<button data-add-node="${escapeHtml(name)}">+ ${escapeHtml(name)}</button>`).join('')
    + '</div><div class="row">'
    + `<label>Glow scale <input id="glowScale" type="number" step="0.1" min="0.1" value="${spec.glowScale ?? 1}" `
    + 'style="width:62px"></label>'
    + `<label><input type="checkbox" id="colourOverride"${spec.color ? ' checked' : ''}> Colour</label>`
    + `<input type="color" id="colour" value="${hexColour(spec.color || [255, 255, 255])}"${spec.color ? '' : ' disabled'}>`
    + (picked ? '<button id="chargeReset" title="Forget this page\'s socket picks">Reset to installed</button>' : '')
    + '</div>';
  const differing = model.descriptors.some(d => JSON.stringify(d.sockets) !== JSON.stringify(model.descriptors[0].sockets));
  if (differing) {
    html += '<div class="warnbox">The installed tiers have different sockets; a pick here gives every tier the '
      + 'sockets above.</div>';
  }
  return html + `<p class="hint">${picked ? 'Picked on this page (apply_decisions.py writes it).' : 'Installed.'}</p>`;
}

function bindChargeSection(model, role) {
  const panel = $('panel');
  for (const box of panel.querySelectorAll('[data-glow]')) {
    box.onchange = () => editCharge(config => {
      const spec = config.roles[role] ||= {glow: [], release: null, glowScale: 1, color: null};
      spec.glow = spec.glow.filter(name => name !== box.dataset.glow);
      if (box.checked) {
        spec.glow.push(box.dataset.glow);
      }
      spec.glow = spec.glow.slice(0, 4);
      if (role === 'attack_melee' && spec.glow.length && !spec.color) {
        spec.color = [...MELEE_GLOW_COLOUR];
      }
    });
  }
  for (const radio of panel.querySelectorAll('[data-release]')) {
    radio.onchange = () => editCharge(config => {
      const spec = config.roles[role] ||= {glow: [], release: null, glowScale: 1, color: null};
      spec.release = radio.dataset.release || null;
    });
  }
  for (const button of panel.querySelectorAll('[data-remove]')) {
    button.onclick = () => editCharge(config => {
      const name = button.dataset.remove;
      delete config.sockets[name];
      for (const spec of Object.values(config.roles)) {
        spec.glow = spec.glow.filter(glow => glow !== name);
        spec.release = spec.release === name ? null : spec.release;
      }
    });
  }
  for (const button of panel.querySelectorAll('[data-add-node]')) {
    button.onclick = () => editCharge(config => {
      const node = button.dataset.addNode;
      let name = node.replace(/^socket_/i, '').replace(/[^a-z0-9]+/gi, '_').toLowerCase();
      while (name in config.sockets) {
        name += '_2';
      }
      config.sockets[name] = node;
    });
  }
  $('pickSocket').onclick = () => {
    pickingSocket = !pickingSocket;
    renderPanel();
  };
  $('glowScale').onchange = () => editCharge(config => {
    const value = Number($('glowScale').value);
    config.roles[role].glowScale = value > 0 ? value : 1;
  });
  $('colourOverride').onchange = () => editCharge(config => {
    const hex = $('colour').value;
    config.roles[role].color = $('colourOverride').checked
      ? [1, 3, 5].map(i => parseInt(hex.slice(i, i + 2), 16)) : null;
  });
  $('colour').onchange = () => editCharge(config => {
    const hex = $('colour').value;
    config.roles[role].color = [1, 3, 5].map(i => parseInt(hex.slice(i, i + 2), 16));
  });
  if ($('chargeReset')) {
    $('chargeReset').onclick = () => {
      setDecision(fxKey(model), null);
      renderPanel();
    };
  }
}

// Filmstrip thumbnails cropped to the sequence's figure, anchored like the billboard (bottom centre).
async function drawFilm(sequence) {
  const canvases = [...$('panel').querySelectorAll('.film canvas')];
  const images = sequence.frames.map(frame => spriteImages.get(frame.image));
  if (!canvases.length || images.some(image => !image)) {
    return;
  }
  await Promise.all(images.map(image => image.complete && image.naturalWidth ? null : image.decode().catch(() => null)));
  if (!canvases[0].isConnected || images.some(image => !image.naturalWidth)) {
    return;
  }
  for (const image of images) {
    image.bounds = image.bounds || opaqueBounds(image);
  }
  const left = Math.min(...images.map(i => i.bounds.left));
  const right = Math.max(...images.map(i => i.bounds.right));
  const top = Math.min(...images.map(i => i.bounds.top));
  const bottom = Math.max(...images.map(i => i.bounds.bottom));
  canvases.forEach((canvas, index) => {
    const image = images[index];
    canvas.width = 116;
    canvas.height = 168;
    const context = canvas.getContext('2d');
    const scale = Math.min(canvas.width * 0.94 / (right - left), canvas.height * 0.94 / (bottom - top));
    const anchorX = canvas.width / 2 - (left + right) / 2 * scale;
    const anchorY = canvas.height * 0.97 - bottom * scale;
    context.drawImage(image, anchorX - image.naturalWidth / 2 * scale, anchorY - image.naturalHeight * scale,
      image.naturalWidth * scale, image.naturalHeight * scale);
  });
}

// The contact frame of the selected attack sprite; null keeps the original timing (at the end).
function pickContact(frame) {
  const m = metrics(sel.model, sel.role, sel.tier);
  setDecision(spriteKey(m.sprite),
    {frame, sprites: spriteNamesSharing(m.sprite), seconds: contactSeconds(m.sprite, frame)});
  renderPanel();
}

function setImpact(value) {
  const model = sel.model;
  const role = sel.role;
  const m = metrics(model, role, sel.tier);
  if (!Number.isFinite(value) || value <= 0 || value > m.clipLength + 1e-6) {
    return;
  }
  // The pick is stored on the clip's own clock (a warp preview is not baked into the model yet).
  const impact = Math.round(unwarpTime(value, m.warp) * 1000) / 1000;
  const marker = currentMarker(model, role, sel.tier);
  const same = marker != null && Math.abs(marker - impact) < 0.0005;
  setDecision(clipKey(model, m.clip), {impact: same ? null : impact, confirmed: same, model: model.model, clip: m.clip});
  renderPanel();
}

function escapeHtml(text) {
  return String(text).replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'})[c]);
}

// ---------------------------------------------------------------- model loading and pose evaluation
const loader = new GLTFLoader();

async function loadModel(model) {
  const serial = ++loadSerial;
  showError(`Loading ${model.model}…`);
  let gltf;
  let attachments;
  try {
    [gltf, attachments] = await Promise.all([
      loader.loadAsync(model.url),
      Promise.all(model.attachments.map(a => loader.loadAsync(a.url).then(g => ({attachment: a, gltf: g})))),
    ]);
  } catch (error) {
    if (serial === loadSerial) {
      showError(`Could not load ${model.model}: ${error.message || error}`);
    }
    return;
  }
  if (serial !== loadSerial) {
    return;
  }
  if (view) {
    scene.remove(view.root);
  }
  const root = gltf.scene;
  const byOriginalName = new Map();
  const bySanitizedName = new Map();
  root.traverse(object => {
    const name = object.userData.name || object.name;
    if (!byOriginalName.has(name)) {
      byOriginalName.set(name, object);
    }
    if (!bySanitizedName.has(object.name)) {
      bySanitizedName.set(object.name, object);
    }
  });
  const tips = [];
  for (const {attachment, gltf: part} of attachments) {
    const node = byOriginalName.get(attachment.node);
    if (!node) {
      continue;
    }
    node.add(part.scene);
    const tip = farthestPoint(part.scene);
    if (tip) {
      tip.name = `${attachment.node} tip`;
      part.scene.add(tip);
      tips.push(tip);
    }
  }

  // Compile every clip into per-node interpolants over one pose buffer (10 floats per animated node).
  const nodes = [];
  const nodeIndex = new Map();
  const clips = {};
  for (const clip of gltf.animations) {
    const tracks = [];
    for (const track of clip.tracks) {
      const parsed = THREE.PropertyBinding.parseTrackName(track.name);
      const node = bySanitizedName.get(parsed.nodeName);
      const offset = {position: 0, quaternion: 3, scale: 7}[parsed.propertyName];
      if (!node || offset === undefined) {
        continue;
      }
      if (!nodeIndex.has(node)) {
        nodeIndex.set(node, nodes.length);
        nodes.push(node);
      }
      tracks.push({index: nodeIndex.get(node), offset, interpolant: track.createInterpolant()});
    }
    clips[clip.name] = {duration: clip.duration, tracks};
  }
  const rest = new Float32Array(nodes.length * 10);
  nodes.forEach((node, i) => {
    node.position.toArray(rest, i * 10);
    node.quaternion.toArray(rest, i * 10 + 3);
    node.scale.toArray(rest, i * 10 + 7);
  });
  const upperRoot = model.upperBodyRoot ? byOriginalName.get(model.upperBodyRoot) : null;
  const upper = new Float32Array(nodes.length);
  if (upperRoot) {
    upperRoot.traverse(object => {
      if (nodeIndex.has(object)) {
        upper[nodeIndex.get(object)] = 1;
      }
    });
  }
  const buffers = Array.from({length: 5}, () => new Float32Array(nodes.length * 10));
  if (view?.overlay) {
    scene.remove(view.overlay.group);
  }
  const nodeNames = new Set((gltf.parser.json.nodes || []).map(node => node.name).filter(Boolean));
  view = {model, root, nodes, clips, rest, upper, buffers, tips, byOriginalName, nodeNames, overlay: makeOverlay()};
  scene.add(root);
  scene.add(view.overlay.group);

  // Skeleton extent at Standing frame 0 frames the camera and scales the pose checks.
  applyPose(sample(model.standingClip, 0, buffers[0]));
  const positions = nodes.map(node => node.getWorldPosition(new THREE.Vector3()));
  const box = new THREE.Box3().setFromPoints(positions);
  view.height = Math.max(0.1, box.max.y - box.min.y);
  view.center = box.getCenter(new THREE.Vector3());
  grid.scale.setScalar(view.height * 4);
  showError('');
  analyseClip();
  renderPanel();
  setView('party');
  document.body.dataset.loaded = model.model;
}

function farthestPoint(object) {
  object.updateMatrixWorld(true);
  const inverse = new THREE.Matrix4().copy(object.matrixWorld).invert();
  const point = new THREE.Vector3();
  let best = null;
  let bestDistance = -1;
  object.traverse(mesh => {
    const position = mesh.geometry?.attributes?.position;
    if (!position) {
      return;
    }
    const toRoot = new THREE.Matrix4().multiplyMatrices(inverse, mesh.matrixWorld);
    for (let i = 0; i < position.count; i++) {
      point.fromBufferAttribute(position, i).applyMatrix4(toRoot);
      const distance = point.lengthSq();
      if (distance > bestDistance) {
        bestDistance = distance;
        best = point.clone();
      }
    }
  });
  if (!best) {
    return null;
  }
  const tip = new THREE.Object3D();
  tip.position.copy(best);
  return tip;
}

function sample(clipName, time, out) {
  out.set(view.rest);
  const clip = view.clips[clipName];
  if (!clip) {
    return out;
  }
  const t = Math.min(Math.max(time, 0), clip.duration);
  for (const track of clip.tracks) {
    const values = track.interpolant.evaluate(t);
    const base = track.index * 10 + track.offset;
    for (let k = 0; k < values.length; k++) {
      out[base + k] = values[k];
    }
  }
  return out;
}

function sampleLoop(clipName, time, out) {
  const duration = view.clips[clipName]?.duration || 1;
  return sample(clipName, ((time % duration) + duration) % duration, out);
}

// out = a blended toward b per node with weight(nodeIndex).
function blend(out, a, b, weight) {
  for (let i = 0; i < view.nodes.length; i++) {
    const w = weight(i);
    const o = i * 10;
    for (const k of [0, 1, 2, 7, 8, 9]) {
      out[o + k] = a[o + k] + (b[o + k] - a[o + k]) * w;
    }
    THREE.Quaternion.slerpFlat(out, o + 3, a, o + 3, b, o + 3, w);
  }
  return out;
}

function applyPose(buffer) {
  view.nodes.forEach((node, i) => {
    node.position.fromArray(buffer, i * 10);
    node.quaternion.fromArray(buffer, i * 10 + 3);
    node.scale.fromArray(buffer, i * 10 + 7);
  });
  view.root.updateMatrixWorld(true);
}

// The engine's presentation of one attack at game time `game` (WorldFxSystem::syncActorModels).
function gamePose(game, m) {
  const [attack, frozen, other, out] = view.buffers;
  const model = view.model;
  const walk = $('walk').checked;
  const legs = i => 1 - view.upper[i];
  if (game <= m.presentEnd) {
    sample(m.clip, unwarpTime(clipTimeForGame(game, m), m.warp), attack);
    if (walk && game > m.native) {
      // The AI may walk once the native action ends; the upper body keeps the clip's follow-through.
      sampleLoop(model.walkingClip, game - m.native, other);
      const w = Math.min(1, (game - m.native) / BLEND);
      return blend(out, attack, other, i => legs(i) * w);
    }
    return attack;
  }
  const after = game - m.presentEnd;
  sample(m.clip, unwarpTime(clipTimeForGame(m.presentEnd, m), m.warp), frozen);
  if (walk) {
    sampleLoop(model.walkingClip, game - m.native, other);
    const legsWeight = Math.min(1, (game - m.native) / BLEND);
    const upperWeight = Math.min(1, after / BLEND);
    return blend(out, frozen, other, i => view.upper[i] ? upperWeight : legsWeight);
  }
  sampleLoop(model.standingClip, after, other);
  return blend(out, frozen, other, () => Math.min(1, after / BLEND));
}

// ---------------------------------------------------------------- clip analysis
function analyseClip() {
  if (!view || view.model !== sel.model) {
    return;
  }
  const m = metrics(sel.model, sel.role, sel.tier);
  const clip = view.clips[m.clip];
  if (!clip) {
    showError(`Clip ${m.clip} is not in ${sel.model.model}.`);
    return;
  }
  // Candidate points: animated nodes, sockets and the attachment tips.
  const points = [...view.tips];
  for (const [name, object] of view.byOriginalName) {
    if (view.nodes.includes(object) || /socket/i.test(name)) {
      points.push(object);
    }
  }
  const step = 1 / 120;
  const count = Math.max(2, Math.round(clip.duration / step) + 1);
  const tracks = points.map(() => new Float32Array(count * 3));
  const vector = new THREE.Vector3();
  for (let s = 0; s < count; s++) {
    applyPose(sample(m.clip, Math.min(clip.duration, s * step), view.buffers[0]));
    points.forEach((point, p) => point.getWorldPosition(vector).toArray(tracks[p], s * 3));
  }
  const speeds = tracks.map(track => {
    const speed = new Float32Array(count);
    for (let s = 0; s < count; s++) {
      const a = Math.max(0, s - 1) * 3;
      const b = Math.min(count - 1, s + 1) * 3;
      const dt = (Math.min(count - 1, s + 1) - Math.max(0, s - 1)) * step;
      speed[s] = Math.hypot(track[b] - track[a], track[b + 1] - track[a + 1], track[b + 2] - track[a + 2]) / dt;
    }
    return speed;
  });
  const peak = speeds.map(speed => Math.max(...speed));
  const label = point => point.userData?.name || point.name || 'point';
  // Default point: the node a missile or spell leaves from, else a weapon tip, else the fastest hand, jaw, claw or tail.
  const entries = points.map((point, p) => ({point, p, name: label(point)}));
  const releaseNode = releaseNodeName(sel.model, sel.role);
  const groups = [
    entries.filter(entry => releaseNode && entry.name === releaseNode),
    entries.filter(entry => view.tips.includes(entry.point)),
    entries.filter(entry => /hand|palm|claw|jaw|head|tail|socket|weapon|sword|axe|staff|blade|tip|fist|wing/i
      .test(entry.name) && !/finger|thumb|index|middle|ring|pinky/i.test(entry.name)),
    entries,
  ];
  const pool = groups.find(group => group.length);
  pool.sort((a, b) => peak[b.p] - peak[a.p]);
  const options = points.map((point, p) => ({p, name: label(point)})).sort((a, b) => peak[b.p] - peak[a.p]).slice(0, 30);
  if (!options.some(o => o.p === pool[0].p)) {
    options.unshift({p: pool[0].p, name: pool[0].name});
  }
  const select = $('track');
  select.replaceChildren(...options.map(o => new Option(`${o.name} (peak ${fmt(peak[o.p], 1)}/s)`, o.p)));
  select.value = pool[0].p;
  view.analysis = {clip: m.clip, points, tracks, speeds, count, step};
  computeCurves(pool[0].p);

  // Distances from Standing frame 0, as fractions of the skeleton height.
  const standing = view.nodes.map((node, i) => i);
  applyPose(sample(sel.model.standingClip, 0, view.buffers[0]));
  const reference = view.nodes.map(node => node.getWorldPosition(new THREE.Vector3()));
  const distanceAt = time => {
    applyPose(sample(m.clip, time, view.buffers[0]));
    let worst = {distance: 0, node: ''};
    standing.forEach(i => {
      const d = view.nodes[i].getWorldPosition(vector).distanceTo(reference[i]) / view.height;
      if (d > worst.distance) {
        worst = {distance: d, node: view.nodes[i].userData.name || view.nodes[i].name};
      }
    });
    return worst;
  };
  poseCheck = {clip: m.clip, start: distanceAt(0), distanceAt};
  renderPanel();
}

function computeCurves(p) {
  const a = view.analysis;
  const track = a.tracks[p];
  const speed = a.speeds[p];
  const reach = new Float32Array(a.count);
  for (let s = 0; s < a.count; s++) {
    reach[s] = Math.hypot(track[s * 3], track[s * 3 + 2]);
  }
  const argmax = values => values.reduce((best, value, i) => value > values[best] ? i : best, 0);
  const maxReachIndex = argmax(reach);
  let minBefore = Infinity;
  for (let s = 0; s <= maxReachIndex; s++) {
    minBefore = Math.min(minBefore, reach[s]);
  }
  const threshold = minBefore + 0.95 * (reach[maxReachIndex] - minBefore);
  let reach95Index = maxReachIndex;
  for (let s = 0; s <= maxReachIndex; s++) {
    if (reach[s] >= threshold) {
      reach95Index = s;
      break;
    }
  }
  const point = a.points[p];
  curves = {
    clip: a.clip, speed, reach, step: a.step,
    pointName: point.userData?.name || point.name,
    peakSpeed: argmax(speed) * a.step,
    maxReach: maxReachIndex * a.step,
    reach95: reach95Index * a.step,
  };
  // Party view: look along the direction the tracked point reaches toward.
  const s = maxReachIndex * 3;
  view.forward = new THREE.Vector3(track[s], 0, track[s + 2]);
  if (view.forward.lengthSq() < 1e-6) {
    view.forward.set(0, 0, 1);
  }
  view.forward.normalize();
}

// ---------------------------------------------------------------- charge sockets
// Where an attack or spell charges and leaves: actors.yml `animation.sockets` (a node, or a node plus an offset in its
// space) and the events' glow, release, glow_scale and color (WorldFxSystem ActionEvent). The charge glows at each glow
// socket while the action winds up and the projectile leaves `release`, else the one glow socket or the middle of
// several. A melee blow launches nothing: it glows only in its own colour, out with sparks as the blow lands. Picks are
// stored per model (`fx|<model>`) and apply_decisions.py writes them to every tier.
const CHARGE_ROLES = ['attack_melee', 'attack_ranged', 'cast'];
const MELEE_GLOW_COLOUR = [255, 120, 40];
const fxKey = model => `fx|${model.model}`;
let pickingSocket = false;

function chargeConfig(model) {
  const picked = decisions[fxKey(model)];
  if (picked) {
    return picked;
  }
  const descriptor = model.descriptors[sel.model === model ? sel.tier : 0] || model.descriptors[0];
  const roles = {};
  for (const role of CHARGE_ROLES) {
    const binding = (descriptor.roles[role] ? descriptor : model.descriptors.find(d => d.roles[role]))?.roles[role];
    if (binding) {
      roles[role] = {glow: [...binding.glow], release: binding.release || null, glowScale: binding.glowScale ?? 1,
        color: binding.color || null};
    }
  }
  return {model: model.model, sockets: structuredClone(descriptor.sockets || {}), roles};
}

function editCharge(change) {
  const config = structuredClone(chargeConfig(sel.model));
  delete config.updated;
  change(config);
  setDecision(fxKey(sel.model), config);
  renderPanel();
}

const socketNode = socket => typeof socket === 'string' ? socket : socket?.node;

function socketPosition(socket, out = new THREE.Vector3()) {
  const node = socketNode(socket) ? view.byOriginalName.get(socketNode(socket)) : null;
  if (!node) {
    return null;
  }
  node.updateWorldMatrix(true, false);
  return node.localToWorld(out.fromArray(typeof socket === 'string' ? [0, 0, 0] : socket.offset || [0, 0, 0]));
}

// The release point in the current pose (WorldFxSystem::actorLaunchPoint); null without one.
function releasePosition(spec, sockets) {
  const names = spec?.release ? [spec.release] : spec?.glow || [];
  const points = names.map(name => socketPosition(sockets[name]));
  if (!points.length || points.some(point => !point)) {
    return null;
  }
  return points.reduce((sum, point) => sum.add(point), new THREE.Vector3()).divideScalar(points.length);
}

function releaseNodeName(model, role) {
  if (role === 'attack_melee') {
    return null;
  }
  const config = chargeConfig(model);
  const spec = config.roles[role];
  const name = spec?.release || spec?.glow?.[0];
  return name ? socketNode(config.sockets[name]) : null;
}

// The game's soft blob (ParticleRenderer buildRadialPixels): alpha (1 - r)^2.6 over the quad.
const glowTexture = (() => {
  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = 64;
  const g = canvas.getContext('2d');
  const image = g.createImageData(64, 64);
  for (let y = 0; y < 64; y++) {
    for (let x = 0; x < 64; x++) {
      const r = Math.hypot((x + 0.5) / 32 - 1, (y + 0.5) / 32 - 1);
      image.data.set([255, 255, 255, Math.round(Math.pow(Math.max(0, 1 - Math.min(r, 1)), 2.6) * 255)],
        (y * 64 + x) * 4);
    }
  }
  g.putImageData(image, 0, 0);
  return new THREE.CanvasTexture(canvas);
})();

function makeGlow() {
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({map: glowTexture, blending: THREE.AdditiveBlending,
    depthWrite: false, transparent: true}));
  sprite.renderOrder = 12;
  return sprite;
}

function makeOverlay() {
  const group = new THREE.Group();
  const marker = colour => {
    const mesh = new THREE.Mesh(new THREE.SphereGeometry(1, 12, 8),
      new THREE.MeshBasicMaterial({color: colour, depthTest: false, transparent: true, opacity: 0.9}));
    mesh.renderOrder = 10;
    group.add(mesh);
    return mesh;
  };
  const release = new THREE.Mesh(new THREE.TorusGeometry(1, 0.18, 6, 20),
    new THREE.MeshBasicMaterial({color: 0xff3b3b, depthTest: false}));
  release.renderOrder = 11;
  group.add(release);
  const glows = Array.from({length: 8}, () => {
    const glow = makeGlow();
    group.add(glow);
    return glow;
  });
  const bolt = makeGlow();
  group.add(bolt);
  const trail = new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(), new THREE.Vector3()]),
    new THREE.LineBasicMaterial({color: 0xffffff, depthTest: false, transparent: true, opacity: 0.8}));
  trail.renderOrder = 11;
  group.add(trail);
  return {group, markers: new Map(), marker, release, glows, bolt, trail, releaseCache: null};
}

// Where the projectile leaves, posed at the release (the bolt preview starts there).
function cachedReleasePoint(m, spec, sockets) {
  const overlay = view.overlay;
  const key = JSON.stringify([m.clip, m.contact, m.impact, m.warp, spec, sockets, $('walk').checked]);
  if (overlay.releaseCache?.key !== key) {
    applyPose(gamePose(m.contact, m));
    overlay.releaseCache = {key, point: releasePosition(spec, sockets)};
  }
  return overlay.releaseCache.point;
}

function chargeColour(spec, source) {
  const rgb = spec?.color || source?.rgb || [255, 255, 255];
  return new THREE.Color().setRGB(rgb[0] / 255, rgb[1] / 255, rgb[2] / 255, THREE.SRGBColorSpace);
}

function updateChargeOverlay(m, releasePoint) {
  const overlay = view.overlay;
  const config = chargeConfig(sel.model);
  const spec = CHARGE_ROLES.includes(sel.role) ? config.roles[sel.role] : null;
  const show = $('showSockets').checked;
  const source = (m.binding.charge || [])[0];
  const colour = chargeColour(spec, source);
  const size = view.height * 0.012;
  for (const [name, mesh] of overlay.markers) {
    if (!(name in config.sockets)) {
      mesh.removeFromParent();
      overlay.markers.delete(name);
    }
  }
  for (const [name, socket] of Object.entries(config.sockets)) {
    if (!overlay.markers.has(name)) {
      overlay.markers.set(name, overlay.marker(0xffffff));
    }
    const mesh = overlay.markers.get(name);
    const position = socketPosition(socket);
    mesh.visible = show && Boolean(position);
    if (position) {
      mesh.position.copy(position);
      const glowing = spec?.glow.includes(name);
      mesh.scale.setScalar(glowing ? size * 1.3 : size);
      mesh.material.color.copy(glowing ? colour : new THREE.Color(0xd0d6dc));
    }
  }
  const release = spec && sel.role !== 'attack_melee' ? releasePosition(spec, config.sockets) : null;
  overlay.release.visible = show && Boolean(release);
  if (release) {
    overlay.release.position.copy(release);
    overlay.release.scale.setScalar(size * 2.2);
    overlay.release.quaternion.copy(camera.quaternion);
  }
  // The charge (WorldFxSystem): glows from a quarter to three quarters of the wind-up, out at the release. Outer
  // radius (8 + 24 x charge) x 2 x glow_scale world units, a core of half that; world units / actor scale = model units.
  const glows = Boolean(spec?.glow.length)
    && (Boolean(spec.color) || (sel.role !== 'attack_melee' && (source ? source.glows : true)));
  const charge = gameTime < m.contact ? Math.min(1, Math.max(0, (gameTime / m.contact - 0.25) / 0.5)) : 0;
  const radius = (8 + 24 * charge) * 2 * (spec?.glowScale || 1) / (m.descriptor.scale || 1);
  const core = colour.clone().lerp(new THREE.Color(1, 1, 1), 0.5);
  overlay.glows.forEach((glow, i) => {
    const socket = i < 8 && spec ? config.sockets[spec.glow[i >> 1]] : null;
    const position = glows && charge > 0 && socket ? socketPosition(socket) : null;
    glow.visible = Boolean(position);
    if (position) {
      glow.position.copy(position);
      glow.scale.setScalar(2 * radius * (i % 2 ? 0.5 : 1));
      glow.material.color.copy(i % 2 ? core : colour);
      glow.material.opacity = i % 2 ? 240 / 255 : 160 / 255;
    }
  });
  // After the release, a small marker leaves the release point toward the party (Party view looks from there), slowed
  // down and tied to the release by a line so it reads as the projectile's start, not a stray glow.
  const flight = gameTime - m.contact;
  const flying = Boolean(spec && releasePoint) && flight >= 0 && flight < 0.5;
  overlay.bolt.visible = overlay.trail.visible = flying;
  if (flying) {
    const forward = view.forward || new THREE.Vector3(0, 0, 1);
    overlay.bolt.position.copy(releasePoint).addScaledVector(forward, flight * view.height * 1.2);
    overlay.bolt.scale.setScalar(view.height * 0.08);
    overlay.bolt.material.color.copy(glows ? colour : new THREE.Color(0xffffff));
    overlay.trail.geometry.attributes.position.setXYZ(0, releasePoint.x, releasePoint.y, releasePoint.z);
    overlay.trail.geometry.attributes.position.setXYZ(1, overlay.bolt.position.x, overlay.bolt.position.y,
      overlay.bolt.position.z);
    overlay.trail.geometry.attributes.position.needsUpdate = true;
    overlay.trail.material.color.copy(overlay.bolt.material.color);
  }
}

// Click a body part or held item: a socket on the bone that moves that spot most (skinned) or on the item's node.
function pickSocketAt(event) {
  const rect = canvas.getBoundingClientRect();
  const ndc = new THREE.Vector2((event.clientX - rect.left) / rect.width * 2 - 1,
    -(event.clientY - rect.top) / rect.height * 2 + 1);
  const raycaster = new THREE.Raycaster();
  raycaster.setFromCamera(ndc, camera);
  const hit = raycaster.intersectObject(view.root, true).find(h => h.object.isMesh && h.object.visible);
  if (!hit) {
    showFlash('MISSED');
    return;
  }
  const original = object => object.userData.name || object.name;
  const isNode = object => view.nodeNames.has(original(object)) && view.byOriginalName.get(original(object)) === object;
  let node = null;
  if (hit.object.isSkinnedMesh && hit.face) {
    const {skinIndex, skinWeight} = hit.object.geometry.attributes;
    let nearest = null;
    for (const vertex of [hit.face.a, hit.face.b, hit.face.c]) {
      const position = hit.object.localToWorld(hit.object.getVertexPosition(vertex, new THREE.Vector3()));
      const distance = position.distanceTo(hit.point);
      if (!nearest || distance < nearest.distance) {
        nearest = {vertex, distance};
      }
    }
    let weight = -1;
    for (let k = 0; k < 4; k++) {
      if (skinWeight.getComponent(nearest.vertex, k) > weight) {
        weight = skinWeight.getComponent(nearest.vertex, k);
        node = hit.object.skeleton.bones[skinIndex.getComponent(nearest.vertex, k)];
      }
    }
  }
  for (let object = node ? null : hit.object; object && !node; object = object.parent) {
    node = isNode(object) ? object : null;
  }
  if (!node || !isNode(node)) {
    showFlash('NO NODE');
    return;
  }
  node.updateWorldMatrix(true, false);
  const offset = node.worldToLocal(hit.point.clone()).toArray().map(v => Math.round(v * 10000) / 10000);
  const nodeName = original(node);
  const suggestion = nodeName.replace(/^mixamorig\d*:|^socket_|^b_/i, '').replace(/[^a-z0-9]+/gi, '_').toLowerCase();
  const name = prompt(`Socket on ${nodeName} (offset ${offset.join(', ')}). Name:`, suggestion);
  pickingSocket = false;
  if (!name || !/^[a-z][a-z0-9_]*$/.test(name)) {
    renderPanel();
    return;
  }
  editCharge(config => {
    config.sockets[name] = {node: nodeName, offset};
    const spec = config.roles[sel.role];
    if (spec && !spec.glow.includes(name) && spec.glow.length < 4) {
      spec.glow.push(name);
      if (sel.role === 'attack_melee' && !spec.color) {
        spec.color = [...MELEE_GLOW_COLOUR];
      }
    }
  });
}

function setView(name) {
  if (!view) {
    return;
  }
  const forward = view.forward || new THREE.Vector3(0, 0, 1);
  const side = new THREE.Vector3(forward.z, 0, -forward.x);
  const directions = {
    party: forward.clone(),
    quarter: forward.clone().add(side).normalize(),
    side: side.clone(),
    back: forward.clone().negate(),
  };
  const direction = directions[name] || directions.party;
  controls.target.copy(view.center);
  camera.position.copy(view.center).add(direction.multiplyScalar(view.height * 2.8)).add(new THREE.Vector3(0, view.height * 0.25, 0));
  controls.update();
}

// ---------------------------------------------------------------- sprites
function preloadSprites() {
  const descriptor = sel.model.descriptors[sel.tier];
  for (const sequence of Object.values(descriptor.sprites)) {
    for (const frame of sequence?.frames || []) {
      if (frame.image && !spriteImages.has(frame.image)) {
        const image = new Image();
        image.onload = () => { image.bounds = opaqueBounds(image); };
        image.src = `data/${data.world}/sprites/${frame.image}`;
        spriteImages.set(frame.image, image);
      }
    }
  }
}

// Opaque area relative to the sprite anchor (bottom centre), so frames of different sizes stay aligned.
function opaqueBounds(image) {
  const canvas = document.createElement('canvas');
  canvas.width = image.naturalWidth;
  canvas.height = image.naturalHeight;
  const context = canvas.getContext('2d');
  context.drawImage(image, 0, 0);
  const pixels = context.getImageData(0, 0, canvas.width, canvas.height).data;
  let x0 = canvas.width, y0 = canvas.height, x1 = -1, y1 = -1;
  for (let y = 0; y < canvas.height; y++) {
    for (let x = 0; x < canvas.width; x++) {
      if (pixels[(y * canvas.width + x) * 4 + 3] > 8) {
        x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y);
      }
    }
  }
  if (x1 < 0) {
    return null;
  }
  const w = canvas.width / 2;
  const h = canvas.height;
  return {left: x0 - w, right: x1 + 1 - w, top: y0 - h, bottom: y1 + 1 - h};
}

function drawSprite(game, m) {
  const canvas = $('sprite');
  const rect = canvas.getBoundingClientRect();
  canvas.width = Math.round(rect.width * devicePixelRatio);
  canvas.height = Math.round(rect.height * devicePixelRatio);
  const context = canvas.getContext('2d');
  context.imageSmoothingEnabled = false;
  const descriptor = m.descriptor;
  const attack = descriptor.sprites[m.melee ? 'melee' : 'ranged'];
  const standing = descriptor.sprites.standing;
  const frames = [...(attack?.frames || []), ...(standing?.frames || [])].map(f => spriteImages.get(f.image))
    .filter(image => image?.complete && image.naturalWidth);
  if (!frames.length) {
    context.fillStyle = '#c9ced4';
    context.font = `${12 * devicePixelRatio}px system-ui`;
    context.fillText('no native frames', 10 * devicePixelRatio, canvas.height / 2);
    return;
  }
  const bounds = frames.map(i => i.bounds).filter(Boolean);
  if (!bounds.length) {
    return;
  }
  const left = Math.min(...bounds.map(b => b.left));
  const right = Math.max(...bounds.map(b => b.right));
  const top = Math.min(...bounds.map(b => b.top));
  const bottom = Math.max(...bounds.map(b => b.bottom));
  const scale = Math.min(canvas.width * 0.9 / (right - left), canvas.height * 0.82 / (bottom - top));
  const anchorX = canvas.width / 2 - (left + right) / 2 * scale;
  const anchorY = canvas.height * 0.95 - bottom * scale;
  let image = null;
  if (game < m.native && attack) {
    let time = game;
    for (const frame of attack.frames) {
      if (time < frame.seconds) {
        image = spriteImages.get(frame.image);
        break;
      }
      time -= frame.seconds;
    }
    image = image || spriteImages.get(attack.frames.at(-1)?.image);
  } else if (standing?.frames.length) {
    const total = standing.frames.reduce((sum, f) => sum + f.seconds, 0) || 1;
    let time = (game - m.native) % total;
    for (const frame of standing.frames) {
      if (time < frame.seconds) {
        image = spriteImages.get(frame.image);
        break;
      }
      time -= frame.seconds;
    }
  }
  if (image?.complete && image.naturalWidth) {
    const width = image.naturalWidth * scale;
    const height = image.naturalHeight * scale;
    context.drawImage(image, anchorX - width / 2, anchorY - height, width, height);
  }
}

// ---------------------------------------------------------------- timeline
const timeline = $('timeline');
const ROW_A = [20, 84];
const ROW_B = [128, 174];
const ROW_SOUND = [194, 222];
const PAD_LEFT = 54;
let dragRow = null;

function timelineScale() {
  const width = timeline.clientWidth;
  return {left: PAD_LEFT, right: width - 12};
}

function drawTimeline(m) {
  const width = timeline.clientWidth;
  const height = timeline.clientHeight;
  timeline.width = width * devicePixelRatio;
  timeline.height = height * devicePixelRatio;
  const g = timeline.getContext('2d');
  g.scale(devicePixelRatio, devicePixelRatio);
  g.font = '11px system-ui';
  const {left, right} = timelineScale();
  const xClip = t => left + (right - left) * t / Math.max(m.clipLength, 0.01);
  const xOwn = t => xClip(warpTime(t, m.warp));
  const total = gameLength(m);
  const xGame = t => left + (right - left) * t / total;

  // Row A: the clip at its own speed.
  g.fillStyle = '#9aa4af';
  g.fillText('Clip', 8, ROW_A[0] + 12);
  g.fillText(`${fmt(m.clipLength)} s`, 8, ROW_A[0] + 26);
  g.fillStyle = '#262c34';
  g.fillRect(left, ROW_A[0], right - left, ROW_A[1] - ROW_A[0]);
  axis(g, xClip, m.clipLength, ROW_A[1]);
  if (!m.marked && m.clipLength > m.native + 0.02) {
    g.fillStyle = '#ef6a5e33';
    g.fillRect(xClip(m.native), ROW_A[0], xClip(m.clipLength) - xClip(m.native), ROW_A[1] - ROW_A[0]);
    g.fillStyle = '#ef6a5e';
    g.fillText('cut in game', xClip(m.native) + 3, ROW_A[1] - 4);
  }
  if (curves && curves.clip === m.clip) {
    plot(g, curves.speed, curves.step, xOwn, ROW_A, '#6fb2ff');
    plot(g, curves.reach, curves.step, xOwn, ROW_A, '#f2b04f');
    g.fillStyle = '#c3cbd4';
    for (const [label, time] of [['S', curves.peakSpeed], ['R', curves.maxReach], ['95', curves.reach95]]) {
      g.fillRect(xOwn(time) - 0.5, ROW_A[0] - 6, 1, 6);
      g.fillText(label, xOwn(time) - 3, ROW_A[0] - 8);
    }
  }
  // The attack sound as it plays against the clip: game time mapped onto the clip's clock.
  const sound = m.descriptor.attackSound;
  if (sound?.envelope) {
    drawEnvelope(g, sound, time => {
      const game = m.soundAt + time;
      return game <= m.presentEnd ? xClip(clipTimeForGame(game, m)) : null;
    }, ROW_A[1] - 12, 10, '#7be0a0');
  }
  const marker = currentMarker(sel.model, sel.role, sel.tier);
  const decision = clipDecision(sel.model, m.clip);
  if (marker != null) {
    line(g, xOwn(marker), ROW_A, '#ff9b3d', 2);
    g.fillStyle = '#ff9b3d';
    g.fillText('marker', xOwn(marker) + 3, ROW_A[0] + 11);
  }
  if (Number.isFinite(decision.impact)) {
    line(g, xOwn(decision.impact), ROW_A, '#4fd6e8', 2);
    g.fillStyle = '#4fd6e8';
    g.fillText('reviewed', xOwn(decision.impact) + 3, ROW_A[0] + 24);
  }
  if (m.warp) {
    g.fillStyle = '#c9a6ff';
    g.fillRect(xClip(0), ROW_A[1] - 3, xClip(warpTime(m.warp.end, m.warp)) - xClip(0), 3);
    g.fillText(`warp ${m.warp.speed}×`, xClip(0) + 3, ROW_A[1] - 6);
  }
  line(g, xClip(clipTime), [ROW_A[0] - 2, ROW_A[1] + 2], '#ffffff', 1.5);

  // Row B: the attack in game.
  g.fillStyle = '#9aa4af';
  g.fillText('In game', 8, ROW_B[0] + 12);
  g.fillText(`${fmt(total)} s`, 8, ROW_B[0] + 26);
  const sevColour = !m.marked ? '#ef6a5e' : m.ratio < WINDUP_OK[0] || m.ratio > WINDUP_OK[1] ? '#e5b04d' : '#5cc28a';
  bar(g, xGame(0), xGame(m.contact), ROW_B, sevColour + '55', sevColour,
    `wind-up ${fmt(m.contact)} s` + (m.marked ? ` (clip ×${fmt(m.ratio)})` : ' (no marker)'));
  if (m.native - m.contact > 0.01) {
    bar(g, xGame(m.contact), xGame(m.native), ROW_B, '#6fb2ff30', '#6fb2ff', 'attack runs on');
  }
  if (m.marked && m.clipEnd > m.native) {
    const okEnd = Math.min(m.clipEnd, m.nextAttack);
    bar(g, xGame(m.native), xGame(okEnd), ROW_B, '#5cc28a33', '#7fd3a2', `follow ${fmt(m.clipEnd - m.native)} s`);
    if (m.clipEnd > m.nextAttack) {
      bar(g, xGame(m.nextAttack), xGame(m.clipEnd), ROW_B, '#ef6a5e44', '#ef6a5e', 'cut if it attacks at once');
    }
  }
  g.fillStyle = '#3a414a';
  g.fillRect(xGame(m.presentEnd), ROW_B[0] + 30, xGame(total) - xGame(m.presentEnd), 10);
  g.fillStyle = '#9aa4af';
  g.fillText($('walk').checked ? 'walking' : 'standing', xGame(m.presentEnd) + 3, ROW_B[1] - 1);
  // Billboard frame boundaries over the native action, numbered.
  if (m.sprite?.frames.length) {
    g.fillStyle = '#c9d1da';
    g.font = '9px system-ui';
    let start = 0;
    m.sprite.frames.forEach((f, index) => {
      g.fillRect(xGame(start), ROW_B[0] - 4, 1, 4);
      g.fillText(String(index), xGame(start) + 2, ROW_B[0] - 4);
      start += f.seconds;
    });
    g.font = '11px system-ui';
  }
  line(g, xGame(m.contact), [ROW_B[0] - 14, ROW_B[1]], '#ff5a4a', 2.5);
  g.fillStyle = '#ff5a4a';
  g.fillText(m.melee ? 'HIT' : 'RELEASE', xGame(m.contact) + 3, ROW_B[0] - 14);
  g.setLineDash([4, 3]);
  line(g, xGame(m.nextAttack), ROW_B, '#d6dbe1', 1);
  g.setLineDash([]);
  g.fillStyle = '#d6dbe1';
  g.fillText('next attack ≥', xGame(m.nextAttack) + 3, ROW_B[1] - 12);
  g.fillText('♪', xGame(m.soundAt) + 2, ROW_B[1] - 12);
  axis(g, xGame, total, ROW_B[1]);

  // Sound lane on the game clock: the attack sound from its start (the attack's start plus any delay).
  g.fillStyle = '#9aa4af';
  g.fillText('Sound', 8, ROW_SOUND[0] + 12);
  g.fillStyle = '#20262d';
  g.fillRect(left, ROW_SOUND[0], right - left, ROW_SOUND[1] - ROW_SOUND[0]);
  if (sound?.envelope) {
    drawEnvelope(g, sound, time => xGame(m.soundAt + time), (ROW_SOUND[0] + ROW_SOUND[1]) / 2,
      (ROW_SOUND[1] - ROW_SOUND[0]) / 2 - 1, '#8fc4ff');
    g.fillStyle = '#c9d1da';
    g.fillText(`${sound.name} · ${fmt(sound.seconds)} s` + (m.soundAt > 0 ? ` · delayed ${fmt(m.soundAt)} s` : ''),
      xGame(m.soundAt) + 4, ROW_SOUND[0] + 10);
  } else {
    g.fillStyle = '#7d8792';
    g.fillText('no attack sound', left + 4, ROW_SOUND[0] + 16);
  }
  line(g, xGame(m.contact), ROW_SOUND, '#ff5a4a', 1.5);
  line(g, xGame(gameTime), [ROW_B[0] - 2, ROW_SOUND[1]], '#ffffff', 1.5);
}

// A peak envelope as a filled, mirrored outline; `timeToX` maps seconds into the sound to x (null hides the sample).
function drawEnvelope(g, sound, timeToX, mid, half, colour) {
  const points = sound.envelope.map((value, i) => [timeToX((i + 0.5) * sound.envelopeStep), value])
    .filter(([x]) => x !== null);
  if (points.length < 2) {
    return;
  }
  g.beginPath();
  points.forEach(([x, value], i) => i ? g.lineTo(x, mid - value * half) : g.moveTo(x, mid - value * half));
  for (let i = points.length - 1; i >= 0; i--) {
    g.lineTo(points[i][0], mid + points[i][1] * half);
  }
  g.closePath();
  g.fillStyle = colour + '66';
  g.fill();
  g.strokeStyle = colour;
  g.lineWidth = 1;
  g.stroke();
}

function axis(g, x, length, y) {
  g.fillStyle = '#7d8792';
  for (let t = 0; t <= length + 1e-6; t += 0.25) {
    const major = Math.abs(t - Math.round(t)) < 1e-6 || Math.abs(t * 2 - Math.round(t * 2)) < 1e-6;
    g.fillRect(x(t), y, 1, major ? 5 : 3);
    if (Math.abs(t * 2 - Math.round(t * 2)) < 1e-6) {
      g.fillText(t.toFixed(1), x(t) - 7, y + 15);
    }
  }
}

function plot(g, values, step, x, row, colour) {
  let min = Infinity;
  let max = -Infinity;
  for (const value of values) {
    min = Math.min(min, value);
    max = Math.max(max, value);
  }
  const span = Math.max(max - min, 1e-6);
  g.strokeStyle = colour;
  g.lineWidth = 1.3;
  g.beginPath();
  values.forEach((value, i) => {
    const px = x(i * step);
    const py = row[1] - 4 - (row[1] - row[0] - 8) * (value - min) / span;
    i ? g.lineTo(px, py) : g.moveTo(px, py);
  });
  g.stroke();
}

function line(g, x, row, colour, width) {
  g.strokeStyle = colour;
  g.lineWidth = width;
  g.beginPath();
  g.moveTo(x, row[0]);
  g.lineTo(x, row[1]);
  g.stroke();
}

function bar(g, x0, x1, row, fill, stroke, label) {
  g.fillStyle = fill;
  g.fillRect(x0, row[0] + 4, Math.max(0, x1 - x0), 22);
  g.strokeStyle = stroke;
  g.lineWidth = 1;
  g.strokeRect(x0 + 0.5, row[0] + 4.5, Math.max(0, x1 - x0 - 1), 21);
  g.fillStyle = '#e8ecf1';
  g.save();
  g.beginPath();
  g.rect(x0, row[0], Math.max(0, x1 - x0), 30);
  g.clip();
  g.fillText(label, x0 + 4, row[0] + 19);
  g.restore();
}

function scrub(event) {
  if (!sel.model || !view) {
    return;
  }
  const m = metrics(sel.model, sel.role, sel.tier);
  const rect = timeline.getBoundingClientRect();
  const x = event.clientX - rect.left;
  const {left, right} = timelineScale();
  const fraction = Math.min(1, Math.max(0, (x - left) / (right - left)));
  if (dragRow === 'A') {
    clipTime = fraction * m.clipLength;
    gameTime = gameTimeForClip(clipTime, m);
  } else {
    gameTime = fraction * gameLength(m);
    clipTime = clipTimeForGame(gameTime, m);
  }
  if ($('mode').value === 'raw') {
    gameTime = gameTimeForClip(clipTime, m);
  }
}

timeline.addEventListener('pointerdown', event => {
  const y = event.clientY - timeline.getBoundingClientRect().top;
  dragRow = y < (ROW_A[1] + ROW_B[0]) / 2 ? 'A' : 'B';
  timeline.setPointerCapture(event.pointerId);
  playing = false;
  $('play').textContent = 'Play';
  scrub(event);
});
timeline.addEventListener('pointermove', event => dragRow && scrub(event));
timeline.addEventListener('pointerup', () => { dragRow = null; });

// ---------------------------------------------------------------- playback
const flash = $('flash');
let flashTimer;
function showFlash(text) {
  flash.textContent = text;
  flash.classList.add('show');
  clearTimeout(flashTimer);
  flashTimer = setTimeout(() => flash.classList.remove('show'), 160);
}

let audio = null;
let soundClock = -1;               // game time of the previous frame, for the sound's start crossing
function playAttackSound(m) {
  const url = m.descriptor.attackSound.url;
  if (!$('sound').checked || !url) {
    return;
  }
  if (!audio || audio.dataset.url !== url) {
    audio = new Audio(url);
    audio.dataset.url = url;
  }
  audio.currentTime = 0;
  audio.preservesPitch = false;
  audio.playbackRate = Math.max(0.1, Number($('speed').value));
  audio.play().catch(() => {});
}

function step(direction) {
  if (!sel.model || !view) {
    return;
  }
  playing = false;
  $('play').textContent = 'Play';
  const m = metrics(sel.model, sel.role, sel.tier);
  if ($('mode').value === 'raw') {
    const interval = sel.model.clips[m.clip]?.step || 1 / 30;
    clipTime = Math.min(m.clipLength, Math.max(0, Math.round(clipTime / interval + direction) * interval));
    gameTime = gameTimeForClip(clipTime, m);
  } else {
    gameTime = Math.min(gameLength(m), Math.max(0, gameTime + direction / 60));
    clipTime = clipTimeForGame(gameTime, m);
  }
}

function tick(now) {
  const delta = Math.min(0.1, (now - lastTick) / 1000);
  lastTick = now;
  if (sel.model && view && view.model === sel.model && view.clips) {
    const m = metrics(sel.model, sel.role, sel.tier);
    const raw = $('mode').value === 'raw';
    if (playing) {
      const speed = Number($('speed').value);
      if (raw) {
        const previous = clipTime;
        clipTime += delta * speed;
        if (clipTime > m.clipLength + 0.4) {
          clipTime = 0;
          soundClock = -1;
          if (!$('loop').checked) {
            playing = false;
            $('play').textContent = 'Play';
          }
        }
        const release = m.marked ? m.impact : m.contact;
        if (previous < release && clipTime >= release) {
          showFlash(m.melee ? 'HIT' : 'RELEASE');
        }
        gameTime = gameTimeForClip(Math.min(clipTime, m.clipLength), m);
      } else {
        const previous = gameTime;
        gameTime += delta * speed;
        if (gameTime > gameLength(m)) {
          gameTime = 0;
          soundClock = -1;
          if (!$('loop').checked) {
            playing = false;
            $('play').textContent = 'Play';
          }
        }
        if (previous < m.contact && gameTime >= m.contact) {
          showFlash(m.melee ? 'HIT' : 'RELEASE');
        }
        clipTime = clipTimeForGame(gameTime, m);
      }
    }
    if (playing && soundClock < m.soundAt && gameTime >= m.soundAt) {
      playAttackSound(m);
    }
    soundClock = playing ? gameTime : -1;
    const charge = CHARGE_ROLES.includes(sel.role) && sel.role !== 'attack_melee' ? chargeConfig(sel.model) : null;
    const releasePoint = charge?.roles[sel.role] ? cachedReleasePoint(m, charge.roles[sel.role], charge.sockets) : null;
    applyPose(raw ? sample(m.clip, unwarpTime(Math.min(clipTime, m.clipLength), m.warp), view.buffers[0])
      : gamePose(gameTime, m));
    updateChargeOverlay(m, releasePoint);
    drawSprite(gameTime, m);
    drawTimeline(m);
    const phase = raw ? (clipTime > m.clipLength ? 'clip ended' : 'raw clip')
      : gameTime < m.contact ? (m.marked ? `wind-up (clip ×${fmt(m.ratio)})` : 'action (no marker)')
        : gameTime < m.native ? 'after the hit: the attack runs on'
          : gameTime <= m.presentEnd && m.marked ? 'follow-through' : ($('walk').checked ? 'walking' : 'standing');
    $('badge').textContent = `${m.descriptor.name} · ${ROLE_LABEL[sel.role]} · ${m.clip}\n`
      + `game ${fmt(gameTime, 3)} s · clip ${fmt(Math.min(clipTime, m.clipLength), 3)} s\n${phase}`;
  }
  controls.update();
  renderer.render(scene, camera);
  requestAnimationFrame(tick);
}

// ---------------------------------------------------------------- controls
$('play').onclick = () => {
  if (!sel.model) {
    return;
  }
  playing = !playing;
  $('play').textContent = playing ? 'Pause' : 'Play';
  const m = metrics(sel.model, sel.role, sel.tier);
  if (playing && ($('mode').value === 'raw' ? clipTime >= m.clipLength : gameTime >= gameLength(m) - 0.01)) {
    clipTime = 0;
    gameTime = 0;
  }
  soundClock = gameTime < 0.02 ? -1 : gameTime;
};
$('prev').onclick = () => step(-1);
$('next').onclick = () => step(1);
$('tier').onchange = () => {
  sel.tier = Number($('tier').value);
  preloadSprites();
  renderPanel();
};
$('mode').onchange = () => {
  const m = sel.model && metrics(sel.model, sel.role, sel.tier);
  if (m) {
    gameTime = gameTimeForClip(Math.min(clipTime, m.clipLength), m);
  }
};
$('track').onchange = () => {
  computeCurves(Number($('track').value));
  renderPanel();
};
$('filter').onchange = renderList;
$('search').oninput = renderList;
$('hideWimps').onchange = renderList;
for (const [name, label] of [['party', 'Party view'], ['quarter', '¾'], ['side', 'Side'], ['back', 'Back']]) {
  const button = document.createElement('button');
  button.textContent = label;
  button.onclick = () => setView(name);
  $('views').append(button);
}
let pointerStart = null;
canvas.addEventListener('pointerdown', event => {
  pointerStart = [event.clientX, event.clientY];
});
canvas.addEventListener('pointerup', event => {
  if (pickingSocket && view && pointerStart
    && Math.hypot(event.clientX - pointerStart[0], event.clientY - pointerStart[1]) < 4) {
    pickSocketAt(event);
  }
  pointerStart = null;
});
$('showSockets').onchange = () => {};
addEventListener('keydown', event => {
  if (event.key === 'Escape' && pickingSocket) {
    pickingSocket = false;
    renderPanel();
    return;
  }
  if (event.target.matches('input, textarea, select')) {
    return;
  }
  if (event.code === 'Space') {
    event.preventDefault();
    $('play').click();
  } else if (event.code === 'ArrowLeft' || event.code === 'ArrowRight') {
    event.preventDefault();
    step(event.code === 'ArrowLeft' ? -1 : 1);
  } else if (event.key === 'i' || event.key === 'I') {
    if (sel.model) {
      setImpact(clipTime);
    }
  }
});

// ---------------------------------------------------------------- start
try {
  // ?world=mm8 reviews another world's actors (default mm6).
  const world = new URLSearchParams(location.search).get('world') || 'mm6';
  const response = await fetch(`data/${world}/review_data.json`);
  if (!response.ok) {
    throw new Error(`data/${world}/review_data.json is missing: run build_review_data.py --world ${world}`);
  }
  data = await response.json();
  document.querySelector('h1').textContent = `Attack timing review: ${world.toUpperCase()}`;
  // ?models=mm6_arc1,mm6_gob2 limits the review to those models.
  const only = new URLSearchParams(location.search).get('models');
  if (only) {
    const names = only.split(',').map(name => name.trim().replace(/\.glb$/, '') + '.glb');
    data.models = data.models.filter(model => names.includes(model.model));
  }
} catch (error) {
  showError(String(error.message || error));
  throw error;
}
await loadDecisions();
renderList();
if (recoveredOnLoad > 0) {
  await saveDecisions();
}
const requested = decodeURIComponent(location.hash.slice(1));
const first = data.models.find(model => model.model === requested)
  || data.models.find(model => !$('hideWimps').checked || !model.descriptors.every(d => d.wimp)) || data.models[0];
selectModel(first);
requestAnimationFrame(tick);
document.body.dataset.ready = 'true';
