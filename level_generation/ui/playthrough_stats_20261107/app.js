// Playthrough statistics mockup. All numbers are one consistent sample playthrough.
'use strict';

const MEMBERS = ['Kareth', 'Elara', 'Mara', 'Vaelis', 'Tor'];

const fmt = (n) => n.toLocaleString('en-US');
const pct = (n, total) => (100 * n / total).toFixed(n / total < 0.1 ? 1 : 0) + '%';

// Breakdown popups, keyed by row id. Each is a list of blocks.
const BREAKDOWNS = {
  played: { title: 'Time played', width: 640, blocks: [
    { rows: [['This session', '1:12:40'], ['Longest session', '3:41:02'], ['Sessions', '37'], ['Average session', '1:07:13']] },
    { rows: [['In this timeline', '38:14:30', '92%'], ['Undone by loading', '3:12:40', '8%']] },
    { sect: 'By continent', rows: [['Jadame', '31:05:12', '75%'], ['Antagarich', '7:40:31', '19%'], ['Enroth', '2:41:27', '6%']] },
    { rule: true },
    { note: 'First played 14 Oct 2026, last played 7 Nov 2026. Counts only while a game is running in a focused window, outside the pause menu.' },
  ] },
  turnbased: { title: 'Turn-based combat', width: 620, blocks: [
    { rows: [['Time in turn-based', '6:12:44', '15%'], ['Fights entered', '188', ''], ['Turns taken', '2,904', ''], ['Average fight', '1:59', '']] },
    { rows: [['Kills in turn-based', '1,031', '43%']] },
  ] },
  xp: { title: 'Experience earned', width: 660, blocks: [
    { rows: [['Monsters', fmt(1021400), pct(1021400, 1284330)], ['Quests and events', fmt(243930), pct(243930, 1284330)], ['Other', fmt(19000), pct(19000, 1284330)]] },
    { note: 'Other: wells, fountains, books and potions.' },
    { rule: true },
    { rows: [['Largest single award', fmt(40000), ''], ['Including undone play', fmt(1371920), '']] },
  ] },
  levels: { title: 'Levels gained', width: 560, blocks: [
    { rows: MEMBERS.map((m, i) => [m, ['19', '20', '19', '20', '16'][i], 'lvl ' + ['20', '21', '20', '21', '17'][i]]) },
    { rule: true },
    { rows: [['Training cost', fmt(412000), '']] },
  ] },
  saves: { title: 'Saves and loads', width: 560, blocks: [
    { sect: 'Saves', rows: [['Quicksaves', '204', ''], ['Autosaves', '96', ''], ['Named slots', '11', '']] },
    { sect: 'Loads', rows: [['Quickloads', '287', ''], ['From the Load screen', '115', ''], ['After a party wipe', '4', '']] },
  ] },
  kills: { title: 'Monsters killed', width: 660, blocks: [
    { sect: 'By method', rows: [['Melee', fmt(1322), pct(1322, 2417)], ['Missiles', fmt(310), pct(310, 2417)], ['Spells', fmt(755), pct(755, 2417)], ['Allies and traps', fmt(30), pct(30, 2417)]] },
    { sect: 'Most slain', rows: [['Lizardman', '214', ''], ['Skeleton', '188', ''], ['Ogre', '141', ''], ['Harpy', '120', ''], ['Dragonfly', '96', '']] },
    { rule: true },
    { rows: [['Strongest foe', 'Dragon, level 60'], ['Including undone play', fmt(2688)]], two: true },
  ] },
  damage: { title: 'Damage dealt', width: 720, bars: [
    ['Physical', 1160000, '#c9b58a'], ['Fire', 271000, '#d8814f'], ['Air', 166000, '#9fc4d8'], ['Light', 101000, '#efe2a8'],
    ['Dark', 77233, '#8f7aa8'], ['Water', 54000, '#5e8fc0'], ['Earth', 38000, '#9b8a5c'], ['Mind, Body', 37000, '#b88aa0'],
  ], total: 1904233, after: [
    { rule: true },
    { rows: [['Critical hits', fmt(3104), ''], ['Largest hit', '1,226', ''], ['', 'Vaelis, Fire, Ogre', ''], ['Including undone play', fmt(2117480), '']] },
  ] },
  taken: { title: 'Damage taken', width: 620, blocks: [
    { rows: [['Melee', fmt(368100), pct(368100, 612880)], ['Missiles', fmt(61200), pct(61200, 612880)], ['Spells', fmt(171580), pct(171580, 612880)], ['Falls, traps, water', fmt(12000), pct(12000, 612880)]] },
    { rule: true },
    { rows: [['Largest hit taken', '688', ''], ['', 'Dragon breath, Tor', '']] },
  ] },
  biggest: { title: 'Largest hit', width: 640, blocks: [
    { rows: [['1,226', 'Vaelis, Fire, Ogre', ''], ['1,104', 'Tor, Axe, Lizardman', ''], ['1,050', 'Vaelis, Fire, Dragon', ''], ['  812', 'Kareth, Sword, Troll', ''], ['  690', 'Mara, Earth, Golem', '']] },
  ] },
  spells: { title: 'Spells cast', width: 600, blocks: [
    { sect: 'Most cast', rows: [['Heal', '902', ''], ['Fire Bolt', '611', ''], ['Lightning Bolt', '402', ''], ['Bless', '233', ''], ['Fly', '188', '']] },
    { rule: true },
    { rows: [['Cast from scrolls', '64', ''], ['Spell points spent', fmt(98420), '']] },
  ] },
  deaths: { title: 'Deaths', width: 700, blocks: [
    { sect: 'By member', rows: [['Vaelis', '8', ''], ['Kareth', '6', ''], ['Mara', '4', ''], ['Tor', '3', ''], ['Elara', '2', '']] },
    { sect: 'Deadliest', rows: [['Lich', '5', ''], ['Dragon', '4', ''], ['Falling', '2', '']] },
    { sect: 'Latest', rows: [['Vaelis', 'Lich, Necropolis', 'day 188'], ['Tor', 'Dragon, Dragon Cave', 'day 171'], ['Kareth', 'Ogre, Ogre Fortress', 'day 140']] },
    { rule: true },
    { rows: [['Including undone play', '31', '']] },
  ] },
  wipes: { title: 'Party wipes', width: 620, blocks: [
    { rows: [['Lich, Necropolis', '', 'day 188'], ['Dragon, Dragon Cave', '', 'day 171'], ['Ogre Fortress', '', 'day 92'], ['Shadowspire', '', 'day 61']] },
    { rule: true },
    { rows: [['Gold lost to wipes', fmt(14200), ''], ['Loaded afterwards', '4 of 4', '']] },
  ] },
  temple: { title: 'Temple healings', width: 560, blocks: [
    { rows: [['Healings', '11', ''], ['Members raised', '9', ''], ['Gold paid', fmt(38200), ''], ['Donations', fmt(1500), '']] },
  ] },
  tp: { title: 'Town Portal', width: 560, blocks: [
    { sect: 'Most used destination', rows: [['Ravenshore', '29', ''], ['Alvar', '14', ''], ['Balthazar Lair', '9', '']] },
    { rows: [['Scrolls used', '6', '']] },
  ] },
  lloyd: { title: "Lloyd's Beacon", width: 560, blocks: [
    { rows: [['Recalls', '98', ''], ['Beacons set', '14', '']] },
  ] },
  travel: { title: 'Coach and ship', width: 560, blocks: [
    { rows: [['Coach trips', '11', ''], ['Ship voyages', '8', ''], ['Days travelled', '63', ''], ['Gold paid', fmt(9310), '']] },
  ] },
  maps: { title: 'Maps visited', width: 560, blocks: [
    { rows: [['Outdoor areas', '17', ''], ['Dungeons and buildings', '41', '']] },
    { note: 'A map counts once, the first time the party enters it.' },
  ] },
  chests: { title: 'Chests opened', width: 560, blocks: [
    { rows: [['Opened', '412', ''], ['Traps disarmed', '121', ''], ['Traps sprung', '37', ''], ['Damage from traps', fmt(8400), '']] },
  ] },
  looted: { title: 'Gold looted', width: 600, blocks: [
    { rows: [['Corpses', fmt(402300), pct(402300, 812450)], ['Chests', fmt(288150), pct(288150, 812450)], ['Ground', fmt(31000), pct(31000, 812450)], ['Quests and events', fmt(91000), pct(91000, 812450)]] },
    { rule: true },
    { rows: [['Shared with followers', fmt(6400), '']] },
  ] },
  spent: { title: 'Gold spent', width: 620, blocks: [
    { rows: [['Training', fmt(412000), pct(412000, 790110)], ['Shops', fmt(288600), pct(288600, 790110)], ['Temples', fmt(38200), pct(38200, 790110)], ['Spells and guilds', fmt(34000), pct(34000, 790110)], ['Travel', fmt(9310), pct(9310, 790110)], ['Other', fmt(8000), pct(8000, 790110)]] },
    { rule: true },
    { rows: [['Earned selling items', fmt(301400), '']] },
  ] },
  artifacts: { title: 'Artifacts found', width: 600, blocks: [
    { rows: [['Mash', 'day 66', ''], ['Hermes’ Sandals', 'day 98', ''], ['Ethric’s Staff', 'day 140', ''], ['and four more', '', '']] },
  ] },
};

// Overview groups: [label, value, class, breakdown id].
const OVERVIEW = [
  [
    { h: 'Time', rows: [['Played', '41:27:10', '', 'played'], ['Game time', '214 days', '', 'played'], ['Turn-based', '6:12:44', '', 'turnbased'], ['Sessions', '37', '', 'played']] },
    { h: 'Experience', rows: [['Earned', fmt(1284330), '', 'xp'], ['Per hour', fmt(30983), 'gold', 'xp'], ['Levels gained', '94', '', 'levels']] },
    { h: 'Saves', rows: [['Saves', '311', '', 'saves'], ['Loads', '402', '', 'saves']] },
  ],
  [
    { h: 'Combat', rows: [['Monsters killed', fmt(2417), '', 'kills'], ['Kills per hour', '58.3', 'gold', 'kills'], ['Damage dealt', fmt(1904233), '', 'damage'], ['Damage taken', fmt(612880), '', 'taken'], ['Largest hit', '1,226', 'gold', 'biggest'], ['Spells cast', fmt(4118), '', 'spells']] },
    { h: 'Losses', rows: [['Deaths', '23', 'bad', 'deaths'], ['Eradications', '2', 'bad', 'deaths'], ['Party wipes', '4', 'bad', 'wipes'], ['Temple healings', '11', '', 'temple']] },
  ],
  [
    { h: 'Exploration', rows: [['Town Portals', '64', '', 'tp'], ["Lloyd's Beacons", '98', '', 'lloyd'], ['Coach and ship', '19', '', 'travel'], ['Maps visited', '58', '', 'maps'], ['Chests opened', '412', '', 'chests']] },
    { h: 'Wealth', rows: [['Gold looted', fmt(812450), '', 'looted'], ['Gold spent', fmt(790110), '', 'spent'], ['Artifacts found', '7', '', 'artifacts']] },
  ],
];

// Old-save variant: tracking began on load of a save made before statistics existed.
const OVERVIEW_PARTIAL = [
  [
    { h: 'Time', rows: [['Played', '0:48:05', '', ''], ['Game time', '9 days', '', ''], ['Turn-based', '0:06:12', '', ''], ['Sessions', '2', '', '']] },
    { h: 'Experience', rows: [['Earned', fmt(18210), '', ''], ['Per hour', fmt(22720), 'gold', ''], ['Levels gained', '3', '', '']] },
    { h: 'Saves', rows: [['Saves', '5', '', ''], ['Loads', '3', '', '']] },
  ],
  [
    { h: 'Combat', rows: [['Monsters killed', '41', '', ''], ['Kills per hour', '51.2', 'gold', ''], ['Damage dealt', fmt(23104), '', ''], ['Damage taken', fmt(6022), '', ''], ['Largest hit', '211', 'gold', ''], ['Spells cast', '58', '', '']] },
    { h: 'Losses', rows: [['Deaths', '0', 'dim', ''], ['Eradications', '0', 'dim', ''], ['Party wipes', '0', 'dim', ''], ['Temple healings', '1', '', '']] },
  ],
  [
    { h: 'Exploration', rows: [['Town Portals', '2', '', ''], ["Lloyd's Beacons", '0', 'dim', ''], ['Coach and ship', '1', '', ''], ['Maps visited', '4', '', ''], ['Chests opened', '6', '', '']] },
    { h: 'Wealth', rows: [['Gold looted', fmt(3620), '', ''], ['Gold spent', fmt(2950), '', ''], ['Artifacts found', '0', 'dim', '']] },
  ],
];

// Party tab rows: label, five values, optional formatter flags.
const PARTY = [
  ['Kills', [712, 214, 388, 731, 342]],
  ['Damage dealt', [512300, 108450, 296880, 640103, 318200]],
  ['Share', [512300, 108450, 296880, 640103, 318200], 'share'],
  ['Largest hit', [812, 340, 690, 1226, 1104]],
  ['Damage taken', [198400, 88210, 92770, 71300, 162200], 'low'],
  ['Spells cast', [96, 1488, 1102, 1320, 112]],
  ['Healing given', [0, 402880, 151300, 0, 0]],
  ['Knocked out', [31, 12, 19, 27, 22], 'low'],
  ['Deaths', [6, 2, 4, 8, 3], 'low'],
  ['Experience', [251200, 262400, 258900, 270330, 241500]],
];

function el(tag, cls, html) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (html !== undefined) e.innerHTML = html;
  return e;
}

function img(cls, src) {
  const i = el('img', cls);
  i.src = src;
  i.alt = '';
  return i;
}

function baseFrame(tab) {
  const f = el('div', 'frame');
  f.append(img('surface', 'assets/art/obsidian_reading_surface.png'));
  f.append(img('basebar', 'assets/art/basebar_capture.png'));
  const s = el('div', 'session');
  s.append(el('h4', '', 'This session'));
  for (const [k, v] of [['Time', '1:12:40'], ['Kills', '34'], ['Experience', '21,480'], ['Deaths', '0']]) {
    const r = el('div', 'srow');
    r.append(el('span', '', k), el('span', '', v));
    s.append(r);
  }
  f.append(s);
  const b = el('div', 'buttons');
  b.append(el('div', 'btn' + (tab === 'overview' ? ' sel' : ''), 'Overview'));
  b.append(el('div', 'btn' + (tab === 'party' ? ' sel' : ''), 'Party'));
  b.append(el('div', 'hint', tab === 'party' ? 'Hold right mouse on a name for that member’s full record' : 'Hold right mouse on a line for its breakdown'));
  b.append(el('div', 'btn exit', 'Exit'));
  f.append(b);
  return f;
}

function header(f, partial) {
  const h = el('div', 'hdr');
  if (partial) {
    h.append(el('div', 'title', 'Statistics'));
    h.append(el('div', 'since', 'Tracked since 7 Nov 2026: this party’s earlier play predates statistics'));
  } else {
    h.append(el('div', 'title', 'Begun 14 October 2026'));
    h.append(el('div', 'sub', 'Jadame start · MAW · Normal'));
    h.append(el('div', 'played', 'Played<b>41:27:10</b>'));
  }
  f.append(h);
}

function overviewFrame(opts = {}) {
  const f = baseFrame('overview');
  header(f, opts.partial);
  const cols = el('div', 'cols');
  const data = opts.partial ? OVERVIEW_PARTIAL : OVERVIEW;
  for (const col of data) {
    const c = el('div', 'col');
    for (const g of col) {
      const gr = el('div', 'group');
      gr.append(el('h3', '', g.h));
      for (const [label, value, cls, id] of g.rows) {
        const r = el('div', 'row' + (id ? ' inspectable' : ''));
        r.dataset.breakdown = id;
        r.append(el('span', 'k', label), el('span', 'v ' + (cls || ''), value));
        if (opts.hot && opts.hot === label) r.classList.add('hot');
        gr.append(r);
      }
      c.append(gr);
    }
    cols.append(c);
  }
  f.append(cols);
  return f;
}

function partyFrame() {
  const f = baseFrame('party');
  header(f, false);
  const t = el('div', 'ptable');
  t.append(el('div', 'corner', ''));
  for (const m of MEMBERS) t.append(el('div', 'name c', m));
  const total = 1904233;
  PARTY.forEach(([label, vals, kind], rowIndex) => {
    const sep = rowIndex === 4 || rowIndex === 9 ? ' sep' : '';
    t.append(el('div', 'lbl' + sep, label));
    const best = Math.max(...vals);
    vals.forEach((v) => {
      const cell = el('div', 'c' + sep);
      if (kind === 'share') {
        const s = el('div', 'share');
        const tr = el('div', 'track');
        const fill = el('div', 'fill');
        fill.style.width = (100 * v / best).toFixed(1) + '%';
        tr.append(fill);
        s.append(tr, el('span', '', (100 * v / total).toFixed(0) + '%'));
        cell.append(s);
      } else {
        const span = el('span', '', v === 0 ? '–' : fmt(v));
        if (v === 0) span.style.color = 'var(--dim)';
        else if (v === best && kind !== 'low') span.className = 'top';
        cell.append(span);
      }
      t.append(cell);
    });
  });
  f.append(t);
  f.append(el('div', 'former', 'Former members: Gavin (dismissed day 40, 30 kills). Allies and traps: 30 kills, 28,300 damage.'));
  return f;
}

function popupFrame(id, x, y) {
  const d = BREAKDOWNS[id];
  const p = el('div', 'popup');
  p.style.left = x + 'px';
  p.style.top = y + 'px';
  p.style.width = d.width + 'px';
  p.append(el('div', 'bg'));
  for (const c of ['tl', 'tr', 'bl', 'br', 't', 'b', 'l', 'r']) p.append(el('div', 'edge ' + c));
  const body = el('div', 'body');
  body.append(el('div', 'ptitle', d.title));
  const renderBlocks = (blocks) => {
    for (const b of blocks) {
      if (b.sect) body.append(el('div', 'sect', b.sect));
      if (b.rule) body.append(el('div', 'rule'));
      if (b.note) body.append(el('div', 'note', b.note));
      if (b.rows) {
        for (const [k, n, pc] of b.rows) {
          const r = el('div', 'prow' + (b.two ? ' two' : ''));
          r.append(el('span', 'k', k), el('span', 'n', n));
          if (!b.two) r.append(el('span', 'p', pc || ''));
          body.append(r);
        }
      }
    }
  };
  if (d.bars) {
    for (const [k, n, color] of d.bars) {
      const r = el('div', 'barrow');
      const tr = el('div', 'track');
      const fill = el('div', 'fill');
      fill.style.width = (100 * n / d.bars[0][1]).toFixed(1) + '%';
      fill.style.background = `linear-gradient(${color}, ${color}99)`;
      tr.append(fill);
      r.append(el('span', '', k), tr, el('span', 'n', fmt(n)), el('span', 'p', pct(n, d.total)));
      body.append(r);
    }
    renderBlocks(d.after);
  } else {
    renderBlocks(d.blocks);
  }
  p.append(body);
  return p;
}

function topBarFrame() {
  const f = el('div', 'frame');
  f.append(el('div', 'barstage'));
  const icons = ['obsidian_books', 'obsidian_party', 'obsidian_rest', 'obsidian_options'];
  const build = (top, withStats) => {
    const s = 3;  // logical to frame pixels
    const width = (withStats ? 298 : 268) * s;
    const tb = el('div', 'tb');
    tb.style.left = '40px';
    tb.style.top = top + 'px';
    tb.style.width = width + 'px';
    tb.append(el('div', 'plate'));
    const gold = el('div', 'res');
    gold.style.left = 6 * s + 'px';
    gold.append(img('', 'assets/art/scorebg_gold.png'), el('span', '', '10,027'));
    const food = el('div', 'res');
    food.style.left = 76 * s + 'px';
    food.append(img('', 'assets/art/scorebg_food.png'), el('span', '', '7'));
    tb.append(gold, food);
    const order = withStats ? ['obsidian_books', 'obsidian_party', 'STATS', 'obsidian_rest', 'obsidian_options'] : icons;
    order.forEach((name, i) => {
      const ic = el('div', 'ico' + (name === 'STATS' ? ' hover' : ''));
      ic.style.left = (144 + i * 30) * s + 'px';
      ic.append(img('', name === 'STATS' ? STATS_ICON : `assets/art/${name}.png`));
      tb.append(ic);
    });
    return tb;
  };
  const a = build(46, false);
  const b = build(176, true);
  const la = el('div', 'tblabel', 'Now');
  la.style.left = '40px'; la.style.top = '14px';
  const lb = el('div', 'tblabel', 'Proposed: Statistics between Party and Rest');
  lb.style.left = '40px'; lb.style.top = '144px';
  const tip = el('div', 'tip', 'Statistics <b>(F1)</b>');
  tip.style.left = (40 + (144 + 2 * 30) * 3 - 40) + 'px';
  tip.style.top = '250px';
  f.append(a, la, b, lb, tip);
  return f;
}

let STATS_ICON = 'assets/art/stats_icon_a.png';

// Scale every authored 1280-wide frame to its viewport.
function fit(vp) {
  const f = vp.querySelector('.frame');
  if (f) f.style.transform = `scale(${vp.clientWidth / 1280})`;
}

function mount(id, frame, extraClass) {
  const host = document.getElementById(id);
  if (!host) return null;
  const vp = el('div', 'viewport' + (extraClass ? ' ' + extraClass : ''));
  vp.append(frame);
  host.append(vp);
  new ResizeObserver(() => fit(vp)).observe(vp);
  fit(vp);
  return vp;
}

// Live overview: hold the right mouse button on a line to see its breakdown, release to close.
function makeInteractive(vp) {
  const frame = vp.querySelector('.frame');
  let open = null;
  const close = () => {
    if (open) open.remove();
    open = null;
    frame.querySelectorAll('.row.hot').forEach((r) => r.classList.remove('hot'));
  };
  frame.addEventListener('contextmenu', (e) => e.preventDefault());
  frame.addEventListener('mousedown', (e) => {
    if (e.button !== 2) return;
    const row = e.target.closest('.row.inspectable');
    if (!row || !row.dataset.breakdown) return;
    close();
    row.classList.add('hot');
    const scale = vp.clientWidth / 1280;
    const fr = frame.getBoundingClientRect();
    const rr = row.getBoundingClientRect();
    const d = BREAKDOWNS[row.dataset.breakdown];
    const rowX = (rr.left - fr.left) / scale;
    const rowY = (rr.top - fr.top) / scale;
    open = popupFrame(row.dataset.breakdown, 0, 0);
    frame.append(open);
    place(open, rowX, rowY, rr.width / scale, rr.height / scale);
  });
  window.addEventListener('mouseup', (e) => { if (e.button === 2) close(); });
  window.addEventListener('blur', close);
}

// Below the row if it fits, else above, else beside its column; never over the inspected row.
function place(popup, rowX, rowY, rowW, rowH) {
  const w = popup.offsetWidth;
  const h = popup.offsetHeight;
  let x = Math.max(16, Math.min(1264 - w, rowX + rowW / 2 - w / 2));
  let y;
  if (rowY + rowH + 6 + h <= 948) {
    y = rowY + rowH + 6;
  } else if (rowY - 6 - h >= 12) {
    y = rowY - 6 - h;
  } else {
    x = rowX + rowW + 24 + w <= 1264 ? rowX + rowW + 24 : Math.max(16, rowX - 24 - w);
    y = Math.max(12, Math.min(948 - h, rowY + rowH / 2 - h / 2));
  }
  popup.style.left = x + 'px';
  popup.style.top = y + 'px';
}

const STATIC_POPUPS = [];

function popupShot(id, hotLabel) {
  const f = overviewFrame({ hot: hotLabel });
  const p = popupFrame(id, 0, 0);
  f.append(p);
  STATIC_POPUPS.push(p);
  return f;
}

function placeStaticPopups() {
  for (const p of STATIC_POPUPS) {
    const row = p.parentElement.querySelector('.row.hot');
    let x = 0;
    let y = 0;
    for (let n = row; n && n !== p.parentElement; n = n.offsetParent) {
      x += n.offsetLeft;
      y += n.offsetTop;
    }
    place(p, x, y, row.offsetWidth, row.offsetHeight);
  }
}

function buildPage() {
  mount('shot-bar', topBarFrame(), 'bar');
  const live = mount('shot-overview', overviewFrame());
  if (live) makeInteractive(live);
  mount('shot-party', partyFrame());
  mount('shot-xp', popupShot('xp', 'Earned'));
  mount('shot-kills', popupShot('kills', 'Monsters killed'));
  mount('shot-damage', popupShot('damage', 'Damage dealt'));
  mount('shot-deaths', popupShot('deaths', 'Deaths'));
  mount('shot-played', popupShot('played', 'Played'));
  mount('shot-partial', overviewFrame({ partial: true }));
  placeStaticPopups();
}

function chooseIcon() {
  const candidates = ['candidate_a', 'candidate_b', 'candidate_c'];
  const want = new URLSearchParams(location.search).get('icon');
  if (want && candidates.includes(want)) STATS_ICON = `assets/art/stats_icon_${want.slice(-1)}.png`;
}

const FACES = ['Native Lucida', 'Native Arrus', 'Native Create', 'Native Smallnum', 'Fondamento'];
Promise.all(FACES.map((f) => document.fonts.load(`30px "${f}"`))).catch(() => {}).then(() => {
  chooseIcon();
  buildPage();
});
