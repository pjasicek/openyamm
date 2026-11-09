// Party creation study 2026-11-01: shared model, rules, stage scaling and popups for approaches A, B and C.
// The creation rules mirror NewGameScreen.cpp (bonus pool, stat steps, two optional skills) and the caps come
// pre-computed from ClassSkillTable's effective-cap logic in data.js (extract_data.py).
'use strict';

const D = window.PC_DATA;
const ICON = '../../../assets_dev/engine/icons_x2/';
const CLASS_ICON = '../../../assets_dev/engine/hud_x2/menus/classes/';
const AUDIO = '../../../assets_dev/engine/audio/';
const MASTERY = ['None', 'Normal', 'Expert', 'Master', 'Grandmaster'];
const LETTER = '-BEMG';
const LETTER_SHOW = ['–', 'N', 'E', 'M', 'G'];
const STAT_SHORT = ['Mig', 'Int', 'Per', 'End', 'Acc', 'Spd', 'Lck'];
const POOL = 15, MIN_OFFSET = 2, MAX_MEMBERS = 5;

const params = new URLSearchParams(location.search);
const App = {
  ruleset: params.get('ruleset') === 'maw' ? 'maw' : 'standard',
  continent: params.get('continent') || 'antagarich',
  device: params.get('device') || 'desktop',
  party: params.get('party') || 'sample',
  export: params.get('export') === '1',
  members: [],
  sel: 0,
  planMode: false,
  planning: true,       // the skill planner (Plan mode, ⚑ plans); C2 turns it off
  focus: null,          // {m, skill} in touch mode
  render: () => {},
  approach: '',
};

const R = () => D[App.ruleset];
const el = (sel, root = document) => root.querySelector(sel);
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
const touch = () => App.device === 'phone';

// ---------------------------------------------------------------- data helpers
function skillList() { return R().skills; }
function skillIndex(skill) { return R().skills.indexOf(skill); }
function skillName(skill) {
  if (App.ruleset === 'maw' && skill === 'Learning') return 'Ascension';
  return D.skillDisplay[skill] || skill;
}
function skillGroups() {
  const all = new Set(skillList());
  return Object.entries(D.skillGroups).map(([name, skills]) => [name, skills.filter(s => all.has(s))])
    .filter(([, skills]) => skills.length);
}
function portraitById(id) { return R().portraits.find(p => p.id === id); }
function race(m) { return R().races[portraitById(m.portrait).race]; }
function cls(id) { return R().classes[id]; }
function className(id) { return cls(id) ? cls(id).name : '?'; }
function classIcon(id) {
  const c = cls(id);
  if (!c) return CLASS_ICON + 'peasant.png';
  let token = c.canon.toLowerCase();
  if (!D.classIcons.includes(token)) {
    const root = Object.values(R().classes).find(o => o.kind === c.kind && D.classIcons.includes(o.canon.toLowerCase()));
    token = root ? root.canon.toLowerCase() : 'peasant';
  }
  return CLASS_ICON + token + '.png';
}
function continent() { return R().continents.find(c => c.key === App.continent) || R().continents[0]; }
// NewGameScreen startingCasterClassId: only Cleric/Priest and Sorcerer/Necromancer vary by continent.
function casterForContinent(id) {
  if (R().freeSelection) return id;
  const offers = x => continent().classIds.includes(x);
  if (id === 4 || id === 5) return offers(5) ? 5 : 4;
  if (id === 42 || id === 44) return offers(44) ? 44 : 42;
  return id;
}
function classOptions(raceId) {
  const ids = [...new Set(R().races[raceId].classes.map(casterForContinent))].filter(id => cls(id));
  return ids.sort((a, b) => a - b);
}
function combo(m) { return R().combos[`${portraitById(m.portrait).race}:${m.cls}`]; }
function capNow(m, skill) { return LETTER.indexOf(combo(m).now[skillIndex(skill)]); }
function capBest(m, skill) { return LETTER.indexOf(combo(m).best[skillIndex(skill)]); }
function startOf(m, skill) { return combo(m).start[skillIndex(skill)]; }
function fixedSkills(m) { return skillList().filter(s => startOf(m, s) === 'F'); }
function optionalSkills(m) { return skillList().filter(s => startOf(m, s) === 'C'); }
// Which promotion first reaches `level` for this skill (class names), for "after promotion" labels.
function promotionFor(m, skill, level) {
  const i = skillIndex(skill);
  const tree = combo(m).tree;
  const step = Math.min(...tree.filter(n => LETTER.indexOf(n.caps[i]) >= level).map(n => cls(n.id).step));
  return tree.filter(n => LETTER.indexOf(n.caps[i]) >= level && cls(n.id).step === step).map(n => className(n.id));
}
function raceRuleFor(m, skill) { return (race(m).skillRules || []).find(r => r.skill === skill); }
function raceFlat(m, skill) { return (race(m).flatSkills || []).includes(skill); }

// A skill's state for one member: fixed / chosen / option / later (learnable in play) / promo (after promotion) / none
function skillState(m, skill) {
  const start = startOf(m, skill);
  if (start === 'F') return 'fixed';
  if (start === 'C') return m.chosen.includes(skill) ? 'chosen' : 'option';
  if (capNow(m, skill) > 0) return 'later';
  if (capBest(m, skill) > 0) return 'promo';
  return 'none';
}
function has(m, skill) { const s = skillState(m, skill); return s === 'fixed' || s === 'chosen'; }
function coverage(skill) {
  return App.members.map((m, i) => ({i, m})).filter(({m}) => has(m, skill) || m.plan.includes(skill))
    .map(({m, i}) => ({i, planned: !has(m, skill)}));
}
function partyBest(skill) { return Math.max(0, ...App.members.map(m => capBest(m, skill))); }

// ---------------------------------------------------------------- stats (NewGameScreen bonusPoolForState)
function statRule(m, i) { const [base, max, add, drop] = race(m).stats[i]; return {base, max, add, drop}; }
function pool(m) {
  let left = POOL;
  for (let i = 0; i < 7; i++) {
    const {base, add, drop} = statRule(m, i);
    const cur = m.stats[i];
    const [penalty, bonus] = cur >= base ? [drop, add] : [add, drop];
    if (bonus > 0) left += Math.trunc(penalty * (base - cur) / bonus);
  }
  return left;
}
function canInc(m, i) {
  const {base, max, add, drop} = statRule(m, i);
  const cur = m.stats[i];
  const [amount, cost] = cur < base ? [drop, add] : [add, drop];
  return pool(m) >= cost && cur + amount <= max;
}
function inc(m, i) {
  if (!canInc(m, i)) return false;
  const {base, add, drop} = statRule(m, i);
  m.stats[i] += m.stats[i] < base ? drop : add;
  return true;
}
function canDec(m, i) {
  const {base, add, drop} = statRule(m, i);
  const amount = m.stats[i] <= base ? drop : add;
  return m.stats[i] - amount >= base - MIN_OFFSET;
}
function dec(m, i) {
  if (!canDec(m, i)) return false;
  const {base, add, drop} = statRule(m, i);
  m.stats[i] -= m.stats[i] <= base ? drop : add;
  return true;
}
function statTrait(m, i) {
  const {add, drop} = statRule(m, i);
  if (add > 1) return {cls: 'strong', mark: '▲', text: `+${add} per point`};
  if (drop > 1) return {cls: 'weak', mark: '▼', text: `${drop} points per +1`};
  return {cls: '', mark: '', text: '1 point per +1'};
}
function ready(m) { return pool(m) === 0 && (m.chosen.length === 2 || optionalSkills(m).length < 2 && m.chosen.length === optionalSkills(m).length); }

// ---------------------------------------------------------------- members
function voicesById() { return Object.fromEntries(D.voices.map(v => [v.id, v])); }
// Voices are named after the portrait whose own voice they are (the lowest such portrait number), so portrait #N
// speaks with "Voice N" unless it shares another portrait's voice; voices no offered portrait owns are "extra".
function voiceLabel(id) {
  const owners = voiceOwners(id);
  return owners.length ? `Voice ${Math.min(...owners.map(p => p.id))}` : `Extra voice ${id + 1}`;
}
function voiceOwners(id) { return R().portraits.filter(p => p.voice === id); }
function voiceKindFor(p) {
  const v = voicesById()[p.voice];
  return v ? v.kind : (p.sex ? 'Woman' : 'Man');
}
function voicesFor(m, all) {
  const p = portraitById(m.portrait);
  const kind = voiceKindFor(p);
  const usable = new Set(R().portraits.map(o => o.voice));
  return D.voices.filter(v => v.lines.length && (all || (v.kind === kind && usable.has(v.id))));
}
function defaultName(p, index) {
  const list = p.sex ? D.names.female : D.names.male;
  return list[(p.id * 7 + index * 3) % list.length];
}
function makeMember(portraitId, classId, index) {
  const p = portraitById(portraitId);
  const options = classOptions(p.race);
  const wanted = casterForContinent(classId ?? p.defClass);
  const c = options.includes(wanted) ? wanted : (options.find(x => x >= wanted) ?? options[0]);
  const m = {portrait: p.id, cls: c, voice: p.voice, name: defaultName(p, index), chosen: [], plan: [], stats: []};
  m.stats = race(m).stats.map(s => s[0]);
  return m;
}
function setPortrait(m, portraitId) {
  const oldClass = m.cls;
  const p = portraitById(portraitId);
  const keepVoice = m.voice !== portraitById(m.portrait).voice;
  m.portrait = portraitId;
  const options = classOptions(p.race);
  m.cls = options.includes(oldClass) ? oldClass : (options.find(x => x >= oldClass) ?? options[0]);
  if (!keepVoice || voiceKindFor(p) !== (voicesById()[m.voice] || {}).kind) m.voice = p.voice;
  m.stats = race(m).stats.map(s => s[0]);
  refreshSkills(m);
}
function setClass(m, classId) { m.cls = classId; refreshSkills(m); }
function refreshSkills(m) {
  const options = optionalSkills(m);
  m.chosen = m.chosen.filter(s => options.includes(s));
  m.plan = m.plan.filter(s => capBest(m, s) > 0 && !has(m, s));
}
function toggleChosen(m, skill) {
  const state = skillState(m, skill);
  if (state === 'chosen') { m.chosen = m.chosen.filter(s => s !== skill); return true; }
  if (state !== 'option') {
    if (state === 'fixed') toast(`${skillName(skill)} is a fixed ${className(m.cls)} skill`);
    else if (state === 'later') toast(`${skillName(skill)}: not a starting choice — a teacher can teach it later${App.planning ? ' (plan it)' : ''}`);
    else if (state === 'promo') toast(`${skillName(skill)} opens after promotion to ${promotionFor(m, skill, 1).join(' / ')}`);
    else toast(`${className(m.cls)} can never learn ${skillName(skill)}`);
    return false;
  }
  if (m.chosen.length >= 2) { toast('Only two additional skills can be selected — remove one first'); return false; }
  m.chosen.push(skill);
  m.plan = m.plan.filter(s => s !== skill);
  return true;
}
function togglePlan(m, skill) {
  if (has(m, skill)) { toast(`${m.name} already starts with ${skillName(skill)}`); return false; }
  if (capBest(m, skill) === 0) { toast(`${className(m.cls)} can never learn ${skillName(skill)}`); return false; }
  m.plan = m.plan.includes(skill) ? m.plan.filter(s => s !== skill) : [...m.plan, skill];
  return true;
}
// Click on a skill for member index mi. Mouse: act; touch: first tap focuses (card with actions).
function skillTap(mi, skill, anchor) {
  const m = App.members[mi];
  App.sel = mi;
  if (touch()) {
    App.focus = {m: mi, skill};
    App.render();
    showCard(mi, skill, anchor, true);
    return;
  }
  if (App.planMode) togglePlan(m, skill); else toggleChosen(m, skill);
  App.render();
}

// stat spends: [stat index, +presses] pairs.
const SAMPLE = {
  standard: [
    {p: 1, c: 16, chosen: ['Shield', 'ChainArmor'], plan: ['Armsmaster', 'Bodybuilding'], spend: [[0, 5], [3, 5], [4, 3], [5, 2]]},
    {p: 34, c: 4, chosen: ['Meditation', 'Merchant'], plan: ['MindMagic'], spend: [[2, 4], [3, 2]]},
    {p: 62, c: 34, chosen: ['DisarmTraps'], plan: ['Perception'], spend: [[4, 5], [5, 5]]},
    {p: 10, c: 42, chosen: ['AirMagic', 'IdentifyItem'], plan: ['WaterMagic', 'EarthMagic'], spend: [[1, 8], [5, 4], [6, 3]]},
    {p: 56, c: 12, chosen: [], plan: [], spend: []},
  ],
  maw: [
    {p: 1, c: 16, chosen: ['Spear', 'ChainArmor'], plan: ['Armsmaster'], spend: [[0, 5], [3, 5], [4, 3], [5, 2]]},
    {p: 34, c: 59, chosen: [], plan: [], spend: [[2, 4]]},
    {p: 62, c: 56, chosen: ['Shield'], plan: [], spend: [[0, 5], [3, 5]]},
    {p: 10, c: 62, chosen: ['AirMagic', 'IdentifyItem'], plan: ['WaterMagic'], spend: [[1, 8], [5, 4], [6, 3]]},
    {p: 56, c: 34, chosen: [], plan: [], spend: []},
  ],
};
function buildParty() {
  App.members = [];
  if (App.party === 'fresh') {
    App.members.push(makeMember(1, 16, 0));
  } else {
    SAMPLE[App.ruleset].forEach((s, index) => {
      const m = makeMember(s.p, s.c, index);
      for (const skill of s.chosen) if (skillState(m, skill) === 'option' && m.chosen.length < 2) m.chosen.push(skill);
      if (App.planning) for (const skill of s.plan) if (capBest(m, skill) > 0 && !has(m, skill)) m.plan.push(skill);
      s.spend.forEach(([stat, times]) => { for (let k = 0; k < times; k++) inc(m, stat); });
      App.members.push(m);
    });
  }
  App.sel = 0;
}
function addMember() {
  if (App.members.length >= MAX_MEMBERS) return;
  const used = new Set(App.members.map(m => m.portrait));
  const p = R().portraits.find(o => !used.has(o.id) && o.start !== false) || R().portraits[0];
  App.members.push(makeMember(p.id, null, App.members.length));
  App.sel = App.members.length - 1;
  App.render();
}
function removeMember(i) {
  if (App.members.length <= 1) return;
  App.members.splice(i, 1);
  if (i < App.sel) App.sel--;   // keep the same character selected
  App.sel = Math.min(App.sel, App.members.length - 1);
  App.render();
}
function resetMember(i) {
  const m = App.members[i];
  App.members[i] = makeMember(m.portrait, m.cls, i);
  App.members[i].name = m.name;
  App.members[i].voice = m.voice;
  App.render();
}
function partyStatus() {
  const notReady = App.members.map((m, i) => ({m, i})).filter(({m}) => !ready(m));
  if (!notReady.length) return {ok: true, text: `${App.members.length} adventurer${App.members.length > 1 ? 's' : ''} ready.`};
  const {m} = notReady[0];
  const parts = [];
  if (pool(m) > 0) parts.push(`${pool(m)} bonus point${pool(m) > 1 ? 's' : ''}`);
  if (pool(m) < 0) parts.push(`${-pool(m)} points over`);
  const need = Math.min(2, optionalSkills(m).length) - m.chosen.length;
  if (need > 0) parts.push(`${need} skill choice${need > 1 ? 's' : ''}`);
  return {ok: false, text: `<b>${esc(m.name)}</b> still needs ${parts.join(' and ')}.` + (notReady.length > 1 ? ` (${notReady.length} not ready)` : '')};
}

// ---------------------------------------------------------------- small render helpers
function mastery(now, best, opts = {}) {
  if (now === 0 && best === 0) return `<span class="ml dim">–</span>`;
  const later = best > now ? `<span class="later mc${best}">›${LETTER_SHOW[best]}</span>` : '';
  const nowText = now > 0 ? `<span class="now" data-c="${now}">${opts.long ? MASTERY[now] : LETTER_SHOW[now]}</span>` : '';
  return `<span class="ml">${nowText}${later}</span>`;
}
function ladder(now, best) {
  let out = '<span class="ladder">';
  for (let i = 1; i <= 4; i++) out += `<i class="${i <= now ? 'n' : i <= best ? 'p' : ''}"></i>`;
  return out + '</span>';
}
function badge(i, planned) { return `<span class="mb${planned ? ' planned' : ''}" data-m="${i}">${i + 1}</span>`; }
function coverageBadges(skill, except) {
  return coverage(skill).filter(c => c.i !== except).map(c => badge(c.i, c.planned)).join('');
}
function raceMarks(m, skill) {
  let out = '';
  const rule = raceRuleFor(m, skill);
  if (rule) out += `<span class="racemark" title="${esc(rule.text)}">${esc(race(m).name.slice(0, 3))}</span>`;
  if (raceFlat(m, skill)) out += `<span class="racemark flatmark" title="${esc(race(m).name)}: +3 skill">+3</span>`;
  return out;
}
function portraitImg(p, cls = '') { return `<img src="${ICON}${p.img}" alt="" draggable="false" class="${cls}">`; }

// The racial bonuses as compact text pieces (used on cards and columns).
function raceSummary(m, opts = {}) {
  const r = race(m);
  const pieces = [];
  r.stats.forEach((s, i) => {
    const t = statTrait(m, i);
    if (t.cls) pieces.push(`<span class="tr ${t.cls}" style="width:auto">${t.mark}${opts.long ? D.statNames[i] : STAT_SHORT[i]}${opts.long ? ` ${s[0]}` : ''}</span>`);
  });
  const skills = raceRuleGroups(r).map(g => `<span class="rs">${esc(opts.long ? `${g.effect}: ${g.names.join(', ')}` : `${g.names.join(', ')} ${shortEffect(g.effect)}`)}</span>`);
  const notes = (r.notes || []).map(n => `<span class="rs">${esc(n)}</span>`);
  return {stats: pieces, skills, notes};
}
// Race skill rules grouped by effect: "+1 mastery rank: Merchant, Perception".
function raceRuleGroups(r) {
  const groups = [];
  for (const rule of r.skillRules || []) {
    const cut = rule.text.indexOf(': ');
    const name = rule.text.slice(0, cut), effect = rule.text.slice(cut + 2);
    const label = effect.charAt(0).toUpperCase() + effect.slice(1);
    const g = groups.find(x => x.effect === label);
    if (g) g.names.push(name); else groups.push({effect: label, names: [name]});
  }
  return groups;
}
function shortEffect(effect) {
  return effect.replace(/^At least /, '≥').replace(/, \+1 mastery rank/, ' +1').replace(/^\+1 mastery rank$/, '+1')
    .replace(' (warrior classes)', '*').replace(/ \(not .* line\)/, '').replace('Expert', 'E').replace('Master', 'M');
}
function shortRule(rule) {
  return rule.text.replace(/: at least /, ' ≥').replace(/, \+1 mastery rank/, ' +1').replace(/: \+1 mastery rank/, ' +1')
    .replace(' (warrior classes)', '*').replace(/ \(not .* line\)/, '');
}

// ---------------------------------------------------------------- toast / card
let toastTimer = 0;
function toast(text) {
  const t = el('#toast');
  t.textContent = text;
  t.classList.add('on');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove('on'), 2200);
}

// Skill card: description, a structured mastery table for this member (now / after promotion / never), who covers it.
function showCard(mi, skill, anchor, withActions) {
  const m = App.members[mi];
  const card = el('#card');
  const text = R().skillText[skill] || {desc: '', m: ['', '', '', '']};
  const now = capNow(m, skill), best = capBest(m, skill);
  let rows = '';
  for (let level = 1; level <= 4; level++) {
    let av;
    if (now >= level) av = `<span class="mc${Math.max(level, 2)}">✓ now</span>`;
    else if (best >= level) av = `<span class="mc3">${esc(promotionFor(m, skill, level).join(' / '))}</span>`;
    else av = `<span class="dim">never</span>`;
    const reach = now >= level ? 'now' : best >= level ? 'promo' : 'never';
    rows += `<tr class="${reach}"><td class="lv mc${level}">${MASTERY[level]}</td><td>${esc(text.m[level - 1] || '')}</td><td class="av">${av}</td></tr>`;
  }
  const state = skillState(m, skill);
  const stateText = {fixed: 'Fixed starting skill', chosen: 'Chosen starting skill', option: 'Can be chosen as a starting skill',
    later: 'Learnable later from a teacher', promo: 'Learnable after promotion', none: 'Never learnable for this class'}[state];
  const rule = raceRuleFor(m, skill);
  const who = coverage(skill).map(c => `${badge(c.i, c.planned)} ${esc(App.members[c.i].name)}${c.planned ? ' (plan)' : ''}`).join(' &nbsp; ');
  let acts = '';
  if (withActions) {
    const canChoose = state === 'option' || state === 'chosen';
    acts = `<div class="acts">
      ${canChoose ? `<button class="btn small" data-act="choose">${state === 'chosen' ? 'Remove' : 'Choose'}</button>` : ''}
      ${App.planning && state !== 'fixed' && state !== 'chosen' && best > 0 ? `<button class="btn small quiet" data-act="plan">${m.plan.includes(skill) ? 'Unplan' : 'Plan for later'}</button>` : ''}
      <button class="btn small quiet" data-act="close" style="margin-left:auto">Close</button></div>`;
  }
  card.innerHTML = `<div class="ct"><span class="h2">${esc(skillName(skill))}</span>${mastery(now, best)}<span class="caption" style="margin-left:auto">${esc(m.name)} · ${esc(className(m.cls))}</span></div>
    <div class="cd">${esc(text.desc)}</div>
    <div class="caption" style="margin-bottom:4px">${stateText}${rule ? ` · <span style="color:#b7d38a">${esc(rule.text)}</span>` : ''}</div>
    <table>${rows}</table>
    <div class="who"><span class="caption">Party</span> ${who || '<span class="dim">nobody yet</span>'}</div>${acts}`;
  card.classList.add('on');
  // position near the anchor, inside the stage
  const stage = el('#stage').getBoundingClientRect();
  const scale = stage.width / 1600;
  const a = anchor ? anchor.getBoundingClientRect() : {left: stage.left + 560 * scale, right: stage.left + 560 * scale, top: stage.top + 300 * scale, bottom: stage.top + 300 * scale};
  const ax = (a.left - stage.left) / scale, ar = (a.right - stage.left) / scale;
  const at = (a.top - stage.top) / scale, ab = (a.bottom - stage.top) / scale;
  const h = card.offsetHeight, w = card.offsetWidth;
  let x = ar + 12;
  if (x + w > 1580) x = ax - w - 12;
  if (x < 20) x = Math.min(1580 - w, Math.max(20, ax));
  let y = Math.min(Math.max(20, at - 20), 880 - h);
  if (x === Math.min(1580 - w, Math.max(20, ax))) y = at - h - 10 < 20 ? Math.min(ab + 10, 880 - h) : at - h - 10;
  card.style.left = `${x}px`;
  card.style.top = `${y}px`;
  card.querySelectorAll('[data-act]').forEach(b => b.onclick = e => {
    e.stopPropagation();
    if (b.dataset.act === 'choose') toggleChosen(m, skill);
    if (b.dataset.act === 'plan') togglePlan(m, skill);
    hideCard();
    App.focus = null;
    App.render();
  });
}
function hideCard() { el('#card').classList.remove('on'); }

// Desktop: hover shows the card; right button (held) shows it too, matching the game's RMB help.
function wireSkillEvents(root) {
  root.querySelectorAll('[data-skill]').forEach(node => {
    const mi = Number(node.dataset.m ?? App.sel), skill = node.dataset.skill;
    node.addEventListener('click', e => { e.stopPropagation(); skillTap(mi, skill, node); });
    node.addEventListener('contextmenu', e => { e.preventDefault(); if (!touch()) showCard(mi, skill, node, false); });
    node.addEventListener('mouseenter', () => { if (!touch() && App.hoverCards !== false) showCard(mi, skill, node, false); });
    node.addEventListener('mouseleave', () => { if (!touch()) hideCard(); });
  });
}

// ---------------------------------------------------------------- modal popups
function openModal(html, rect) {
  const modal = el('#modal');
  modal.innerHTML = `<div class="veil"></div><div class="dlg" style="left:${rect[0]}px;top:${rect[1]}px;width:${rect[2]}px;height:${rect[3]}px">${html}</div>`;
  modal.classList.add('on');
  el('.veil', modal).onclick = closeModal;
  modal.querySelectorAll('[data-close]').forEach(b => b.onclick = closeModal);
  hideCard();
  return el('.dlg', modal);
}
function closeModal() { el('#modal').classList.remove('on'); el('#modal').innerHTML = ''; App.render(); }

// Portrait grid: every portrait, grouped by race with the race's bonuses on the group header.
function openPortraitPicker(mi) {
  const m = App.members[mi];
  let filter = 'all';
  const draw = () => {
    const usedBy = Object.fromEntries(App.members.map((o, i) => [o.portrait, i]));
    const byRace = {};
    for (const p of R().portraits) {
      if (filter === 'male' && p.sex !== 0) continue;
      if (filter === 'female' && p.sex !== 1) continue;
      (byRace[p.race] ||= []).push(p);
    }
    const order = [0, 7, 8, 9, 2, 3, 4, 1, 5, 6, 10];
    let html = '';
    for (const raceId of order) {
      const list = byRace[raceId];
      if (!list) continue;
      const r = R().races[raceId];
      const probe = {portrait: list[0].id, cls: 0};
      const sum = raceSummary(probe);
      html += `<div class="pg-race"><span class="h2">${esc(r.name)}</span><span class="rb">${sum.stats.join(' ')} ${sum.skills.length ? ' · ' + sum.skills.join(', ') : ''}${sum.notes.length ? ' · ' + sum.notes.join(' · ') : ''}</span></div><div class="pg-grid">`;
      for (const p of list) {
        const inParty = usedBy[p.id];
        html += `<button class="pg-tile" data-p="${p.id}" aria-pressed="${p.id === m.portrait}">
          <span class="portrait">${portraitImg(p)}<span class="pnum">#${p.id}</span>${inParty !== undefined && inParty !== mi ? `<span class="inparty">${badge(inParty)}</span>` : ''}</span>
          <span class="vlab">${p.sex ? '♀' : '♂'} ${voiceLabel(p.voice)}${p.note && !p.start ? ' · ' + esc(p.note) : ''}</span></button>`;
      }
      html += '</div>';
    }
    dlg.querySelector('.body').innerHTML = html;
    dlg.querySelectorAll('.pg-filter button').forEach(b => b.setAttribute('aria-pressed', b.dataset.f === filter));
    dlg.querySelectorAll('.pg-tile').forEach(b => b.onclick = () => {
      setPortrait(m, Number(b.dataset.p));
      playVoiceLine(m.voice, 'ChooseMe');
      closeModal();
    });
  };
  const dlg = openModal(`<div class="dlg-head"><span class="h2">Choose Portrait</span>
      <span class="pg-filter"><button class="btn tiny quiet" data-f="all">All</button><button class="btn tiny quiet" data-f="male">Male</button><button class="btn tiny quiet" data-f="female">Female</button></span>
      <span class="caption">The portrait sets the race · # is the portrait number, the voice shown is its own</span>
      <button class="btn small quiet x" data-close>Close</button></div><div class="body"></div>`, [70, 40, 1460, 820]);
  dlg.querySelectorAll('.pg-filter button').forEach(b => b.onclick = () => { filter = b.dataset.f; draw(); });
  draw();
}

// Structured mastery table for a class line with this race: rows skills, columns start class + promotions.
function masteryTableHtml(m, classId, opts = {}) {
  const raceId = portraitById(m.portrait).race;
  const c = R().combos[`${raceId}:${classId}`];
  const tree = c.tree;
  let head = '<tr><th></th><th class="st"></th>' + tree.map(n => `<th class="cls">${esc(className(n.id)).replace(/ /, '<br>')}</th>`).join('') + '</tr>';
  let body = '';
  for (const [group, skills] of skillGroups()) {
    const rows = skills.filter(s => tree.some(n => n.caps[skillIndex(s)] !== '-'));
    if (!rows.length) continue;
    body += `<tr class="grp"><td colspan="${tree.length + 2}">${group}</td></tr>`;
    for (const s of rows) {
      const i = skillIndex(s);
      const st = c.start[i];
      let prev = 0;
      const cells = tree.map((n, k) => {
        const v = LETTER.indexOf(n.caps[i]);
        const parentStep = k === 0 ? -1 : cls(n.id).step;
        const base = k === 0 ? 0 : LETTER.indexOf(tree[0].caps[i]);
        const cell = `<td class="${k > 0 && v > base ? 'gain' : ''}"><span class="mc${v}">${v ? LETTER_SHOW[v] : '<span class=dim>·</span>'}</span></td>`;
        prev = v;
        return cell;
      }).join('');
      const glyph = st === 'F' ? '<span class="sg fixed" title="fixed starting skill"></span>' : st === 'C' ? '<span class="sg option" title="starting choice"></span>' : '';
      body += `<tr><td class="sk">${esc(skillName(s))}${raceMarks(m, s)}</td><td class="st">${glyph}</td>${cells}</tr>`;
    }
  }
  return `<table class="mt">${head}${body}</table>
    <div class="caption" style="margin-top:8px;letter-spacing:.5px;text-transform:none">◆ fixed starting skill · ○ starting choice · shaded: rank gained by that promotion · N/E/M/G = Normal, Expert, Master, Grandmaster</div>`;
}

function openClassPicker(mi) {
  const m = App.members[mi];
  const raceId = portraitById(m.portrait).race;
  const options = classOptions(raceId);
  let preview = m.cls;
  const draw = () => {
    const list = options.map(id => {
      const c = R().combos[`${raceId}:${id}`];
      const gm = R().skills.filter((s, i) => c.best[i] === 'G' && s !== 'Blaster').map(skillName);
      return `<button class="cp-card${id === m.cls ? ' current' : ''}" data-c="${id}" aria-pressed="${id === preview}">
        <img src="${classIcon(id)}" alt=""><span><span class="cn">${esc(className(id))}</span><br>
        <span class="cg">GM: ${esc(gm.slice(0, 5).join(', ') || '—')}${gm.length > 5 ? ` +${gm.length - 5}` : ''}</span></span></button>`;
    }).join('');
    const desc = (cls(preview).desc || '').split('. ').slice(0, 2).join('. ');
    dlg.querySelector('.cp-list').innerHTML = list;
    dlg.querySelector('.cp-detail').innerHTML = `<div style="display:flex;align-items:center;gap:12px"><img src="${classIcon(preview)}" width="54" height="54"><span class="h2" style="font-size:30px">${esc(className(preview))}</span>
      <button class="btn primary small" data-pick style="margin-left:auto">${preview === m.cls ? 'Keep' : 'Choose'} ${esc(className(preview))}</button></div>
      <div style="font:15px/1.35 var(--small);color:#cfc7b1;margin:6px 0 8px">${esc(desc)}${desc.endsWith('.') ? '' : '.'}</div>
      ${masteryTableHtml(m, preview)}`;
    dlg.querySelectorAll('.cp-card').forEach(b => {
      b.onclick = () => { preview = Number(b.dataset.c); draw(); };
      b.ondblclick = () => { setClass(m, Number(b.dataset.c)); closeModal(); };
    });
    dlg.querySelector('[data-pick]').onclick = () => { setClass(m, preview); closeModal(); };
  };
  const dlg = openModal(`<div class="dlg-head"><span class="h2">Choose Class</span><span class="caption">${esc(R().races[raceId].name)} · ${options.length} classes · mastery table shows this race</span>
     <button class="btn small quiet x" data-close>Close</button></div>
     <div class="cp"><div class="cp-list"></div><div class="cp-detail body"></div></div>`, [70, 40, 1460, 820]);
  draw();
}

function openMasteryTable(mi) {
  const m = App.members[mi];
  openModal(`<div class="dlg-head"><span class="h2">${esc(m.name)} — mastery table</span><span class="caption">${esc(race(m).name)} ${esc(className(m.cls))} and promotions</span>
    <button class="btn small quiet x" data-close>Close</button></div><div class="body">${masteryTableHtml(m, m.cls)}</div>`, [300, 40, 1000, 820]);
}

// Voice picker: every voice of the portrait's kind, labelled by number (= the portrait whose own voice it is),
// owners shown as thumbnails, with several playable lines per voice.
const SAMPLER = ['ChooseMe1', 'Hello1', 'Hello2', 'Yes1', 'Thanks1', 'Win!1', 'BigMonster1', 'Heh1', 'GoodItem1', 'Hungry1', 'Indignant'];
function lineLabel(cat) {
  return cat.replace(/!/, '').replace(/\d+$/, n => ` ${n}`).replace(/([a-z])([A-Z])/g, '$1 $2')
    .replace('Choose Me', 'Choose me').replace('Win', 'Victory').replace(/ 1$/, '').trim();
}
function openVoicePicker(mi) {
  const m = App.members[mi];
  let all = false, expanded = m.voice;
  const own = portraitById(m.portrait).voice;
  const draw = () => {
    const voices = voicesFor(m, all);
    dlg.querySelector('.vp-list').innerHTML = voices.map(v => {
      const owners = voiceOwners(v.id);
      const lines = v.id === expanded ? v.lines : SAMPLER.map(c => v.lines.find(l => l[0] === c)).filter(Boolean).slice(0, 7);
      return `<div class="vp-card" aria-pressed="${v.id === m.voice}" data-v="${v.id}">
        <div style="flex:1;min-width:0"><div><span class="vn">${voiceLabel(v.id)}</span>${v.id === own ? '<span class="tag">this portrait\'s own voice</span>' : ''}
        <span class="vk">&nbsp; ${esc(v.kind || 'Unsorted')}${v.note ? ' · ' + esc(v.note) : ''} · ${v.lines.length} lines</span></div>
        <div class="owners">${owners.map(p => `<span class="portrait" title="Portrait #${p.id}">${portraitImg(p)}</span>`).join('')}${owners.length ? `<span class="vk" style="align-self:center;margin-left:4px">default of ${owners.map(p => '#' + p.id).join(', ')}</span>` : '<span class="vk">no starting portrait uses it</span>'}</div>
        <div class="lines">${lines.map(l => `<button class="line" data-line="${esc(l[1])}">${esc(lineLabel(l[0]))}</button>`).join('')}
        ${v.id !== expanded ? `<button class="line" data-more="${v.id}" style="border-style:dashed">all ${v.lines.length}…</button>` : ''}</div></div>
        <button class="btn small${v.id === m.voice ? '' : ' quiet'}" data-use="${v.id}" style="flex:none">${v.id === m.voice ? 'Selected' : 'Use'}</button></div>`;
    }).join('');
    dlg.querySelectorAll('[data-line]').forEach(b => b.onclick = () => playFile(b.dataset.line, b));
    dlg.querySelectorAll('[data-more]').forEach(b => b.onclick = () => { expanded = Number(b.dataset.more); draw(); });
    dlg.querySelectorAll('[data-use]').forEach(b => b.onclick = () => { m.voice = Number(b.dataset.use); playVoiceLine(m.voice, 'ChooseMe'); draw(); });
    dlg.querySelector('[data-all]').setAttribute('aria-pressed', all);
  };
  const dlg = openModal(`<div class="dlg-head"><span class="h2">Choose Voice</span><span class="caption">Voice N is portrait #N's own voice · ▶ plays the real game line</span>
      <button class="btn tiny quiet" data-all>All voices</button><button class="btn small quiet x" data-close>Done</button></div>
      <div class="body"><div class="vp-list"></div></div>`, [70, 40, 1460, 820]);
  dlg.querySelector('[data-all]').onclick = () => { all = !all; draw(); };
  draw();
}

// ---------------------------------------------------------------- audio: IMA ADPCM WAV decoder (game voices)
let audioCtx = null, audioSource = null;
const IMA_INDEX = [-1, -1, -1, -1, 2, 4, 6, 8, -1, -1, -1, -1, 2, 4, 6, 8];
const IMA_STEP = [7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 19, 21, 23, 25, 28, 31, 34, 37, 41, 45, 50, 55, 60, 66, 73, 80, 88, 97,
  107, 118, 130, 143, 157, 173, 190, 209, 230, 253, 279, 307, 337, 371, 408, 449, 494, 544, 598, 658, 724, 796, 876, 963,
  1060, 1166, 1282, 1411, 1552, 1707, 1878, 2066, 2272, 2499, 2749, 3024, 3327, 3660, 4026, 4428, 4871, 5358, 5894, 6484,
  7132, 7845, 8630, 9493, 10442, 11487, 12635, 13899, 15289, 16818, 18500, 20350, 22385, 24623, 27086, 29794, 32767];
function decodeWav(buffer) {
  const v = new DataView(buffer);
  let pos = 12, fmt = null, data = null;
  while (pos + 8 <= v.byteLength) {
    const id = String.fromCharCode(v.getUint8(pos), v.getUint8(pos + 1), v.getUint8(pos + 2), v.getUint8(pos + 3));
    const size = v.getUint32(pos + 4, true);
    if (id === 'fmt ') fmt = {format: v.getUint16(pos + 8, true), channels: v.getUint16(pos + 10, true), rate: v.getUint32(pos + 12, true),
      align: v.getUint16(pos + 20, true), bits: v.getUint16(pos + 22, true)};
    if (id === 'data') data = {offset: pos + 8, size: Math.min(size, v.byteLength - pos - 8)};
    pos += 8 + size + (size & 1);
  }
  if (!fmt || !data || fmt.channels !== 1) throw new Error('unsupported wav');
  const out = [];
  if (fmt.format === 1 && fmt.bits === 16) {
    for (let i = 0; i + 1 < data.size; i += 2) out.push(v.getInt16(data.offset + i, true) / 32768);
  } else if (fmt.format === 0x11) {
    for (let block = data.offset; block + 4 <= data.offset + data.size; block += fmt.align) {
      let pred = v.getInt16(block, true), index = Math.min(88, v.getUint8(block + 2));
      out.push(pred / 32768);
      const end = Math.min(block + fmt.align, data.offset + data.size);
      for (let p = block + 4; p < end; p++) {
        const byte = v.getUint8(p);
        for (const nib of [byte & 15, byte >> 4]) {
          const step = IMA_STEP[index];
          let diff = step >> 3;
          if (nib & 4) diff += step;
          if (nib & 2) diff += step >> 1;
          if (nib & 1) diff += step >> 2;
          pred = Math.max(-32768, Math.min(32767, pred + (nib & 8 ? -diff : diff)));
          index = Math.max(0, Math.min(88, index + IMA_INDEX[nib]));
          out.push(pred / 32768);
        }
      }
    }
  } else throw new Error('unsupported wav format ' + fmt.format);
  return {rate: fmt.rate, samples: Float32Array.from(out)};
}
async function playFile(file, button) {
  document.querySelectorAll('.line.playing').forEach(b => b.classList.remove('playing'));
  if (button) button.classList.add('playing');
  try {
    audioCtx ||= new (window.AudioContext || window.webkitAudioContext)();
    const response = await fetch(AUDIO + file);
    const wav = decodeWav(await response.arrayBuffer());
    const buffer = audioCtx.createBuffer(1, wav.samples.length, wav.rate);
    buffer.copyToChannel(wav.samples, 0);
    if (audioSource) try { audioSource.stop(); } catch (e) { /* already stopped */ }
    audioSource = audioCtx.createBufferSource();
    audioSource.buffer = buffer;
    audioSource.connect(audioCtx.destination);
    audioSource.onended = () => button && button.classList.remove('playing');
    audioSource.start();
  } catch (e) {
    toast(`▶ ${file} (playback unavailable here)`);
    if (button) setTimeout(() => button.classList.remove('playing'), 900);
  }
}
function playVoiceLine(voiceId, prefix, button) {
  const v = voicesById()[voiceId];
  if (!v) return;
  const options = v.lines.filter(l => l[0].startsWith(prefix));
  if (!options.length) return;
  const line = options[Math.floor(Math.random() * options.length)];
  playFile(line[1], button);
}
function voiceButtons(m, which = ['ChooseMe', 'Hello', 'Yes', 'Win']) {
  const v = voicesById()[m.voice];
  return which.filter(w => v && v.lines.some(l => l[0].startsWith(w)))
    .map(w => `<button class="line" data-vl="${w}">${esc(lineLabel(w + '1'))}</button>`).join('');
}
function wireVoiceButtons(root) {
  root.querySelectorAll('[data-vl]').forEach(b => b.onclick = e => {
    e.stopPropagation();
    const mi = Number(b.closest('[data-member]')?.dataset.member ?? App.sel);
    playVoiceLine(App.members[mi].voice, b.dataset.vl, b);
  });
}

// ---------------------------------------------------------------- stage, device simulation, review bar
const DEVICES = {
  desktop: {label: '16:9 desktop', aspect: 16 / 9},
  window43: {label: '4:3 window (letterboxed canvas)', aspect: 4 / 3},
  phone: {label: '6.5″ 20:9 phone · touch · fingertip = 9 mm', aspect: 20 / 9},
};
// A 6.5-inch 20:9 phone is 67.7 mm tall; the 480-unit canvas fills that height.
const PHONE_MM_PER_UNIT = 67.7 / 480;
function layoutStage() {
  const vp = el('#viewport').getBoundingClientRect();
  const dev = DEVICES[App.device];
  const margin = App.export ? 0 : 40;
  let w = vp.width - margin, h = vp.height - margin;
  if (w / h > dev.aspect) w = h * dev.aspect; else h = w / dev.aspect;
  const device = el('#device');
  device.className = App.device;
  device.style.width = `${w}px`;
  device.style.height = `${h}px`;
  const scale = Math.min(w / 1600, h / 900);
  const stage = el('#stage');
  stage.style.transform = `scale(${scale})`;
  stage.style.left = `${(w - 1600 * scale) / 2}px`;
  stage.style.top = `${(h - 900 * scale) / 2}px`;
  const finger = el('#finger');
  const pxPerMm = (900 * scale) / 67.7;
  finger.style.width = finger.style.height = `${9 * pxPerMm}px`;
  el('.device-label').textContent = dev.label + (App.device === 'window43' ? ' · canvas at 75 % of 16:9 size' : '');
  document.body.classList.toggle('touch', touch());
  document.body.classList.toggle('mouse', !touch());
}
function smallTargetAudit(mark) {
  // Interactive targets measured in canvas logical units (1600 px = 853.3 units) and phone millimetres.
  const nodes = [...el('#screen').querySelectorAll('button, input, [data-skill], [data-hit]')].filter(n => n.offsetParent !== null);
  const stage = el('#stage').getBoundingClientRect();
  const scale = stage.width / 1600;
  const res = nodes.map(n => {
    const r = n.getBoundingClientRect();
    const hUnits = r.height / scale * 8 / 15, wUnits = r.width / scale * 8 / 15;
    return {n, mm: Math.min(hUnits, wUnits) * PHONE_MM_PER_UNIT, hmm: hUnits * PHONE_MM_PER_UNIT};
  });
  document.querySelectorAll('.small-target').forEach(n => n.classList.remove('small-target'));
  if (mark) res.filter(r => r.hmm < 5).forEach(r => r.n.classList.add('small-target'));
  const n = res.length || 1;
  return {targets: res.length, atLeast7: Math.round(100 * res.filter(r => r.mm >= 7).length / n),
    atLeast5: Math.round(100 * res.filter(r => r.hmm >= 5).length / n),
    medianHeightMm: +(res.map(r => r.hmm).sort((a, b) => a - b)[Math.floor(res.length / 2)] || 0).toFixed(1)};
}
window.smallTargetAudit = smallTargetAudit;

function reviewBar() {
  const links = [['a', 'A · Five columns'], ['b', 'B · Skill board'], ['c', 'C · Focus + rail'], ['c2', 'C2 · Revised']];
  const q = k => {
    const p = new URLSearchParams({ruleset: App.ruleset, continent: App.continent, device: App.device, party: App.party});
    return `${k}.html?${p}`;
  };
  return `<a class="home" href="index.html">Party creation study</a>
    <span class="seg">${links.map(([k, t]) => `<button aria-pressed="${App.approach === k}" data-go="${q(k)}">${t}</button>`).join('')}</span>
    <label>Rules</label><span class="seg"><button data-set="ruleset" data-v="standard">Standard</button><button data-set="ruleset" data-v="maw">MAW</button></span>
    <label>Continent</label><span class="seg">${D.standard.continents.map(c => `<button data-set="continent" data-v="${c.key}">${esc(c.name)}</button>`).join('')}</span>
    <label>View</label><span class="seg"><button data-set="device" data-v="desktop">16:9</button><button data-set="device" data-v="window43">4:3</button><button data-set="device" data-v="phone">Phone</button></span>
    <label>Party</label><span class="seg"><button data-set="party" data-v="sample">Sample five</button><button data-set="party" data-v="fresh">Fresh start</button></span>
    <button class="seg" data-audit style="padding:5px 10px;color:#c9c2ab">Mark &lt;5 mm targets</button>
    <span class="spacer"></span><span class="hint">${touch() ? 'Touch: tap = inspect, then act' : 'Mouse: click = choose · hover / RMB = details'}</span>`;
}
function wireReviewBar() {
  const bar = el('.review');
  bar.innerHTML = reviewBar();
  bar.querySelectorAll('[data-set]').forEach(b => {
    b.setAttribute('aria-pressed', App[b.dataset.set] === b.dataset.v);
    b.onclick = () => {
      App[b.dataset.set] = b.dataset.v;
      const url = new URL(location.href);
      url.searchParams.set(b.dataset.set, b.dataset.v);
      history.replaceState(null, '', url);
      if (b.dataset.set !== 'device') buildParty();
      App.focus = null;
      hideCard();
      closeModalSilently();
      wireReviewBar();
      layoutStage();
      App.render();
    };
  });
  bar.querySelectorAll('[data-go]').forEach(b => b.onclick = () => { location.href = b.dataset.go; });
  let marked = false;
  bar.querySelector('[data-audit]').onclick = () => { marked = !marked; const r = smallTargetAudit(marked); toast(`${r.targets} targets · ${r.atLeast5}% ≥ 5 mm tall on a phone · ${r.atLeast7}% ≥ 7 mm both ways`); };
}
function closeModalSilently() { el('#modal').classList.remove('on'); el('#modal').innerHTML = ''; }

function boot(approach, render) {
  App.approach = approach;
  App.render = () => { render(); wireVoiceButtons(el('#screen')); };
  document.body.innerHTML = `<div class="review"></div><div id="viewport"><div id="device"><div id="stage">
      <div class="backdrop"></div><div class="panel"></div><div id="screen"></div><div id="card"></div><div id="modal"></div><div id="toast"></div>
    </div><div id="finger"></div><span class="device-label"></span></div></div>`;
  document.body.classList.toggle('export', App.export);
  buildParty();
  wireReviewBar();
  layoutStage();
  window.addEventListener('resize', layoutStage);
  el('#device').addEventListener('mousemove', e => {
    const r = el('#device').getBoundingClientRect();
    el('#finger').style.left = `${e.clientX - r.left}px`;
    el('#finger').style.top = `${e.clientY - r.top}px`;
  });
  el('#stage').addEventListener('click', e => {
    if (!e.target.closest('#card') && !e.target.closest('[data-skill]')) { hideCard(); if (App.focus) { App.focus = null; App.render(); } }
  });
  document.addEventListener('keydown', e => { if (e.key === 'Escape') { hideCard(); closeModalSilently(); App.render(); } });
  App.render();
  document.fonts.ready.then(() => { document.body.dataset.ready = 'true'; });
}

// Shared header and footer markup.
function headHtml(extra = '') {
  const ready = App.members.filter(ready_).length;
  return `<div class="head"><h1>Create Your Party</h1><span class="sub">${esc(continent().name)} · ${App.ruleset === 'maw' ? 'MAW rules' : 'Standard rules'}</span>
    <span class="grow"></span>${extra}<span class="sub">${App.members.length} / 5 adventurers · ${ready} ready</span></div>`;
}
function ready_(m) { return ready(m); }
function footHtml() {
  const st = partyStatus();
  return `<div class="foot"><button class="btn" data-hit>Cancel</button><span class="status">${st.text}</span>
    <button class="btn primary" ${st.ok ? '' : 'disabled'} data-begin>Begin Adventure</button></div>`;
}
function planToggleHtml() {
  return `<button class="btn tiny${App.planMode ? '' : ' quiet'}" data-plan aria-pressed="${App.planMode}" title="Clicks mark skills to learn later instead of choosing them">⚑ Plan mode</button>`;
}
function wireCommon(root) {
  root.querySelectorAll('[data-plan]').forEach(b => b.onclick = e => { e.stopPropagation(); App.planMode = !App.planMode; App.render(); });
  root.querySelectorAll('[data-begin]').forEach(b => b.onclick = () => toast('The party sets out…'));
  root.querySelectorAll('[data-portrait]').forEach(b => b.onclick = e => { e.stopPropagation(); App.sel = Number(b.dataset.portrait); openPortraitPicker(App.sel); });
  root.querySelectorAll('[data-class]').forEach(b => b.onclick = e => { e.stopPropagation(); App.sel = Number(b.dataset.class); openClassPicker(App.sel); });
  root.querySelectorAll('[data-voice]').forEach(b => b.onclick = e => { e.stopPropagation(); App.sel = Number(b.dataset.voice); openVoicePicker(App.sel); });
  root.querySelectorAll('[data-table]').forEach(b => b.onclick = e => { e.stopPropagation(); openMasteryTable(Number(b.dataset.table)); });
  root.querySelectorAll('[data-add]').forEach(b => b.onclick = e => { e.stopPropagation(); addMember(); });
  root.querySelectorAll('[data-remove]').forEach(b => b.onclick = e => { e.stopPropagation(); removeMember(Number(b.dataset.remove)); });
  root.querySelectorAll('[data-reset]').forEach(b => b.onclick = e => { e.stopPropagation(); resetMember(Number(b.dataset.reset)); });
  root.querySelectorAll('[data-inc]').forEach(b => b.onclick = e => {
    e.stopPropagation();
    const [mi, si] = b.dataset.inc.split(':').map(Number);
    App.sel = mi;
    if (!inc(App.members[mi], si)) toast(pool(App.members[mi]) <= 0 ? 'No bonus points left' : `${D.statNames[si]} is at its racial maximum`);
    App.render();
  });
  root.querySelectorAll('[data-dec]').forEach(b => b.onclick = e => {
    e.stopPropagation();
    const [mi, si] = b.dataset.dec.split(':').map(Number);
    App.sel = mi;
    if (!dec(App.members[mi], si)) toast(`${D.statNames[si]} cannot drop further`);
    App.render();
  });
  root.querySelectorAll('[data-name]').forEach(input => {
    input.oninput = () => { App.members[Number(input.dataset.name)].name = input.value.slice(0, 15); };
    input.onchange = () => App.render();
    input.onclick = e => e.stopPropagation();
  });
  root.querySelectorAll('[data-select]').forEach(b => b.addEventListener('click', () => {
    const mi = Number(b.dataset.select);
    if (App.sel !== mi) { App.sel = mi; App.render(); }
  }));
  wireSkillEvents(root);
}
