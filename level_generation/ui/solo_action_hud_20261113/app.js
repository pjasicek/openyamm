'use strict';
// Solo action HUD study (2026-11-13). Every view draws into one 1600 x 900 stage; ?view=<id>&export=1 shows the
// stage alone for the preview captures. Values are simulated.

const A = (name) => `art/${name}.png`;
const CX = 800, CY = 450;

const HERO = { name: 'Zoltan', level: 47, hp: 412, hpMax: 520, sp: 96, spMax: 140 };
const hpFrac = HERO.hp / HERO.hpMax, spFrac = HERO.sp / HERO.spMax;
const hpBand = hpFrac >= 0.66 ? '' : hpFrac > 0.33 ? 'mid' : 'low';

const BUFFS = [
  { art: 'item_tower_shield', item: true, name: 'Shield Wall', t: '6s', spent: 0.25, talent: true },
  { art: 'buff_sbs02a', name: 'Bless', t: '4m', spent: 0.35 },
  { art: 'buff_sbs07a', name: 'Heroism', t: '2m', spent: 0.6 },
  { art: 'buff_sbf05a', name: 'Haste', t: '48s', spent: 0.7 },
  { art: 'buff_sbe05a', name: 'Stone Skin', t: '9m', spent: 0.2 },
  { art: 'buff_sbl08a', name: 'Day of Protection', t: '58m', spent: 0.05 },
  { art: 'buff_sbl09a', name: 'Hour of Power', t: '12s', spent: 0.93, expiring: true },
];
const DEBUFFS = [
  { art: 'spell_curepoison', name: 'Poisoned', t: '12s', spent: 0.55, cc: true },
  { art: 'debuff_slow', name: 'Slowed', t: '4s', spent: 0.8, cc: true },
];
const PROC_BUFF = { art: 'item_sword', rot: true, name: 'Blade Frenzy', t: '5s', spent: 0.4, talent: true };

// The main row. kind: talent | spell | item. States: cd (seconds), done (0..1 of the cooldown), active, proc, nomana,
// range, count.
const BAR = [
  { key: '1', art: 'item_kite_shield', item: true, name: 'Shield Bash' },
  { key: '2', art: 'item_boots', item: true, name: 'Charge', cd: 9, done: 0.4 },
  { key: '3', art: 'item_sword', rot: true, name: 'Whirlwind', proc: true },
  { key: '4', art: 'spell_firebolt', name: 'Fire Bolt', cost: 2 },
  { key: '5', art: 'spell_fireball', name: 'Fireball', cost: 8, range: true },
  { key: '6', art: 'spell_lightningbolt', name: 'Lightning Bolt', cost: 20, cd: 3, done: 0.7 },
  { key: '7', art: 'spell_heal', name: 'Heal', cost: 5 },
  { key: '8', art: 'item_tower_shield', item: true, name: 'Shield Wall', active: true },
  { key: '9', art: 'spell_stoneskin', name: 'Stone Hide', cd: 24, done: 0.2 },
  { key: '0', art: 'item_cure_wounds', item: true, name: 'Cure Wounds', count: 7 },
];
const BAR_SHIFT = [
  { key: '⇧1', art: 'spell_bless', name: 'Bless', cost: 5 },
  { key: '⇧2', art: 'spell_heroism', name: 'Heroism', cost: 30 },
  { key: '⇧3', art: 'spell_haste', name: 'Haste', cost: 15 },
  { key: '⇧4', art: 'spell_dayofthegods', name: 'Day of the Gods', cost: 70, nomana: true },
  { key: '⇧5', art: 'spell_regeneration', name: 'Regeneration', cost: 10 },
  { key: '⇧6', art: 'spell_curepoison', name: 'Cure Poison', cost: 5 },
  { key: '⇧7', art: 'buff_sbv02a', name: 'Spirit Tide', cd: 95, done: 0.15 },
  { key: '⇧8', art: 'buff_sba02a', name: 'Blink', count: 2, pips: [1, 1, 0] },
  { key: '⇧9', empty: true },
  { key: '⇧0', art: 'item_magic_potion', item: true, name: 'Magic Potion', count: 3 },
];

// ---------- small builders ----------
function iconInner(s)
{
  if (s.rot)
  {
    return `<i class="item"><u style="background-image:url(${A(s.art)})"></u></i>`;
  }
  return `<i class="${s.item ? 'item' : ''}" style="background-image:url(${A(s.art)})"></i>`;
}

function slot(s, extra = '')
{
  if (s.empty)
  {
    return `<div class="slot empty ${extra}"><i></i>${s.key ? `<b class="key${s.key.length > 1 ? ' mod' : ''}">${s.key}</b>` : ''}</div>`;
  }
  const cls = ['slot', extra];
  if (s.active) cls.push('active');
  if (s.proc) cls.push('proc');
  if (s.nomana) cls.push('nomana');
  if (s.range) cls.push('range');
  if (s.gcd) cls.push('gcd');
  if (s.drag) cls.push('drag');
  if (s.locked) cls.push('locked');
  let h = `<div class="${cls.join(' ')}">${iconInner(s)}`;
  if (s.cost !== undefined) h += `<span class="cost">${s.cost}</span>`;
  if (s.key) h += `<b class="key${s.key.length > 1 ? ' mod' : ''}">${s.key}</b>`;
  if (s.count !== undefined) h += `<span class="count">${s.count}</span>`;
  if (s.cd !== undefined) h += `<span class="cd" style="--done:${s.done}"><em>${s.cdText ?? s.cd}</em></span>`;
  if (s.gcd) h += `<span class="cd" style="--done:${s.gcdDone ?? 0.55}"></span>`;
  if (s.proc) h += '<span class="spark"></span>';
  if (s.pips) h += `<span class="pips">${s.pips.map((p) => `<b class="${p ? '' : 'off'}"></b>`).join('')}</span>`;
  if (s.recharge !== undefined) h += `<span class="recharge"><b style="width:${s.recharge * 100}%"></b></span>`;
  return h + '</div>';
}

function tile(b, size = 30)
{
  const cls = ['tile'];
  if (b.cc) cls.push('cc');
  if (b.talent) cls.push('talent');
  if (b.expiring) cls.push('expiring');
  const bg = b.rot ? '' : `background-image:url(${A(b.art)});${b.item ? 'background-size:contain;' : ''}`;
  const inner = b.rot ? `<u style="background-image:url(${A(b.art)})"></u>` : '';
  return `<div class="${cls.join(' ')}" style="width:${size}px;height:${size}px;${bg}" title="${b.name}">${inner}`
    + `<span class="sweep" style="--spent:${b.spent ?? 0}"></span>${b.t ? `<span class="t">${b.t}</span>` : ''}</div>`;
}

function tiles(list, x, y, opt = {})
{
  const style = opt.right ? `right:${1600 - x}px;flex-direction:row-reverse` : `left:${x}px`;
  return `<div class="tiles" style="${style};top:${y}px;gap:${opt.gap ?? 6}px">${list.map((b) => tile(b, opt.size)).join('')}</div>`;
}

function rbar(kind, x, y, w, h, frac, text, extra = '')
{
  const band = kind === 'hp' ? hpBand : '';
  return `<div class="rbar ${kind} ${band} ${extra}" style="left:${x}px;top:${y}px;width:${w}px;height:${h}px">`
    + `<b style="width:calc(${frac * 100}% - 2px)"></b>${text ? `<span style="font-size:${h >= 18 ? 15 : 13}px">${text}</span>` : ''}</div>`;
}

const topbar = () => `<img class="abs" src="${A('native_topbar')}" style="left:0;top:0" alt="">`;
const minimap = () => `<img class="abs" src="${A('native_minimap')}" style="left:1336px;top:4px" alt="">`;
const heroPanels = () => `<img class="abs" src="${A('native_herobuffs')}" style="left:6px;top:60px" alt="">`;

function crosshair(recovery = 0.62)
{
  // Ivory outline cross (the installed design D) plus the proposed recovery brackets: they fill as the swing or cast
  // recovers and stay faint when ready.
  const r = 30, a0 = 140, a1 = 220;
  const pt = (deg) => [45 + r * Math.cos(deg * Math.PI / 180), 45 + r * Math.sin(deg * Math.PI / 180)];
  const arc = (from, to) => { const p = pt(from), q = pt(to); return `M${p[0].toFixed(2)} ${p[1].toFixed(2)} A${r} ${r} 0 0 1 ${q[0].toFixed(2)} ${q[1].toFixed(2)}`; };
  const leftEnd = a1 - (a1 - a0) * recovery;       // left bracket fills upward from the bottom
  const rightEnd = -40 + 80 * recovery;            // right bracket fills from the top down
  const cross = [[45, 31, 45, 39], [45, 51, 45, 59], [31, 45, 39, 45], [51, 45, 59, 45]];
  return `<svg class="xhair" style="left:${CX}px;top:${CY}px" viewBox="0 0 90 90">
    <g fill="none" stroke-linecap="round">
      <path d="${arc(a0, a1)}" stroke="#000" stroke-opacity=".55" stroke-width="5"/>
      <path d="${arc(-40, 40)}" stroke="#000" stroke-opacity=".55" stroke-width="5"/>
      <path d="${arc(a0, a1)}" stroke="#eadfc6" stroke-opacity=".28" stroke-width="2.4"/>
      <path d="${arc(-40, 40)}" stroke="#eadfc6" stroke-opacity=".28" stroke-width="2.4"/>
      ${recovery > 0 ? `<path d="${arc(leftEnd, a1)}" stroke="#fffae0" stroke-width="2.6"/>
      <path d="${arc(-40, rightEnd)}" stroke="#fffae0" stroke-width="2.6"/>` : ''}
      ${cross.map(([x1, y1, x2, y2]) => `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="#202020" stroke-width="4" stroke-linecap="square"/>`).join('')}
      ${cross.map(([x1, y1, x2, y2]) => `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="#fffae0" stroke-width="2" stroke-linecap="square"/>`).join('')}
    </g></svg>`;
}

function target()
{
  const cur = 23, max = 40, trailFrom = 31;
  return `<div class="ebar" style="left:846px;top:254px">
      <div class="lbl">Goblin Lord<span>${cur}/${max}</span></div>
      <div class="track"><div class="fillbox"><div class="trail" style="width:${trailFrom / max * 100}%"></div>
        <div class="fill" style="width:${cur / max * 100}%"></div></div></div>
      <div class="fx">${tile({ art: 'debuff_stun', name: 'Stunned', spent: 0.7, cc: true }, 26)}${tile({ art: 'debuff_slow', name: 'Slowed', spent: 0.35, cc: true }, 26)}</div>
    </div>
    <div class="float crit" style="left:940px;top:372px">31</div>
    <div class="float" style="left:676px;top:420px">12</div>
    <div class="float small" style="left:996px;top:430px">8</div>`;
}

const status = (y, html) => `<div class="status" style="left:${CX}px;top:${y}px">${html}</div>`;
const STATUS_TEXT = 'Zoltan hits the Goblin Lord for <b>31</b> (critical) · Goblin Lord is stunned';

function endcaps(left, right, top, h = 166, icons = true)
{
  const w = Math.round(h * 149 / 335);
  const isz = Math.round(Math.min(40, h * 0.24));
  const ic = (art) => (icons ? `<i style="background-image:url(${A(art)});width:${isz}px;height:${isz}px;margin:${-isz / 2}px 0 0 ${-isz / 2}px"></i>` : '');
  return `<div class="endcap" style="left:${left - w}px;top:${top}px;width:${w}px;height:${h}px">${ic('item_scroll')}</div>`
    + `<div class="endcap right" style="left:${right}px;top:${top}px;width:${w}px;height:${h}px">${ic('item_cure_wounds')}</div>`;
}

function slotsRow(list, x, y, gap = 6)
{
  return `<div class="bar" style="left:${x}px;top:${y}px;gap:${gap}px">${list.map((s) => slot(s)).join('')}</div>`;
}

const SLOT = 52, GAP = 6, BAR_W = 10 * SLOT + 9 * GAP;  // 574

// Action bar in an Obsidian panel, flush with the screen bottom like the party basebar.
function actionBar(opt = {})
{
  const border = 16, pad = 7;
  const echo = opt.echo ? 16 : 0;
  const rows = opt.shiftRow ? 2 : 1;
  const w = BAR_W + 2 * (border + pad);
  const h = rows * SLOT + (rows - 1) * 8 + 2 * (border + pad) + echo;
  const x = CX - w / 2, y = 900 - h + 2;
  let s = `<div class="panel thin" style="left:${x}px;top:${y}px;width:${w}px;height:${h}px"></div>`;
  const sx = x + border + pad;
  let sy = y + border + pad;
  if (opt.echo)
  {
    s += rbar('hp', sx, sy - 1, BAR_W / 2 - 3, 7, hpFrac, '', 'slim');
    s += rbar('mp', sx + BAR_W / 2 + 3, sy - 1, BAR_W / 2 - 3, 7, spFrac, '', 'slim');
    sy += echo;
  }
  if (opt.shiftRow)
  {
    s += slotsRow(BAR_SHIFT, sx, sy);
    sy += SLOT + 8;
  }
  s += slotsRow(BAR, sx, sy);
  if (opt.sockets !== false)
  {
    s += endcaps(x + 14, x + w - 14, 900 - 166);
  }
  return { html: s, x, y, w, h };
}

// ---------- placeholder view model (neutral, drawn here; not game art) ----------
function viewModel()
{
  return `<svg class="vm" viewBox="0 0 1600 900" preserveAspectRatio="none">
  <defs>
    <linearGradient id="blade" x1="0" x2="1"><stop offset="0" stop-color="#7d858b"/><stop offset=".42" stop-color="#d9dee1"/>
      <stop offset=".5" stop-color="#9aa2a8"/><stop offset=".58" stop-color="#e6eaec"/><stop offset="1" stop-color="#6c7378"/></linearGradient>
    <linearGradient id="iron" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#5d6266"/><stop offset="1" stop-color="#25292c"/></linearGradient>
    <linearGradient id="glove" x1="0" x2="1" y1="0" y2="1"><stop offset="0" stop-color="#5a4a3a"/><stop offset="1" stop-color="#2a2019"/></linearGradient>
    <radialGradient id="wood" cx=".55" cy=".2" r="1"><stop offset="0" stop-color="#7a5a3a"/><stop offset=".6" stop-color="#4b3420"/><stop offset="1" stop-color="#2a1c10"/></radialGradient>
  </defs>
  <g transform="translate(150 1000) rotate(-8)">
    <circle r="318" fill="#141414" opacity=".5" transform="translate(10 10)"/>
    <circle r="310" fill="url(#wood)"/>
    ${[-200, -120, -40, 40, 120, 200].map((x) => `<line x1="${x}" y1="-300" x2="${x}" y2="300" stroke="#1e140b" stroke-opacity=".55" stroke-width="3"/>`).join('')}
    <circle r="310" fill="none" stroke="#3b3f42" stroke-width="22"/>
    <circle r="310" fill="none" stroke="#8a8f92" stroke-width="3" stroke-opacity=".6"/>
    ${[...Array(14).keys()].map((i) => { const a = -1.9 + i * 0.13; return `<circle cx="${(296 * Math.cos(a)).toFixed(1)}" cy="${(296 * Math.sin(a)).toFixed(1)}" r="5" fill="#9b9fa2"/>`; }).join('')}
    <circle r="70" fill="url(#iron)" stroke="#1a1c1e" stroke-width="4"/>
  </g>
  <g transform="translate(1238 842) rotate(-31)">
    <path d="M-12 -62 L12 -62 L10 -405 L0 -438 L-10 -405 Z" fill="url(#blade)" stroke="#2b2f33" stroke-width="2"/>
    <path d="M0 -70 L0 -395" stroke="#5e666c" stroke-width="3"/>
    <rect x="-62" y="-74" width="124" height="15" rx="6" fill="url(#iron)" stroke="#16181a" stroke-width="2"/>
    <circle cx="-62" cy="-66" r="9" fill="#9a8150"/><circle cx="62" cy="-66" r="9" fill="#9a8150"/>
    <rect x="-10" y="-60" width="20" height="78" fill="#3a2718"/>
    <circle cx="0" cy="26" r="13" fill="#9a8150" stroke="#2b2215" stroke-width="2"/>
    <path d="M-40 4 L40 4 L60 320 L-60 320 Z" fill="url(#glove)" stroke="#120d09" stroke-width="3"/>
    <path d="M-44 40 L44 40 M-48 90 L48 90" stroke="#7a6550" stroke-width="4"/>
    <ellipse cx="0" cy="-16" rx="40" ry="31" fill="#4a3b2d" stroke="#120d09" stroke-width="3"/>
    <path d="M-36 -30 Q0 -38 36 -30 M-39 -16 Q0 -24 39 -16 M-36 -2 Q0 -10 36 -2" stroke="#2a2019" stroke-width="3" fill="none"/>
  </g></svg>`;
}

// ---------- unit frames ----------
function unitFrameWow(x, y)
{
  return `<div class="uf">
    <div class="face" style="left:${x + 8}px;top:${y + 4}px;width:92px;height:92px"></div>
    <div class="lvl" style="left:${x}px;top:${y + 66}px">${HERO.level}</div>
    <div class="name" style="left:${x + 112}px;top:${y + 8}px;width:270px">${HERO.name}<small>Battle Mage</small></div>
    ${rbar('hp', x + 112, y + 37, 270, 20, hpFrac, `${HERO.hp} / ${HERO.hpMax}`)}
    ${rbar('mp', x + 112, y + 61, 270, 17, spFrac, `${HERO.sp} / ${HERO.spMax}`)}
  </div>`;
}

function unitFrameOval(x, y)
{
  // The approved oval portrait and rim, a level diamond in place of the party's selection diamond.
  return `<div class="uf">
    <div class="face oval" style="left:${x + 9}px;top:${y + 8}px;width:70px;height:94px"></div>
    <div class="rim" style="left:${x + 4}px;top:${y + 3}px;width:80px;height:104px"></div>
    <div class="lvl diamond" style="left:${x + 66}px;top:${y + 78}px"><span>${HERO.level}</span></div>
    <div class="name" style="left:${x + 104}px;top:${y + 12}px;width:250px">${HERO.name}<small>Battle Mage</small></div>
    ${rbar('hp', x + 104, y + 41, 250, 20, hpFrac, `${HERO.hp} / ${HERO.hpMax}`)}
    ${rbar('mp', x + 104, y + 65, 250, 17, spFrac, `${HERO.sp} / ${HERO.spMax}`)}
  </div>`;
}

function arcPortrait(cx, cy, scale = 1, labels = true)
{
  // Split arcs from obsidian_curved_portraits_20260929/design.yml, scaled: HP from 100 deg sweeping +160, mana from
  // 80 deg sweeping -160 (fill from the bottom).
  const rx = 66 * scale, ry = 84 * scale, sw = 9 * scale;
  const pt = (deg) => [rx * Math.cos(deg * Math.PI / 180), ry * Math.sin(deg * Math.PI / 180)];
  const path = (from, sweep) =>
  {
    const p = pt(from), q = pt(from + sweep);
    return `M${p[0].toFixed(1)} ${p[1].toFixed(1)} A${rx} ${ry} 0 0 ${sweep > 0 ? 1 : 0} ${q[0].toFixed(1)} ${q[1].toFixed(1)}`;
  };
  const hpCol = hpBand === '' ? '#79b866' : hpBand === 'mid' ? '#d6ad4c' : '#cf5a4a';
  const fw = 104 * scale, fh = 140 * scale;
  return `<div class="arcport">
    <svg class="abs" style="left:${cx - rx - 12}px;top:${cy - ry - 12}px" width="${2 * rx + 24}" height="${2 * ry + 24}"
      viewBox="${-rx - 12} ${-ry - 12} ${2 * rx + 24} ${2 * ry + 24}">
      <path d="${path(100, 160)}" fill="none" stroke="#0b0f10" stroke-width="${sw + 3}"/>
      <path d="${path(80, -160)}" fill="none" stroke="#0b0f10" stroke-width="${sw + 3}"/>
      <path d="${path(100, 160 * hpFrac)}" fill="none" stroke="${hpCol}" stroke-width="${sw}"/>
      <path d="${path(80, -160 * spFrac)}" fill="none" stroke="#5e9fd8" stroke-width="${sw}"/>
    </svg>
    <div class="face" style="left:${cx - fw / 2}px;top:${cy - fh / 2}px;width:${fw}px;height:${fh}px"></div>
    <div class="rim" style="left:${cx - fw / 2 - 6 * scale}px;top:${cy - fh / 2 - 6 * scale}px;width:${fw + 12 * scale}px;height:${fh + 12 * scale}px"></div>
    <div class="uf"><div class="lvl diamond" style="left:${cx - 15}px;top:${cy - ry - 18}px"><span>${HERO.level}</span></div></div>
    <div class="gem" style="left:${cx - rx + 2}px;top:${cy + ry - 26}px"></div>
    <div class="medal" style="left:${cx + rx - 26}px;top:${cy + ry - 32}px"></div>
    ${labels ? `<div class="rlabel" style="left:${cx - rx - 44}px;top:${cy + ry - 22}px">${HERO.hp}</div>
    <div class="rlabel" style="left:${cx + rx + 14}px;top:${cy + ry - 22}px">${HERO.sp}</div>` : ''}
  </div>`;
}

function orb(kind, cx, cy, d, frac, cur, max)
{
  return `<div class="orb ${kind}" style="left:${cx - d / 2}px;top:${cy - d / 2}px;width:${d}px;height:${d}px">
    <div class="liquid" style="height:${frac * 100}%"></div><div class="glass"></div>
    <div class="val"><div>${cur}<small>/ ${max}</small></div></div></div>`;
}

// ---------- the HUD variants ----------
// In-game captures of the same scene with the private Oblivion arms (reference/oblivion_poc/preview/hud_scene, linked
// here as oblivion/, never committed): they replace the background and the drawn placeholder.
const ARMS = [
  ['placeholder', 'Drawn placeholder'],
  ['sword_shield_idle', 'Sword + shield'],
  ['sword_shield_swing', 'Swing'],
  ['sword_shield_block', 'Shield block'],
  ['claymore_idle', 'Claymore'],
  ['staff_cast', 'Cast'],
];

function common(opt = {})
{
  let s = opt.viewModel !== false && state.vm && state.arms === 'placeholder' ? viewModel() : '';
  s += crosshair(state.recovery);
  s += target();
  // The left-bar view can move the top bar under the minimap, freeing the top-left corner for the unit frame.
  if (state.view === 'a3' && state.topbar === 'right')
  {
    // The top bar in the top-right corner; the minimap below it without its clock (the art's rows 0-33), the clock
    // under the minimap or gone.
    const mx = 1336, my = 50;
    s += `<img class="abs" src="${A('native_topbar')}" style="left:${1600 - 559}px;top:0" alt="">`;
    s += `<div class="abs" style="left:${mx}px;top:${my}px;width:244px;height:230px;background:url(${A('native_minimap')}) 0 -34px no-repeat"></div>`;
    if (state.clock === 'rim')
    {
      // A small plate on the minimap's bottom rim between the zoom buttons, as WoW shows its clock.
      s += `<div class="clockplate" style="left:${mx + 122}px;top:${my + 206}px">9:05 am</div>`;
    }
    if (state.clock === 'below')
    {
      s += `<div class="abs" style="left:${mx}px;top:${my + 234}px;width:244px;height:34px;background:url(${A('native_minimap')}) 0 0 no-repeat"></div>`;
    }
    return s;
  }
  s += topbar() + minimap();
  return s;
}

const VIEWS = {};

VIEWS.a = {
  tab: 'A · Unit frame', title: 'A · WoW-like unit frame top-left, action bar bottom-centre',
  render()
  {
    let s = common();
    s += unitFrameWow(10, 58);
    s += tiles(BUFFS, 20, 166);
    s += tiles(DEBUFFS, 20, 218);
    const bar = actionBar();
    s += bar.html + status(bar.y - 44, STATUS_TEXT);
    return s;
  },
  notes: [
    ['What it is', ['Round portrait with a level badge, a name plate and green HP / blue SP bars with numbers, as in the WoW player frame.',
      'Buffs (timed, clockwise sweep, time below) and debuffs (red rim) hang under the frame; the talent effect Shield Wall has a gold rim.',
      'The ten-slot bar sits in the basebar\'s Obsidian panel, flush with the bottom; the potion and scroll sockets stay at its ends.',
      'The hero and skull panels are gone: with one character, party buffs and personal buffs are the same list.']],
    ['For', ['Everything about the character in one place, with exact numbers.', 'Smallest footprint at the bottom, where the weapon, the shield and the enemies\' feet are.',
      'Familiar to anyone who played WoW; the user likes this frame.'], 'pro'],
    ['Against', ['HP is in the corner, far from the crosshair: in a melee you must look away to check it.',
      'The round portrait crops the oval MM faces (the approved rim is oval).'], 'con'],
  ],
};

VIEWS.b = {
  tab: 'B · Minimal', title: 'B · Minimal (Skyrim / Avowed): no portrait, bars low beside the action bar',
  render()
  {
    let s = common();
    const y = 900 - SLOT - 16, x = CX - BAR_W / 2;
    s += `<div class="abs" style="left:${x - 40}px;top:${y - 24}px;width:${BAR_W + 80}px;height:${SLOT + 40}px;background:radial-gradient(ellipse at 50% 70%, #000a, transparent 70%)"></div>`;
    s += slotsRow(BAR, x, y);
    const by = y + 24;
    s += `<div class="tile" style="left:150px;top:${by - 12}px;position:absolute;width:34px;height:34px"><u style="background-image:url(${A('item_sword')})"></u></div>`;
    s += `<div class="uf"><div class="lvl" style="left:104px;top:${by - 12}px;width:34px;height:34px;font-size:16px">${HERO.level}</div></div>`;
    s += rbar('hp', 194, by, 300, 11, hpFrac, '');
    s += `<div class="rlabel plate" style="right:${1600 - 494}px;top:${by - 24}px">${HERO.hp} <small>/ ${HERO.hpMax}</small></div>`;
    s += rbar('mp', 1106, by, 300, 11, spFrac, '');
    s += `<div class="rlabel plate" style="left:1106px;top:${by - 24}px">${HERO.sp} <small>/ ${HERO.spMax}</small></div>`;
    s += tiles([...BUFFS].reverse(), 1406, by - 72, { right: true, size: 28, gap: 5 });
    s += tiles(DEBUFFS, 194, by - 74, { size: 28, gap: 5 });
    s += status(y - 46, STATUS_TEXT);
    return s;
  },
  notes: [
    ['What it is', ['No portrait, no name. HP (left) and SP (right) are slim bars at the height of the action bar, with the value above each.',
      'Weapon in hand and level sit at the start of the HP bar, like the first-person video reference.',
      'Debuffs over the HP bar, buffs over the SP bar, both small. Bars may fade out when full and out of combat (Skyrim).',
      'The bar has no panel and no sockets: the slots float on a soft shadow.']],
    ['For', ['Lowest screen cost; the scene and the weapon stay visible.', 'HP and SP are on the line the eye drops to from the crosshair.'], 'pro'],
    ['Against', ['No face: MM shows conditions (poisoned, asleep, afraid, insane) on the portrait; here only icons remain.',
      'Leaves the approved Obsidian chrome: it reads like a different game from the party mode.',
      'Bars this slim are hard to read over grass and bright stone.'], 'con'],
  ],
};

VIEWS.c = {
  tab: 'C · Arc portrait', title: 'C · Approved split-arc portrait, enlarged, with the action bar as wings',
  render()
  {
    let s = common();
    s += heroPanels();
    const pw = 226, ph = 214, px = CX - pw / 2, py = 900 - ph + 2;
    const wingW = 5 * SLOT + 4 * GAP + 2 * (16 + 7), wingH = SLOT + 2 * (16 + 7), wy = 900 - wingH + 2;
    const lx = px - wingW + 12, rx = px + pw - 12;
    s += `<div class="panel thin" style="left:${lx}px;top:${wy}px;width:${wingW}px;height:${wingH}px"></div>`;
    s += `<div class="panel thin" style="left:${rx}px;top:${wy}px;width:${wingW}px;height:${wingH}px"></div>`;
    s += slotsRow(BAR.slice(0, 5), lx + 23, wy + 23);
    s += slotsRow(BAR.slice(5), rx + 23, wy + 23);
    s += `<div class="panel" style="left:${px}px;top:${py}px;width:${pw}px;height:${ph}px"></div>`;
    s += arcPortrait(CX, py + ph / 2 + 6, 1);
    s += endcaps(lx + 14, rx + wingW - 14, 900 - 166);
    s += tiles(DEBUFFS, lx + 22, wy - 50);
    s += tiles(BUFFS.slice(0, 1).concat(BUFFS.slice(-1)), rx + wingW - 22, wy - 50, { right: true });
    s += status(py - 36, STATUS_TEXT);
    return s;
  },
  notes: [
    ['What it is', ['The approved curved portrait at about 1.3x: HP arc left (green/amber/red bands), SP arc right, aggro gem lower left, personal-buff medallion lower right.',
      'The selection diamond has no meaning with one character, so it becomes the level badge.',
      'Five slots on each wing, the potion and scroll sockets at the wing ends. Party buffs stay in the hero/skull panels as today.',
      'Proposed addition: the HP and SP values beside the arcs\' lower ends.']],
    ['For', ['Closest to what is installed and approved; party mode and solo mode look like one game.',
      'Face, conditions, HP and SP all in one spot just below the crosshair.'], 'pro'],
    ['Against', ['The tallest element on screen (214 px): it covers the enemies\' feet and the weapon\'s grip.',
      'Keys 1-5 and 6-0 are split by the portrait, so the bar is 260 px wider than in A.',
      'Buffs end up in three places (hero/skull panels, medallion, timed strip).'], 'con'],
  ],
};

VIEWS.d = {
  tab: 'D · Orbs', title: 'D · Diablo-like HP and SP orbs flanking the action bar',
  render()
  {
    let s = common();
    const bar = actionBar({ sockets: false });
    const d = 148, cy = 900 - d / 2 - 8;
    const lcx = bar.x - d / 2 + 18, rcx = bar.x + bar.w + d / 2 - 18;
    s += bar.html;
    s += orb('hp', lcx, cy, d, hpFrac, HERO.hp, HERO.hpMax);
    s += orb('mp', rcx, cy, d, spFrac, HERO.sp, HERO.spMax);
    s += `<div class="uf"><div class="lvl" style="left:${lcx - 17}px;top:${cy - d / 2 - 22}px">${HERO.level}</div></div>`;
    s += tiles(BUFFS, bar.x + 24, bar.y - 50, { size: 28, gap: 5 });
    s += tiles(DEBUFFS, bar.x + bar.w - 24, bar.y - 50, { right: true, size: 28 });
    s += status(bar.y - 92, STATUS_TEXT);
    return s;
  },
  notes: [
    ['What it is', ['Two glass orbs in brass rings, liquid level = HP (red) and SP (blue), the values inside.',
      'The level badge sits on the HP orb. Buffs left and debuffs right above the bar.',
      'The orbs take the sockets\' place; potions and scrolls go on the bar (slot 0, Shift+0).']],
    ['For', ['The strongest at-a-glance read of HP and SP; numbers are big.', 'Action-RPG players know it at once.'], 'pro'],
    ['Against', ['Red HP liquid contradicts the approved green/amber/red HP bands; green liquid reads as poison.',
      'Orbs are foreign to Might and Magic and to the Obsidian kit; new art would be needed.',
      'Two 148 px circles in the lower corners fight the shield and the sword for the same space.'], 'con'],
  ],
};

VIEWS.r = {
  tab: 'R · Recommended', title: 'R · Recommended: oval unit frame top-left, bar with HP/SP echo, recovery brackets',
  render()
  {
    let s = common();
    s += unitFrameOval(10, 56);
    s += tiles([PROC_BUFF, ...BUFFS], 20, 172);
    s += tiles(DEBUFFS, 20, 224);
    const bar = actionBar({ echo: true });
    s += bar.html + status(bar.y - 44, STATUS_TEXT);
    return s;
  },
  notes: [
    ['What it is', ['A, with the approved oval portrait and rim instead of a circle, and the level in the diamond where the party HUD has its selection diamond.',
      'A thin HP / SP echo on top of the action bar: no numbers, just enough to see "low" without looking away from the fight.',
      'Recovery brackets on the crosshair fill after each swing or cast (the MM recovery, now per action).',
      'Passive talents show only when they fire: Blade Frenzy proc lights Whirlwind (slot 3) and adds a gold-rimmed buff.']],
    ['Why', ['Keeps the face (identity and MM\'s conditions) without paying for it at the bottom of the screen.',
      'Uses only approved pieces: Obsidian panel, endcap sockets, oval rim, status plate, enemy bar.',
      'HP is readable in two places: exact in the frame, coarse next to the keys you are pressing.'], 'pro'],
    ['Open', ['Whether the echo should be there all the time or appear only below 50 % HP.',
      'Whether long buffs (Day of the Gods, Protection from Magic) stay in the one list or keep a compact hero/skull pair.'], 'con'],
  ],
};

VIEWS.today = {
  tab: 'Today', title: 'Today: the installed HUD with a one-member party, same place',
  render()
  {
    return '<div class="ref-tag">Native capture, 1600 × 900, one-member party, enemy bars in target mode</div>';
  },
  stageClass: 'today',
  notes: [
    ['Reference', ['The installed Obsidian HUD shrinks the basebar to one portrait; the hero and skull panels still hold the party buffs.',
      'There is no action bar: attacks are the mouse and the quick spells (Q, F5-F8 from Battle Orders).']],
  ],
};

// ---------- A refined (after the user's pick of A, 2026-11-13) ----------
// Map progress as MAW shows it today (GameplayMapProgressBar, option A of maw_map_progress_20261025): a violet channel
// in the frame's top stone band and a tab at its right corner with the normalised percent and slain / needed.
const MAW = { percent: 38.5, slain: 112, needed: 292, revivalShare: 0.65 };

function frameFull(x, y)
{
  // One Obsidian panel: the whole portrait at the party frame's size in its oval rim, the level on the rim's top
  // diamond (where the party frame has its selection diamond), name, HP and SP bars with numbers, buffs inside.
  const w = 430, h = 196, fx = x + 26, fy = y + 30, fw = 104, fh = 140;
  const rx = fx + fw + 22, rw = x + w - 22 - rx;
  return `<div class="panel thin" style="left:${x}px;top:${y}px;width:${w}px;height:${h}px"></div>
    <div class="uf">
      <div class="face full" style="left:${fx}px;top:${fy}px;width:${fw}px;height:${fh}px"></div>
      <div class="rim plain" style="left:${fx - 7}px;top:${fy - 7}px;width:${fw + 14}px;height:${fh + 14}px"></div>
      <div class="lvl diamond" style="left:${fx + fw / 2 - 15}px;top:${fy - 22}px"><span>${HERO.level}</span></div>
      <div class="name" style="left:${rx}px;top:${y + 24}px;width:${rw}px">${HERO.name}<small>Battle Mage</small></div>
      ${rbar('hp', rx, y + 56, rw, 22, hpFrac, `${HERO.hp} / ${HERO.hpMax}`)}
      ${rbar('mp', rx, y + 84, rw, 18, spFrac, `${HERO.sp} / ${HERO.spMax}`)}
    </div>
    ${tiles([PROC_BUFF, ...BUFFS].slice(0, 7), rx, y + 116, { size: 28, gap: 4 })}`;
}

function frameArcs(x, y)
{
  // The approved party portrait cell (split arcs, diamond, aggro gem, buff medallion) with a plate joined to its
  // right side for the name and the exact numbers; the cell and the plate share one border.
  const cw = 200, ch = 222, pw = 250, ph = 136, px = x + cw - 18, py = y + 30;
  return `<div class="panel thin" style="left:${px}px;top:${py}px;width:${pw}px;height:${ph}px"></div>
    <div class="panel thin" style="left:${x}px;top:${y}px;width:${cw}px;height:${ch}px"></div>
    ${arcPortrait(x + cw / 2, y + ch / 2 + 6, 1, false)}
    <div class="uf"><div class="name" style="left:${px + 30}px;top:${py + 22}px;width:${pw - 52}px">${HERO.name}<small>Battle Mage</small></div></div>
    <div class="numrow" style="left:${px + 30}px;top:${py + 50}px;width:${pw - 52}px">
      <span class="k">HP</span><span class="v hp ${hpBand}">${HERO.hp}<small> / ${HERO.hpMax}</small></span>
      <span class="k">SP</span><span class="v mp">${HERO.sp}<small> / ${HERO.spMax}</small></span></div>
    <div class="xpline" style="left:${px + 30}px;top:${py + 104}px;width:${pw - 52}px" title="Experience to level 48"><b style="width:64%"></b></div>`;
}

function frameWow(x, y)
{
  // WoW's player frame in the Obsidian kit: one framed box (the native frame pieces as a 9-slice) holding a name row
  // and the HP and SP bars with their numbers centred, the oval portrait medallion overlapping its left end, the level
  // on a brass coin at the medallion's foot, the weapon in hand on a small socket at its shoulder.
  const mw = 120, mh = 156;                 // medallion (rim) size
  const bx = x + mw - 26, by = y + 29, bw = 316, bh = 98;
  const mx = x, my = y;
  const ix = bx + 42, iw = bw - 42 - 12;   // inner rows, clear of the medallion's overlap
  return `<div class="ufw">
    <div class="box" style="left:${bx}px;top:${by}px;width:${bw}px;height:${bh}px"></div>
    <div class="row name" style="left:${ix}px;top:${by + 11}px;width:${iw}px">${HERO.name}<small>Battle Mage</small></div>
    <div class="row bar hp ${hpBand}" style="left:${ix}px;top:${by + 38}px;width:${iw}px;height:24px"><b style="width:${hpFrac * 100}%"></b><span>${HERO.hp} / ${HERO.hpMax}</span></div>
    <div class="row bar mp" style="left:${ix}px;top:${by + 64}px;width:${iw}px;height:20px"><b style="width:${spFrac * 100}%"></b><span>${HERO.sp} / ${HERO.spMax}</span></div>
    <div class="medal" style="left:${mx}px;top:${my}px;width:${mw}px;height:${mh}px">
      <div class="face" style="background-image:url(${A('face_pc03')})"></div>
      <div class="rim"></div>
    </div>
    <div class="coin" style="left:${mx - 4}px;top:${my + mh - 36}px">${HERO.level}</div>
    <div class="weapon" style="left:${mx + mw - 12}px;top:${by - 8}px"><u style="background-image:url(${A('item_sword')})"></u></div>
  </div>`;
}

const BAR_LAYOUTS = {
  rows5: { label: '2 × 5', rows: () => [BAR.slice(0, 5), BAR.slice(5)], border: 16, pad: 7 },
  slim: { label: 'One row, slim sides', rows: () => [BAR], border: 9, pad: 4 },
  rows10: { label: '2 × 10 (Shift row)', rows: () => [BAR_SHIFT, BAR], border: 16, pad: 7 },
};

function basebar(layoutId, opt)
{
  const L = BAR_LAYOUTS[layoutId];
  const rows = L.rows();
  const cols = rows[0].length;
  const inner = cols * SLOT + (cols - 1) * GAP;
  const echoH = opt.echo ? (L.border < 12 ? 12 : 16) : 0;
  const w = inner + 2 * (L.border + L.pad);
  const h = rows.length * SLOT + (rows.length - 1) * 8 + 2 * (L.border + L.pad) + echoH;
  const x = CX - w / 2, y = 900 - h + 2;
  let s = `<div class="panel thin" style="left:${x}px;top:${y}px;width:${w}px;height:${h}px;border-width:${L.border}px;border-image-width:${L.border}px"></div>`;
  const sx = x + L.border + L.pad;
  let sy = y + L.border + L.pad;
  if (opt.echo)
  {
    s += rbar('hp', sx, sy - 1, inner / 2 - 3, 7, hpFrac, '', 'slim');
    s += rbar('mp', sx + inner / 2 + 3, sy - 1, inner / 2 - 3, 7, spFrac, '', 'slim');
    sy += echoH;
  }
  rows.forEach((row) =>
  {
    s += slotsRow(row, sx, sy);
    sy += SLOT + 8;
  });
  const capH = Math.min(166, Math.max(104, h + 18));
  s += endcaps(x + Math.round(L.border * 0.8), x + w - Math.round(L.border * 0.8), 900 - capH, capH);
  let top = y;
  if (opt.maw)
  {
    // The channel sits in the top border band between the corners; the tab rises from the right corner.
    const band = Math.max(4, Math.round(L.border * 0.32));
    const cx0 = x + L.border + 4, cw = w - 2 * (L.border + 4);
    const raw = MAW.slain / (MAW.needed / 0.9801);
    s += `<div class="mawch" style="left:${cx0}px;top:${y + Math.round(L.border / 2 - band / 2)}px;width:${cw}px;height:${band}px">`
      + `<b style="width:${MAW.percent}%"></b><i style="left:${MAW.revivalShare / 0.9801 * 100}%"></i></div>`;
    s += `<div class="mawtab" style="right:${1600 - (x + w - L.border)}px;top:${y - 24}px">${MAW.percent} % · ${MAW.slain} / ${MAW.needed}</div>`;
    top = y - 24;
  }
  return { html: s, x, y, w, h, top };
}

VIEWS.a2 = {
  tab: 'A · Refined', title: 'A refined: whole portrait joined to its bars, basebar options, MAW map progress',
  render()
  {
    let s = common();
    if (state.frame === 'wow')
    {
      s += frameWow(14, 58);
      s += tiles([PROC_BUFF, ...BUFFS], 14 + 120 + 14, 58 + 26 + 98 + 10, { size: 26, gap: 9 });
      s += tiles(DEBUFFS, 14 + 120 + 14, 58 + 26 + 98 + 54, { size: 26, gap: 9 });
      const bar = basebar(state.bar, { echo: state.echo, maw: state.maw });
      return s + bar.html + status(bar.top - 40, STATUS_TEXT);
    }
    s += state.frame === 'arcs' ? frameArcs(6, 52) : frameFull(6, 52);
    const below = state.frame === 'arcs' ? 52 + 222 + 10 : 52 + 196 + 8;
    if (state.frame === 'arcs')
    {
      s += tiles([PROC_BUFF, ...BUFFS], 6 + 204, 52 + 30 + 136 + 8, { size: 28, gap: 4 });
      s += tiles(DEBUFFS, 6 + 204, 52 + 30 + 136 + 52, { size: 28, gap: 4 });
    }
    else
    {
      s += tiles(DEBUFFS, 18, below, { size: 28, gap: 4 });
    }
    const bar = basebar(state.bar, { echo: state.echo, maw: state.maw });
    s += bar.html + status(bar.top - 40, STATUS_TEXT);
    return s;
  },
  notes: [
    ['Top left: the unit frame (default)', ['WoW\'s player frame built from the game\'s own pieces: one box in the native Obsidian frame (the party frame\'s corners and stone band) holding the name row and the HP and SP bars with the numbers centred.',
      'The whole oval portrait sits in a stone-and-brass medallion overlapping the box\'s left end; the level on a brass coin at its foot, the weapon in hand on a small socket at its shoulder.',
      'Buffs (gold rim: special skills) and debuffs (red rim) in two rows under the box.']],
    ['Alternatives', ['<b>Portrait panel</b>: one Obsidian panel holds the whole portrait at the party frame\'s size (nothing over the face), the level on the rim\'s top diamond, name, HP and SP bars with numbers, and the buffs inside it. Debuffs hang below.',
      '<b>Arcs and plate</b>: the approved party portrait cell as it is (HP arc left, SP arc right, diamond, aggro gem, buff medallion), with a plate joined to its right for the name, the exact numbers and experience. Buffs and debuffs below the plate.',
      'Both keep the face whole and uncovered; the level moved off the chin.']],
    ['Basebar', ['<b>2 × 5</b>: keys 1–5 over 6–0. 330 px wide instead of 620; as tall as the potion and scroll sockets, so they keep their full size.',
      '<b>One row, slim sides</b>: the same ten slots in a 9 px border with sockets scaled to the bar (the sockets stay: they open the scroll and potion lists).',
      '<b>2 × 10</b>: a second row on Shift for twenty buttons, at the full width.',
      'MAW: the map progress channel and its tab are the installed ones (violet channel in the top band, 38.5 % · 112 / 292 on the right corner tab, the red notch where the dead stop rising). The status line moves above the tab.'], 'pro'],
    ['Open', ['Which frame: portrait panel or arcs and plate?', 'Which basebar: 2 × 5, slim one row, or 2 × 10?',
      'Keep the thin HP/SP strip on the bar now that the frame has exact numbers? (toggle above)'], 'con'],
  ],
};

// ---------- left vertical bar (user, 2026-11-13: move the bar under the unit frame, 1-0 in one column) ----------
const LBAR_VARIANTS = {
  corner: 'Sockets on the medallion, top left',
  knobs: 'Sockets beside the column foot',
  split: 'Sockets between 5 and 6',
  frame: 'Sockets on the unit frame',
};

function socketKnob(x, y, art, size = 46)
{
  return `<div class="knob" style="left:${x}px;top:${y}px;width:${size}px;height:${size}px"><i style="background-image:url(${A(art)})"></i></div>`;
}

function leftBar(variant, slotSize, top = 224)
{
  const S = slotSize, G = 5, border = 11, pad = 5;
  const splitGap = variant === 'split' ? 16 : 0;
  const colH = 10 * S + 9 * G + splitGap;
  const w = S + 2 * (border + pad);
  const h = colH + 2 * (border + pad);
  const x = 14, y = top;
  let s = `<div class="panel thin" style="left:${x}px;top:${y}px;width:${w}px;height:${h}px;border-width:${border}px;border-image-width:${border}px"></div>`;
  let sy = y + border + pad;
  BAR.forEach((slotDef, index) =>
  {
    if (variant === 'split' && index === 5)
    {
      // The sockets sit outside the column at the split between 5 and 6, which marks the two blocks of five.
      const ky = sy + splitGap / 2 - 2 - 42;
      s += `<div class="abs" style="left:${x + border}px;top:${sy + splitGap / 2 - 3}px;width:${w - 2 * border}px;height:2px;background:#a8925f66"></div>`;
      s += socketKnob(x + w + 6, ky, 'item_scroll', 40) + socketKnob(x + w + 6, ky + 46, 'item_cure_wounds', 40);
      sy += splitGap;
    }
    s += `<div class="abs" style="left:${x + border + pad}px;top:${sy}px;width:${S}px;height:${S}px">${slot(slotDef, 'fill')}</div>`;
    sy += S + G;
  });
  if (variant === 'knobs')
  {
    const kx = x + w + 6, ky = y + h - 2 * 46 - 14;
    s += socketKnob(kx, ky, 'item_scroll') + socketKnob(kx, ky + 52, 'item_cure_wounds');
  }
  return { html: s, bottom: y + h };
}

// Scrolling combat text about the player (user, 2026-11-13: like WoW's): heals, damage taken with what was resisted or
// blocked, SP, conditions gained and fading. Newest at the bottom; older lines rise and fade.
const SELF_TEXT = [
  { t: '+642', k: 'heal' },
  { t: '+4 SP', k: 'sp' },
  { t: '+379', k: 'heal' },
  { t: '−212 (64 blocked)', k: 'hurt' },
  { t: 'Poisoned', k: 'cond' },
  { t: '+1,238 Divine Cure', k: 'heal' },
  { t: '−184 (20 resisted)', k: 'hurt' },
  { t: '‹Poison› fades', k: 'fade' },
];

function selfText(placement)
{
  const lines = SELF_TEXT.map((line, i) =>
  {
    const age = (SELF_TEXT.length - 1 - i) / (SELF_TEXT.length - 1);
    return `<div class="sct ${line.k}" style="opacity:${(1 - 0.75 * age).toFixed(2)}">${line.t}</div>`;
  }).join('');
  if (placement === 'frame')
  {
    // A compact column under the buff rows, beside the action bar: it stays out of the fight's centre.
    return `<div class="sctbox left" style="left:${14 + 120 + 14}px;top:330px">${lines}</div>`;
  }
  // Below and right of the crosshair, where WoW draws it on the character; clear of the target's bar and floats.
  return `<div class="sctbox" style="left:${CX + 70}px;top:${CY + 60}px">${lines}</div>`;
}

VIEWS.a3 = {
  tab: 'Left bar', title: 'The action bar as one column under the unit frame; the bottom centre stays free',
  render()
  {
    let s = common();
    const dy = state.topbar === 'right' ? -46 : 0;
    const fy = 58 + dy;
    s += frameWow(14, fy);
    // Buffs to the right of the medallion, under the box; MAW progress set into the box's bottom band.
    s += tiles([PROC_BUFF, ...BUFFS], 14 + 120 + 14, fy + 29 + 98 + 10, { size: 26, gap: 9 });
    s += tiles(DEBUFFS, 14 + 120 + 14, fy + 29 + 98 + 54, { size: 26, gap: 9 });
    const bx = 14 + 120 - 26, by = fy + 29, bw = 316, bh = 98;
    if (state.maw)
    {
      s += `<div class="mawch" style="left:${bx + 40}px;top:${by + bh - 8}px;width:${bw - 70}px;height:4px">`
        + `<b style="width:${MAW.percent}%"></b><i style="left:${MAW.revivalShare / 0.9801 * 100}%"></i></div>`;
      s += `<div class="mawtab side" style="left:${bx + bw + 2}px;top:${by + bh - 22}px">${MAW.percent} % · ${MAW.slain} / ${MAW.needed}</div>`;
    }
    if (state.lbar === 'corner')
    {
      // Two small sockets on the medallion's upper-left rim, mirroring the level coin at its foot.
      s += socketKnob(6, fy, 'item_scroll', 34) + socketKnob(0, fy + 42, 'item_cure_wounds', 34);
    }
    if (state.lbar === 'frame')
    {
      s += socketKnob(bx + bw + 6, by - 6, 'item_scroll', 36) + socketKnob(bx + bw + 6, by + 34, 'item_cure_wounds', 36);
    }
    s += leftBar(state.lbar, Number(state.lslot), 224 + dy).html;
    if (state.sct !== 'off')
    {
      s += selfText(state.sct);
    }
    s += status(860, STATUS_TEXT);
    return s;
  },
  notes: [
    ['What it is', ['Keys 1–0 in one column down the left edge, under the medallion, in a slim panel of the native frame; slots 52 or 58 px (64 does not fit ten high at 900 px).',
      'The bottom centre is free for the arms, the weapon and the enemies\' feet; only the status line stays there.',
      'MAW\'s map progress moves into the unit frame\'s bottom band, its tab at the box\'s right end.']],
    ['Potion and scroll sockets', ['<b>Beside the foot</b>: two round sockets next to the bottom of the column, near keys 9 and 0.',
      '<b>Between 5 and 6</b>: the sockets split the column into two blocks of five, which also makes the keys easier to find by eye.',
      '<b>On the unit frame</b>: two sockets at the box\'s right end, by the HP and SP numbers.'], 'pro'],
    ['Self combat text (solo only)', ['WoW\'s scrolling text about the player: heals in green, damage taken in red with what was blocked or resisted, SP in blue, conditions gained in amber and fading in grey. Newest at the bottom; older lines rise and fade within about 2 s.',
      '<b>By the crosshair</b>: below and right of it, where WoW draws it on the character; read without looking away.',
      '<b>Under the buffs</b>: a compact column beside the bar, out of the fight\'s centre.',
      'Monster damage numbers stay as they are (the existing floating text over monsters).']],
    ['Open', ['Which socket placement?', '52 or 58 px slots?', 'Keys inside the slot (as now) or on a small tab outside its right edge?',
      'Self text: by the crosshair, under the buffs, or off; and whether it replaces the status line\'s combat messages in solo.'], 'con'],
  ],
};

// ---------- action bar detail sheet ----------
VIEWS.bar = {
  tab: 'Action bar', title: 'Action bar: slot states, keys, tooltip, recovery and the optional signature slot',
  render()
  {
    const fb = { art: 'spell_fireball', cost: 8, key: '5' };
    const states = [
      ['Ready', { ...fb }, 'Cost top left, key top right.'],
      ['Cooldown', { ...fb, art: 'item_boots', item: true, cost: undefined, key: '2', cd: 9, done: 0.4 }, 'Dark wedge clears clockwise; seconds left.'],
      ['Recovering', { ...fb, gcd: true, gcdDone: 0.55 }, 'Shared MM recovery after any action; lighter, no number.'],
      ['Not enough SP', { ...fb, art: 'spell_dayofthegods', cost: 70, key: '⇧4', nomana: true }, 'Blue veil, cost in red.'],
      ['Out of range', { ...fb, range: true }, 'Red veil, key in red.'],
      ['Active / aura', { art: 'item_tower_shield', item: true, key: '8', active: true }, 'Gold rim and underline while running.'],
      ['Proc', { art: 'item_sword', rot: true, key: '3', proc: true }, 'A passive fired: this button is worth pressing now.'],
      ['Charges', { art: 'buff_sba02a', key: '⇧8', count: 2, pips: [1, 1, 0] }, 'Count and pips; recharges one at a time.'],
      ['Item stack', { art: 'item_cure_wounds', item: true, key: '0', count: 7 }, 'Number carried.'],
      ['Empty', { key: '9', empty: true }, 'Engraved socket; keeps its key.'],
      ['Drag target', { art: 'spell_heal', key: '7', drag: true }, 'Dashed gold while dragging from the book or talents.'],
      ['Unusable', { art: 'item_kite_shield', item: true, key: '1', locked: true }, 'No shield equipped: Shield Bash greyed.'],
    ];
    let s = '<div class="sheet">';
    s += '<div class="abs" style="left:60px;top:34px"><h2>Action bar</h2><div class="sec">slot states · 52 px at 1600 × 900, shown at 1.4×</div></div>';
    states.forEach(([name, sl, cap], i) =>
    {
      const x = 52 + i * 124;
      s += `<div class="cell" style="left:${x}px;top:128px;width:118px"><div style="transform:scale(1.4);transform-origin:50% 0;height:84px">${slot(sl)}</div>`
        + `<div class="cap"><b>${name}</b>${cap}</div></div>`;
    });
    // two rows
    s += '<div class="abs" style="left:60px;top:352px"><div class="sec">Keys 1–0 and a second row on Shift</div>'
      + '<div class="cap" style="margin-top:4px;width:640px">The main row is 1–0. A second row is optional: Shift+1–0 (shown) or Ctrl+1–0. It shares the panel, so the bar grows upward by one row and nothing moves sideways. Mouse 4/5, Q, E, R and F stay free for block, kick, the signature skill and interact.</div></div>';
    const two = actionBarStandalone(60, 470);
    s += two;
    // anatomy
    s += anatomy(60, 660);
    // tooltip
    s += `<div class="tip" style="left:820px;top:356px">
      <h4>Fireball</h4><div class="sub">Fire Magic · Master · spell</div>
      <div class="row"><span>8 SP</span><span>range 40 m</span></div>
      <div class="row"><span>Recovery 1.1 s</span><span>no cooldown</span></div>
      <hr>Explodes on impact for 10d6 + 1d6 per point of Fire skill fire damage to everything within 2.5 m.
      <hr><div class="foot">Key 5 · drag to move · right-click to clear</div></div>`;
    s += `<div class="tip" style="left:1190px;top:356px">
      <h4>Shield Bash</h4><div class="sub" style="color:#e8c46c">Special skill · Shield · Expert · active</div>
      <div class="row"><span>no SP</span><span style="color:#f2d27a">cooldown 8 s</span></div>
      <div class="row"><span>Recovery 0.6 s</span><span>needs a shield</span></div>
      <hr>Strike with the shield for 4–8 + Shield skill damage. Stuns for 1.5 s (2 s at Master) and interrupts a monster's spell.
      <hr><div class="foot">Key 1 · rank 1/1 · from Special Skills</div></div>`;
    // crosshair states
    s += `<div class="abs" style="left:820px;top:640px"><div class="sec">Crosshair recovery brackets</div>
      <div class="cap" style="width:350px;margin-top:4px">Fill after each swing or cast; faint when ready.</div></div>`;
    [[0, 'Ready'], [0.35, 'Recovering'], [0.8, 'Almost']].forEach(([r, n], i) =>
    {
      const x = 840 + i * 116, y = 760;
      s += `<div class="abs" style="left:${x - 50}px;top:${y - 50}px;width:100px;height:100px;border-radius:4px;background:url(art/bg_goblins.jpg) -${760 + i * 40}px -${420}px / 1600px 900px"></div>`;
      s += crosshair(r).replace(`left:${CX}px;top:${CY}px`, `left:${x}px;top:${y}px`);
      s += `<div class="cap abs" style="left:${x - 50}px;top:${y + 56}px;width:100px;text-align:center">${n}</div>`;
    });
    // signature slot
    s += `<div class="abs" style="left:1190px;top:640px"><div class="sec">Optional: signature skill</div>
      <div class="cap" style="width:350px;margin-top:4px">One Grandmaster talent on its own key (R), with a recharge bar that fills from kills and hits, like a Vermintide career skill.</div></div>`;
    s += `<div class="abs" style="left:1196px;top:740px">${slot({ art: 'spell_sunray', key: 'R', recharge: 0.72, cdText: '' }, 'big')}</div>`;
    s += `<div class="abs" style="left:1282px;top:742px">${slot({ art: 'spell_sunray', key: 'R', recharge: 1, proc: true }, 'big')}</div>`;
    s += '<div class="cap abs" style="left:1196px;top:820px;width:200px">Charging (72 %) · ready</div>';
    return s + '</div>';
  },
  notes: [
    ['Rules', ['Mana cost always visible (top left), so you know what the next press costs before pressing.',
      'Cooldown shows seconds only above 1.5 s; below that only the wedge, to avoid flicker.',
      'Recovering is the shared MM recovery after any action (the old per-character recovery, now per action): a lighter wedge on every slot that needs it.',
      'Proc and active use gold; resources use blue (SP) and red (range); nothing else on the bar is coloured.']],
    ['Open', ['Second row on Shift or on Ctrl? Shift is easier to reach while moving with WASD; Ctrl often crouches.',
      'Should the signature skill exist, and recharge from damage dealt (Vermintide) or from time?'], 'con'],
  ],
};

function actionBarStandalone(x, y)
{
  const border = 16, pad = 7, w = BAR_W + 2 * (border + pad), h = 2 * SLOT + 8 + 2 * (border + pad);
  return `<div class="panel thin" style="left:${x}px;top:${y}px;width:${w}px;height:${h}px"></div>`
    + slotsRow(BAR_SHIFT, x + border + pad, y + border + pad) + slotsRow(BAR, x + border + pad, y + border + pad + SLOT + 8);
}

function anatomy(x, y)
{
  const s = { art: 'item_boots', item: true, key: '2', cost: 4, cd: 9, done: 0.4, count: 3 };
  const callout = (text, lx, ly, tx, ty) => `<svg class="abs" style="left:0;top:0;overflow:visible" width="1" height="1"><line x1="${lx}" y1="${ly}" x2="${tx}" y2="${ty}" stroke="#b29a64" stroke-width="1"/></svg>`
    + `<div class="cap abs" style="left:${tx + (tx < lx ? -170 : 6)}px;top:${ty - 10}px;width:164px;${tx < lx ? 'text-align:right' : ''}">${text}</div>`;
  const sx = x + 260, sy = y + 30;
  return `<div class="abs" style="left:${x}px;top:${y}px"><div class="sec">Anatomy at 2×</div></div>`
    + `<div class="abs" style="left:${sx}px;top:${sy}px;transform:scale(2);transform-origin:0 0">${slot(s)}</div>`
    + callout('Cost in SP (blue tab)', sx + 10, sy + 12, sx - 60, sy + 4)
    + callout('Key (SMALLNUM)', sx + 96, sy + 10, sx + 160, sy + 2)
    + callout('Seconds left', sx + 52, sy + 52, sx - 60, sy + 64)
    + callout('Charges or stack', sx + 96, sy + 94, sx + 160, sy + 104);
}

// ---------- special skills (talents) ----------
const SCHOOLS = [
  ['Weapons', [['Sword', 'm', 14], ['Dagger', 'e', 6], ['Axe', '', 0], ['Mace', 'n', 3], ['Spear', '', 0], ['Staff', '', 0], ['Bow', 'e', 7], ['Unarmed', 'n', 2]]],
  ['Armour', [['Shield', 'm', 12, true], ['Leather', 'e', 5], ['Chain', 'm', 10], ['Plate', '', 0], ['Dodging', '', 0], ['Armsmaster', 'e', 8]]],
  ['Magic', [['Fire', 'm', 12], ['Air', 'e', 7], ['Water', '', 0], ['Earth', 'e', 6], ['Spirit', 'n', 4], ['Mind', '', 0], ['Body', 'e', 7], ['Light', '', 0], ['Dark', '', 0]]],
];
const MASTERY = { n: 'Normal', e: 'Expert', m: 'Master', g: 'Grandmaster' };

const SHIELD_TREE = [
  ['e', 'Expert', 'Shield at Expert', [
    { name: 'Shield Bash', type: 'active', art: 'item_kite_shield', item: true, st: 'learned', rank: '1/1', bar: '1' },
    { name: 'Brace', type: 'passive', art: 'buff_sba06a', st: 'learned', rank: '2/2' },
    { name: 'Deflect', type: 'passive', art: 'buff_sbb09a', st: 'avail', rank: '0/1' }]],
  ['m', 'Master', 'Shield at Master', [
    { name: 'Shield Wall', type: 'active', art: 'item_tower_shield', item: true, st: 'learned sel', rank: '1/1', bar: '8' },
    { name: 'Spell Ward', type: 'passive', art: 'buff_sbm03a', st: 'avail', rank: '0/2' },
    { name: 'Shield Charge', type: 'active', art: 'item_boots', item: true, st: 'avail', rank: '0/1' }]],
  ['g', 'Grandmaster', 'needs Shield at Grandmaster', [
    { name: 'Bulwark', type: 'passive', art: 'buff_sbdk07a', st: 'locked', rank: '0/1' },
    { name: 'Rally', type: 'active', art: 'buff_sbl09a', st: 'locked', rank: '0/1' },
    { name: 'Aegis', type: 'active', art: 'buff_combat', st: 'locked', rank: '0/1' }]],
];

VIEWS.talents = {
  tab: 'Special skills', title: 'Special skills: a talent layer on the MM skills, in the Obsidian 4:3 overlay',
  render()
  {
    let s = '<div class="dim"></div><div class="frame43"><div class="in">';
    s += `<div class="abs" style="left:0;top:-4px"><h2 style="font:36px Fondamento,serif;color:#eadfc6;margin:0">Special Skills</h2>
      <div class="cap" style="font:15px Lucida,sans-serif;color:#c8c7a7">Zoltan · level 47 · <span style="color:#e3c185">3 points to spend</span> · next point at level 50</div></div>`;
    s += '<div class="abs" style="right:0;top:0"><span class="btn">Close</span></div>';
    s += '<div class="abs" style="left:560px;top:-6px;display:flex;gap:6px">'
      + ['Skills', 'Special Skills', 'Spells'].map((t, i) => `<span class="btn${i === 1 ? ' hot' : ''}" style="font-size:17px">${t}</span>`).join('') + '</div>';
    // school list
    s += '<div class="schools">';
    SCHOOLS.forEach(([grp, list]) =>
    {
      s += `<div class="grp">${grp}</div>`;
      list.forEach(([name, m, lv, sel]) =>
      {
        const off = !m;
        s += `<div class="sk${sel ? ' sel' : ''}${off ? ' off' : ''}"><span>${name}${lv ? `<span class="n">${lv}</span>` : ''}</span>`
          + `<em class="m-${m || 'n'}">${off ? '–' : MASTERY[m]}</em></div>`;
      });
    });
    s += '</div>';
    // tree
    s += '<div class="tree">';
    SHIELD_TREE.forEach(([m, label, req, nodes]) =>
    {
      s += `<div class="tier"><div class="th m-${m}">${label}<small>${req}</small></div>`;
      nodes.forEach((n, i) =>
      {
        const icon = n.item ? `<div class="ic item" style="background-image:url(${A(n.art)})">` : `<div class="ic" style="background-image:url(${A(n.art)})">`;
        s += `<div class="tnode ${n.type} ${n.st}" style="left:${i * 158}px">${icon}<span class="rank">${n.rank}</span>`
          + `${n.bar ? `<span class="onbar keycap">${n.bar}</span>` : ''}</div>`
          + `<div class="nm">${n.name}</div><div class="ty">${n.type === 'active' ? 'Active · cooldown' : 'Passive'}</div></div>`;
      });
      s += '</div>';
    });
    s += `<div class="cap" style="margin-top:10px;display:flex;gap:22px;align-items:center">
      <span><span style="display:inline-block;width:14px;height:14px;border-radius:50%;box-shadow:0 0 0 2px #e3c185;vertical-align:-2px"></span> active, on the bar</span>
      <span><span style="display:inline-block;width:14px;height:14px;border-radius:2px;box-shadow:0 0 0 2px #e3c185;vertical-align:-2px"></span> passive</span>
      <span style="color:#59d2c8">teal rim: learnable now</span></div>`;
    s += '</div>';
    // detail card
    s += `<div class="detail" style="width:372px">
      <div style="display:flex;gap:14px;align-items:center">
        <div style="width:72px;height:72px;border-radius:50%;background:#1a1f1f url(${A('item_tower_shield')}) center/contain no-repeat;box-shadow:0 0 0 2px #e3c185,0 0 14px #e3c18566"></div>
        <div><h3>Shield Wall</h3><div class="kind">Active · Shield · Master</div></div></div>
      <div class="stats"><span>Cooldown</span><span>45 s</span><span>Duration</span><span>8 s (+1 s per 5 Shield skill)</span>
        <span>Cost</span><span>none · 0.5 s recovery</span><span>Needs</span><span>a shield in the off hand</span></div>
      <p>Raise the shield and plant your feet. For the duration, damage from the front is reduced by 60 % and you cannot be knocked back or stunned. Moving is slowed by half.</p>
      <p style="color:#9aa294;font-size:13.5px">Learned · rank 1/1 · on the action bar, key 8. Greyed out on the bar while no shield is equipped.</p>
      <div style="display:flex;gap:10px;margin-top:14px"><span class="btn">Learned</span><span class="btn hot">Put on bar…</span></div>
      <div class="sec" style="margin-top:20px">Next for 1 point</div>
      <p style="margin-top:4px"><b style="font:16px Arrus,serif;font-weight:normal;color:#eadfc6">Spell Ward</b> · passive · a raised shield adds 20 + Shield skill to all magic resistances.</p>
    </div>`;
    // footer
    s += `<div class="foot43"><div style="display:flex;gap:28px">
      <div class="cap" style="width:520px"><b>Points</b>One at every 10th level (10, 20, 30 …) and one at each class promotion. Mastery from the trainers unlocks the tiers; points pick within them.</div>
      <div class="cap" style="width:520px"><b>Free with mastery</b>Each school's first Expert active (Shield Bash, Charge, Blink …) is learned free when you reach Expert, so a new character has buttons to press before level 10.</div>
    </div></div>`;
    return s + '</div></div>';
  },
  notes: [
    ['How it sits on MM', ['MM skills stay exactly as they are: skill points raise the level, trainers sell Expert / Master / Grandmaster.',
      'Each school (the weapon, armour and magic skills) gets three tiers of special skills, one per mastery rank above Normal.',
      'Tiers open with the mastery, so the trainers stay the gate; talent points choose within an open tier.',
      'Active special skills go on the action bar and have cooldowns; passive ones need no button.']],
    ['Point gain', ['Solo, the character gets the whole party\'s experience: XP for a level grows with level², so four times the XP is about twice the level. A party member at 50 is a solo character near 100.',
      'One point per 10 levels then gives about 10 points by the end of one MM game and 20 in a long MMerge run; per 5 levels gives 20/40.',
      'Recommended: per 10 levels + 1 per promotion + the free Expert active per school. Per 5 makes every school\'s tree complete and the choice meaningless.']],
    ['Open', ['Respec: free at any trainer, or for gold?', 'Do spells count as "special skills" too (Fire Master unlocks Fire talents), or only weapons and armour? This mockup does both.',
      'Should talents be available in party mode as well (one per member)? The screen works for both.'], 'con'],
  ],
};

// ---------- portrait comparison ----------
VIEWS.portrait = {
  tab: 'Need the portrait?', title: 'Do we need the portrait? Four answers side by side',
  render()
  {
    let s = '<div class="sheet">';
    s += '<div class="abs" style="left:60px;top:30px"><h2>Do we need the portrait?</h2><div class="sec">same scene, same values · click a thumbnail\'s tab above for full size</div></div>';
    const opts = [['a', 'A · Unit frame top-left'], ['b', 'B · No portrait'], ['c', 'C · Big arc portrait'], ['d', 'D · Orbs, no portrait']];
    opts.forEach(([id, name], i) =>
    {
      const x = 60 + i * 380;
      s += `<div class="thumb" style="left:${x}px;top:112px"><div class="stage">${VIEWS[id].render()}</div></div>`;
      s += `<div class="tcap" style="left:${x}px;top:326px">${name}</div>`;
    });
    const rows = [
      ['Identity: face, name, level', ['●●● face, name, level', '●○○ level only', '●●● large face, level', '●○○ level only'], [1, 0, 1, 0]],
      ['MM conditions on the face', ['●●○ small face', '○○○ icons only', '●●● large face', '○○○ icons only'], [1, 0, 1, 0]],
      ['HP/SP near the crosshair', ['●○○ top-left (R adds an echo)', '●●○ low, slim', '●●● under the crosshair', '●●● big orbs'], [0, 0, 1, 1]],
      ['Exact numbers', ['●●● in the bars', '●●○ small labels', '●○○ beside the arcs', '●●● in the orbs'], [1, 0, 0, 1]],
      ['Buffs with timers', ['●●● one list under the frame', '●●○ split by the bars', '●○○ three places', '●●○ above the bar'], [1, 0, 0, 0]],
      ['Screen kept free at the bottom', ['●●● 96 px bar', '●●● floating slots', '○○○ 214 px panel', '●○○ 148 px orbs'], [1, 1, 0, 0]],
      ['Fits the approved Obsidian kit', ['●●○ panel, sockets', '●○○ plain', '●●● the approved arcs', '○○○ new orb art'], [0, 0, 1, 0]],
    ];
    s += '<table class="cmp" style="left:60px;top:378px;width:1000px"><tr><th></th>' + opts.map(([, n]) => `<th>${n.split(' · ')[0]}</th>`).join('') + '</tr>';
    rows.forEach(([crit, cells, win]) =>
    {
      s += `<tr><td>${crit}</td>${cells.map((c, i) => `<td class="${win[i] ? 'win' : c.startsWith('○') ? 'bad' : ''}">${c}</td>`).join('')}</tr>`;
    });
    s += '</table>';
    s += `<div class="abs" style="left:1100px;top:378px;width:440px">
      <div class="sec">Recommendation</div>
      <h2 style="font-size:28px;margin:4px 0 8px">Keep the face, move it up</h2>
      <div class="cap" style="font-size:15px;line-height:1.5">
      <p style="margin:0 0 8px">Yes, keep a portrait: in Might and Magic the face is the character, and it carries the conditions (poisoned, asleep, afraid, insane) that no icon row shows as well.</p>
      <p style="margin:0 0 8px">But not at the bottom. A solo action screen spends the bottom on the weapon, the shield and the enemy's feet; a 214 px portrait there (C) costs the most.</p>
      <p style="margin:0 0 8px">So: <b style="display:inline;font-size:15px;color:#e3c185">R</b> — a compact unit frame top-left with the approved oval rim, level badge, name, HP/SP bars with numbers and one buff list; the ten-slot bar bottom-centre in the basebar's panel with its sockets; a thin HP/SP echo on the bar and recovery brackets on the crosshair.</p>
      <p style="margin:0">Orbs (D) read fastest but are foreign to MM and clash with the green HP bands.</p></div></div>`;
    return s + '</div>';
  },
  notes: [
    ['Summary', ['Portrait: yes, small, top-left (A/R). Not as the centre of the bottom bar (C) and not dropped (B, D).',
      'HP and SP: bars with numbers in the frame, plus a thin echo on the action bar. Not orbs.',
      'Action bar: yes, bottom-centre, ten slots, keys 1–0, optional Shift row.',
      'Special skills: actives on the bar with cooldowns; passives only visible when they fire (proc glow + gold-rimmed buff).']],
  ],
};

// ---------- page ----------
const ORDER = ['a3', 'a2', 'r', 'a', 'b', 'c', 'd', 'today', 'bar', 'talents', 'portrait'];
const params = new URLSearchParams(location.search);
const state = {
  view: ORDER.includes(params.get('view')) ? params.get('view') : 'a3',
  lbar: LBAR_VARIANTS[params.get('lbar')] ? params.get('lbar') : 'corner',
  lslot: ['52', '58', '64'].includes(params.get('lslot')) ? params.get('lslot') : '58',
  topbar: params.get('topbar') === 'left' ? 'left' : 'right',
  clock: ['below', 'off'].includes(params.get('clock')) ? params.get('clock') : 'rim',
  sct: ['off', 'center', 'frame'].includes(params.get('sct')) ? params.get('sct') : 'center',
  frame: ['full', 'arcs'].includes(params.get('frame')) ? params.get('frame') : 'wow',
  bar: BAR_LAYOUTS[params.get('bar')] ? params.get('bar') : 'rows5',
  maw: params.get('maw') !== '0',
  echo: params.get('echo') === '1',
  vm: true,
  arms: ARMS.some(([id]) => id === params.get('arms')) ? params.get('arms') : 'sword_shield_idle',
  recovery: params.has('rec') ? Number(params.get('rec')) : 0.62,
};
if (params.get('export') === '1')
{
  document.body.classList.add('export');
}

function renderTabs()
{
  document.getElementById('tabs').innerHTML = ORDER.map((id) =>
    `<button data-v="${id}" aria-pressed="${id === state.view}">${VIEWS[id].tab}</button>`).join('');
  document.querySelectorAll('#tabs button').forEach((b) => b.addEventListener('click', () =>
  {
    state.view = b.dataset.v;
    try
    {
      const u = new URL(location.href);
      u.searchParams.set('view', state.view);
      history.replaceState(null, '', u);
    }
    catch (e)
    {
      // Some hosts (sandboxed frames) refuse URL changes; the tab still switches.
    }
    render();
  }));
}

function renderControls()
{
  const hud = ['a3', 'a2', 'r', 'a', 'b', 'c', 'd'].includes(state.view);
  const group = (key, options) => `<span class="seg">${options.map(([id, label]) =>
    `<button data-k="${key}" data-v="${id}" aria-pressed="${state[key] === id}">${label}</button>`).join('')}</span>`;
  const leftCtl = state.view === 'a3'
    ? `<label>Sockets ${group('lbar', Object.entries(LBAR_VARIANTS))}</label>
       <label>Top bar ${group('topbar', [['right', 'Top right'], ['left', 'Top left']])}</label>
       <label>Clock ${group('clock', [['rim', 'On the minimap rim'], ['off', 'Off'], ['below', 'Under the minimap']])}</label>
       <label>Slots ${group('lslot', [['52', '52 px'], ['58', '58 px'], ['64', '64 px']])}</label>
       <label>Self text ${group('sct', [['center', 'By the crosshair'], ['frame', 'Under the buffs'], ['off', 'Off']])}</label>
       <label><input type="checkbox" id="maw" ${state.maw ? 'checked' : ''}> MAW map progress</label>`
    : '';
  const refined = state.view === 'a2'
    ? `<label>Frame ${group('frame', [['wow', 'Unit frame'], ['full', 'Portrait panel'], ['arcs', 'Arcs and plate']])}</label>
       <label>Basebar ${group('bar', Object.entries(BAR_LAYOUTS).map(([id, l]) => [id, l.label]))}</label>
       <label><input type="checkbox" id="maw" ${state.maw ? 'checked' : ''}> MAW map progress</label>
       <label><input type="checkbox" id="echo" ${state.echo ? 'checked' : ''}> HP/SP strip on the bar</label>`
    : '';
  document.getElementById('controls').innerHTML = (hud ? leftCtl + refined : '') + (hud
    ? `<label>Arms ${group('arms', ARMS)}</label>
       <label>Recovery <input type="range" id="rec" min="0" max="1" step="0.05" value="${state.recovery}"></label>
       <span style="color:#9aa294">${VIEWS[state.view].title}</span>`
    : `<span style="color:#9aa294">${VIEWS[state.view].title}</span>`);
  document.querySelectorAll('#controls .seg button').forEach((b) => b.addEventListener('click', () =>
  {
    state[b.dataset.k] = b.dataset.v;
    renderControls();
    renderStage();
  }));
  for (const id of ['maw', 'echo'])
  {
    const box = document.getElementById(id);
    if (box) box.addEventListener('change', () => { state[id] = box.checked; renderStage(); });
  }
  const rec = document.getElementById('rec');
  if (rec) rec.addEventListener('input', () => { state.recovery = Number(rec.value); renderStage(); });
}

function renderStage()
{
  const v = VIEWS[state.view];
  const stage = document.getElementById('stage');
  stage.className = `stage ${v.stageClass ?? ''}`;
  const hudView = ['a3', 'a2', 'r', 'a', 'b', 'c', 'd'].includes(state.view);
  stage.style.backgroundImage = hudView && state.arms !== 'placeholder' ? `url(oblivion/${state.arms}.jpg)` : '';
  stage.innerHTML = v.render();
  fit();
}

function renderNotes()
{
  document.getElementById('notes').innerHTML = VIEWS[state.view].notes.map(([h, items, kind]) =>
    `<section><h3>${h}</h3><ul>${items.map((t) => `<li class="${kind ?? ''}">${t}</li>`).join('')}</ul></section>`).join('');
}

function fit()
{
  const wrap = document.getElementById('stageScale');
  const stage = document.getElementById('stage');
  const scale = document.body.classList.contains('export') ? 1 : Math.min(1, wrap.parentElement.clientWidth / 1600);
  stage.style.transform = `scale(${scale})`;
  wrap.style.width = `${1600 * scale}px`;
  wrap.style.height = `${900 * scale}px`;
}

function render()
{
  renderTabs();
  renderControls();
  renderStage();
  renderNotes();
}

window.addEventListener('resize', fit);
document.fonts.ready.then(() => document.body.setAttribute('data-ready', '1'));
render();
