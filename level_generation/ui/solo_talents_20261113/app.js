'use strict';
// Solo talent study (2026-11-13). Every view draws into one 1600 x 900 stage, the native 4:3 character screen;
// ?view=<id>&export=1 shows the stage alone for the preview captures. Values are simulated.

const A = (name) => `art/${name}.png`;
const HERO = { name: 'Zoltan the Battle Mage', level: 64, earned: 6, spent: 5 };
const AVAILABLE = HERO.earned - HERO.spent;
const NEXT_LEVEL = (Math.floor(HERO.level / 10) + 1) * 10;

// The approved trees (BALANCE_AND_TALENTS.md §5.0). rank: learned ranks; lock: the requirement that is not met (the
// locks are this study's proposal: actives need the matching MM skill at Expert or Master, passives are always open).
// ranks: the value at each rank. bar: the action-bar key of a learned active.
const TREES = [
  { id: 'melee', name: 'Melee', nodes: [
    { name: 'Weapon Training', kind: 'passive', max: 5, rank: 3, art: 'item_sword', rot: true,
      what: 'Might, Endurance and Speed', ranks: ['+2 %', '+4 %', '+6 %', '+8 %', '+10 %'],
      text: 'Raises Might, Endurance and Speed by a share of their total.' },
    { name: 'Cleave', kind: 'active', max: 3, rank: 1, art: 'item_axe', rot: true, bar: '3',
      what: 'Cooldown', ranks: ['12 s', '10 s', '8 s'],
      text: 'The next swing hits up to 5 monsters in its arc for 60 % of its damage, each with its own roll to hit.' },
    { name: 'Whirlwind', kind: 'active', max: 3, rank: 0, art: 'spell_shrapmetal', lock: 'needs Sword, Axe or Mace at Master',
      what: 'Cooldown', ranks: ['20 s', '17 s', '14 s'],
      text: 'A spin: every monster within melee reach, all around, takes 50 % of a blow.' },
    { name: 'Frenzy', kind: 'active', max: 3, rank: 0, art: 'buff_sbf08a',
      what: 'Duration', ranks: ['6 s', '7 s', '8 s'],
      text: '+25 % attack speed. Cooldown 30 s.' },
    { name: 'Charge', kind: 'active', max: 3, rank: 0, art: 'item_boots', item: true,
      what: 'Cooldown', ranks: ['25 s', '22 s', '19 s'],
      text: 'Dash to the monster under the crosshair and stagger it.' },
    { name: 'Shield Wall', kind: 'active', max: 3, rank: 0, art: 'item_tower_shield', item: true, lock: 'needs Shield at Expert',
      what: 'Cooldown', ranks: ['60 s', '50 s', '40 s'],
      text: 'With a shield: 50 % less damage for 6 s.' },
  ] },
  { id: 'ranged', name: 'Ranged', nodes: [
    { name: 'Marksman', kind: 'passive', max: 5, rank: 0, art: 'item_longbow', rot: true,
      what: 'Accuracy and Speed', ranks: ['+2 %', '+4 %', '+6 %', '+8 %', '+10 %'],
      text: 'Raises Accuracy and Speed by a share of their total.' },
    { name: 'Volley', kind: 'active', max: 3, rank: 0, art: 'spell_icebolt', lock: 'needs Bow at Expert',
      what: 'Cooldown', ranks: ['12 s', '10 s', '8 s'],
      text: 'Five arrows in a cone, each for 60 % of a shot.' },
    { name: 'Disengage', kind: 'active', max: 3, rank: 0, art: 'buff_sba02a', lock: 'needs Bow at Expert',
      what: 'Cooldown', ranks: ['15 s', '13 s', '11 s'],
      text: 'Leap 4 m back.' },
    { name: 'Pinning Shot', kind: 'active', max: 3, rank: 0, art: 'spell_paralyze', lock: 'needs Bow at Expert',
      what: 'Slow', ranks: ['4 s', '5 s', '6 s'],
      text: 'A shot that slows its target by half. Cooldown 10 s.' },
    { name: 'Steady Aim', kind: 'passive', max: 3, rank: 0, art: 'buff_sbb09a',
      what: 'Critical chance', ranks: ['+3 %', '+6 %', '+9 %'],
      text: 'After standing still for 1 s, shots have a higher critical chance.' },
  ] },
  { id: 'caster', name: 'Caster', nodes: [
    { name: 'Attunement', kind: 'passive', max: 5, rank: 1, art: 'buff_sbv02a',
      what: 'Intellect, Personality, Endurance, spell damage and healing', ranks: ['+2 %', '+4 %', '+6 %', '+8 %', '+10 %'],
      text: 'Raises the caster\'s stats, spell damage and healing done.' },
    { name: 'Blink', kind: 'active', max: 3, rank: 0, art: 'buff_sba10a',
      what: 'Cooldown', ranks: ['15 s', '13 s', '11 s'],
      text: 'Teleport 15 m forward, as WoW\'s Blink. Uses the monsters\' blink effect and sound.' },
    { name: 'Spell Surge', kind: 'active', max: 3, rank: 0, art: 'spell_incinerate', lock: 'needs a magic school at Master',
      what: 'Cooldown', ranks: ['45 s', '40 s', '35 s'],
      text: 'The next spell costs no SP and hits ×1.5.' },
    { name: 'Mana Font', kind: 'passive', max: 5, rank: 0, art: 'buff_sbs03a',
      what: 'SP every 5 s per 10 levels', ranks: ['+1', '+2', '+3', '+4', '+5'],
      text: 'Spell points flow back over time, more at higher levels.' },
    { name: 'Purify', kind: 'active', max: 3, rank: 0, art: 'spell_curepoison', lock: 'needs Body or Spirit at Expert',
      what: 'Cooldown', ranks: ['30 s', '25 s', '20 s'],
      text: 'Cure one condition and be immune to it for 5 s.' },
    { name: 'Resolve', kind: 'passive', max: 5, rank: 0, art: 'buff_sbl08a',
      what: 'All resistances', ranks: ['+2 %', '+4 %', '+6 %', '+8 %', '+10 %'],
      text: 'Raises every resistance by a share of its total.' },
  ] },
];
const SELECTED = TREES[0].nodes[1];  // Cleave

function stateOf(n)
{
  if (n.lock && n.rank === 0) return 'locked';
  if (n.rank === 0) return AVAILABLE > 0 ? 'learnable' : '';
  return n.rank < n.max && AVAILABLE > 0 ? 'learned more' : 'learned';
}
const spentIn = (tree) => tree.nodes.reduce((s, n) => s + n.rank, 0);

function icon(n, size = 56)
{
  const bg = n.rot ? '' : `background-image:url(${A(n.art)})`;
  return `<div class="ic ${n.item ? 'item' : ''}" style="width:${size}px;height:${size}px;${bg}">`
    + (n.rot ? `<u style="background-image:url(${A(n.art)})"></u>` : '')
    + (n.bar ? `<span class="keycap">${n.bar}</span>` : '') + '</div>';
}
function pips(n)
{
  let s = '<div class="pips">';
  for (let i = 0; i < n.max; ++i)
  {
    s += `<b class="${i < n.rank ? 'on' : i === n.rank && stateOf(n).includes('learn') && !n.lock ? 'next' : ''}"></b>`;
  }
  return s + '</div>';
}
function rankTable(n)
{
  let s = `<div class="ranks"><span class="k">${n.what}</span><span></span>`;
  n.ranks.forEach((v, i) =>
  {
    const cls = i + 1 === n.rank ? 'cur' : i === n.rank ? 'nx' : '';
    const tag = i + 1 === n.rank ? ' · current' : i === n.rank ? ' · next' : '';
    s += `<span class="k">Rank ${i + 1}</span><span class="${cls}">${v}${tag}</span>`;
  });
  return s + '</div>';
}
function kindLine(n, tree)
{
  return `${n.kind === 'active' ? 'Active' : 'Passive'} · ${tree} · rank ${n.rank}/${n.max}`;
}

const page = (wide = false) => `<div class="page${wide ? ' wide' : ''}"></div>`;
function header(extraLeft = '')
{
  return `<div class="hdr" style="top:${45 + 18}px;left:${200 + 31}px;width:${875 - 62}px">
    <span>${extraLeft || HERO.name}</span>
    <span class="pts">Talent Points: <b>${AVAILABLE}</b><small>one every 10 levels · next at level ${NEXT_LEVEL}</small></span></div>`;
}
function buttonRow(selected, six = true)
{
  const names = six ? ['Stats', 'Skills', 'Talents', 'Inventory', 'Awards', 'Exit'] : ['Stats', 'Skills', 'Inventory', 'Awards', 'Exit'];
  const w = six ? 131 : 140, step = six ? 141 : 169, x0 = six ? 220 : 230;
  return names.map((n, i) => `<div class="tabbtn ${n === selected ? 'sel' : ''} ${n === 'Talents' ? 'new' : ''}"
    style="left:${x0 + i * step}px;top:632px;width:${w}px">${n}</div>`).join('');
}
function miniBar(keyOn)
{
  const keys = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'];
  return `<div style="display:flex;gap:4px;margin-top:6px">${keys.map((k) =>
    `<span style="width:30px;height:30px;display:grid;place-items:center;font:13px Smallnum,monospace;border-radius:2px;
      ${k === keyOn ? 'background:#2a2c22 url(art/item_axe.png) center/80% no-repeat;box-shadow:0 0 0 2px #f2d27a' : 'background:#0b1012;box-shadow:inset 0 0 0 1px #6f6448'};color:#eadfc6">
      <span style="align-self:start;justify-self:end;margin:-2px 2px 0 0;text-shadow:0 0 2px #000">${k}</span></span>`).join('')}</div>`;
}

const VIEWS = {};

// ---------- A: three columns ----------
VIEWS.a = {
  tab: 'A · Three columns', title: 'A · Three columns on the left page, the paperdoll kept; hover card',
  render()
  {
    let s = page() + header();
    TREES.forEach((tree, c) =>
    {
      const x = 231 + c * 282;
      s += `<div class="grp abs" style="left:${x}px;top:118px">${tree.name}<small>${spentIn(tree)} pts</small></div>`;
      s += `<div class="rule" style="left:${x}px;top:164px;width:262px"></div>`;
      tree.nodes.forEach((n, i) =>
      {
        const y = 176 + i * 71;
        const st = stateOf(n);
        s += `<div class="node ${n.kind} ${st} ${n === SELECTED ? 'sel' : ''}" style="left:${x}px;top:${y}px">${icon(n, 52)}</div>`;
        s += `<div class="node ${st}" style="left:${x + 66}px;top:${y + 1}px;width:200px">
          <div class="nm" style="font-size:21px">${n.name}</div>
          <div style="display:flex;gap:10px;align-items:center;margin-top:6px">${pips(n)}
          <span class="req">${n.lock && n.rank === 0 ? 'locked' : n.rank + '/' + n.max}</span></div></div>`;
      });
    });
    // hover card for Cleave, beside it
    const n = SELECTED;
    s += `<div class="card" style="left:372px;top:226px;width:440px"><div class="in">
      <h3>${n.name}</h3><div class="kind">${kindLine(n, 'Melee')}</div>
      <p>${n.text}</p>${rankTable(n)}
      <p class="hint">Click: learn rank ${n.rank + 1} (1 point). On the action bar: key ${n.bar}. Right-click: put on bar or move.</p>
      </div></div>`;
    s += `<div class="smallbtn" style="left:948px;top:588px">Reset</div>`;
    return s + buttonRow('Talents');
  },
  notes: [
    ['What it is', ['A sixth tab, Talents, between Skills and Inventory (the five native buttons narrow to fit six).',
      'All three trees at once in the left page, one node per row: icon (round: active, square: passive), name, rank pips and n/max. The paperdoll stays.',
      'Hover shows a card with the per-rank numbers, the current and next rank, and the bar key. Click learns the next rank; right-click puts an active on the bar.',
      'States: gold rim learned, teal rim learnable now, gold and teal learned with a rank to buy, grey with a padlock locked (the requirement shown in the card).']],
    ['For', ['Everything at a glance: 17 nodes, three trees, the points spent in each.', 'Keeps the screen\'s structure: same page, same paperdoll, same buttons.', 'Icons are there to recognise on the action bar.'], 'pro'],
    ['Against', ['Six tab buttons are tighter than the native five.', 'The card covers a neighbouring column while it is open.', 'No room to grow a tree beyond about seven nodes.'], 'con'],
  ],
};

// ---------- B: tabs per tree, grid and detail panel ----------
VIEWS.b = {
  tab: 'B · Tabs and detail', title: 'B · One tree at a time, large nodes, a detail panel in place of the paperdoll',
  render()
  {
    const tree = TREES[state.tree];
    let s = page(true) + header();
    TREES.forEach((t, i) =>
    {
      s += `<div class="tabbtn ${i === state.tree ? 'sel' : ''}" style="left:${231 + i * 168}px;top:112px;width:158px;font-size:22px">${t.name} · ${spentIn(t)}</div>`;
    });
    const passives = tree.nodes.filter((n) => n.kind === 'passive');
    const actives = tree.nodes.filter((n) => n.kind === 'active');
    const rowAt = (list, y, label) =>
    {
      let r = `<div class="grp abs" style="left:231px;top:${y}px;font-size:24px">${label}</div>`;
      r += `<div class="rule" style="left:231px;top:${y + 34}px;width:600px"></div>`;
      list.forEach((n, i) =>
      {
        const x = 231 + i * 122;
        const st = stateOf(n);
        r += `<div class="node ${n.kind} ${st} ${n === SELECTED && state.tree === 0 ? 'sel' : ''}" style="left:${x + 25}px;top:${y + 50}px">${icon(n, 72)}</div>`;
        r += `<div class="node ${st}" style="left:${x}px;top:${y + 132}px;width:122px;text-align:center">
          <div class="nm" style="font-size:18px">${n.name}</div>
          <div style="display:flex;justify-content:center;margin-top:6px">${pips(n)}</div>
          ${n.lock && n.rank === 0 ? `<div class="req" style="font-size:12px;margin-top:2px">${n.lock.replace('needs ', 'needs<br>')}</div>` : ''}</div>`;
      });
      return r;
    };
    s += rowAt(passives, 170, 'Passive');
    s += rowAt(actives, 380, 'Active');
    const n = state.tree === 0 ? SELECTED : tree.nodes.find((x) => x.kind === 'active') ?? tree.nodes[0];
    s += `<div class="card" style="left:868px;top:122px;width:510px;height:502px"><div class="in">
      <div style="display:flex;gap:16px;align-items:center">${icon(n, 72).replace('class="ic', `class="ic" data-k="${n.kind}`)}
      <div><h3>${n.name}</h3><div class="kind">${kindLine(n, tree.name)}</div></div></div>
      <p>${n.text}</p>${rankTable(n)}
      ${n.lock ? `<p style="color:#d99b86">Locked: ${n.lock}.</p>` : ''}
      <div style="display:flex;gap:10px;margin:12px 0 4px"><span class="smallbtn ${AVAILABLE > 0 && !n.lock ? 'hot' : 'dim'}" style="position:static">Learn rank ${Math.min(n.rank + 1, n.max)}</span></div>
      ${n.kind === 'active' ? `<div class="kind" style="margin-top:14px">On the action bar</div>${miniBar(n.bar)}
      <p class="hint">Click a key to place it; drag the icon onto the bar in play.</p>` : ''}
      </div></div>`;
    s += `<div class="smallbtn" style="left:231px;top:578px">Reset talents</div>`;
    return s + buttonRow('Talents');
  },
  notes: [
    ['What it is', ['The Talents tab takes the whole screen width: the paperdoll gives way to a detail panel.',
      'One tree at a time behind three tabs that show the points spent in each. Passives in one row, actives in another, large icons.',
      'The detail panel always shows the selected node: per-rank table with current and next, the lock reason, Learn, and for actives a ten-key strip to put it on the bar.']],
    ['For', ['Most room for numbers and the bar assignment; no hovering needed (Android-friendly).', 'Scales to bigger trees later.'], 'pro'],
    ['Against', ['Two of three trees are hidden; a mixed build means switching tabs.', 'Breaks the screen\'s rule that the paperdoll is always there.', 'Five or six nodes per tree leave the grid half empty.'], 'con'],
  ],
};

// ---------- C: the native Skills list ----------
VIEWS.c = {
  tab: 'C · Skills-page list', title: 'C · As the native Skills page: rows, blue when learnable, held right-click inspects',
  render()
  {
    let s = page();
    s += `<div class="hdr" style="top:63px;left:231px;width:813px">
      <span><span class="subtab">Skills</span><span class="subtab on">Talents</span></span>
      <span class="pts">Talent Points: <b>${AVAILABLE}</b><small>next at level ${NEXT_LEVEL}</small></span></div>`;
    const col = (tree, x, y0) =>
    {
      let r = `<div class="grp abs" style="left:${x}px;top:${y0}px">${tree.name}</div>`;
      r += `<div class="rule" style="left:${x}px;top:${y0 + 46}px;width:390px"></div>`;
      tree.nodes.forEach((n, i) =>
      {
        const st = stateOf(n);
        const cls = st.startsWith('learnable') || st === 'learned more' ? 'learnable' : st === 'locked' ? 'locked' : '';
        const bg = n.rot ? `background-image:url(${A(n.art)});transform:rotate(45deg) scale(.8)` : `background-image:url(${A(n.art)})`;
        r += `<div class="row ${cls} ${n.kind === 'active' ? 'active-kind' : ''} ${n === SELECTED ? 'hover' : ''}" style="left:${x}px;top:${y0 + 52 + i * 30}px;width:390px">
          <span class="mini ${n.item ? 'item' : ''}" style="${bg}"></span><span style="font-size:26.5px">${n.name}</span>
          <span class="r" style="font-size:26.5px">${n.lock && n.rank === 0 ? '–' : n.rank + '/' + n.max}</span></div>`;
      });
      return r;
    };
    s += col(TREES[0], 231, 112);
    s += col(TREES[1], 231, 112 + 52 + 6 * 30 + 24);
    s += col(TREES[2], 655, 112);
    s += `<div class="abs" style="left:655px;top:${112 + 52 + 6 * 30 + 30}px;width:390px;font:15px Smallnum,monospace;color:#9aa294;line-height:1.5">
      ● round: active, goes on the bar<br>■ square: passive<br><span style="color:#8ebcfa">blue: click to learn the next rank</span><br>grey: locked (hold right-click to see why)</div>`;
    const n = SELECTED;
    s += `<div class="inspect" style="left:400px;top:236px"><h3>${n.name}</h3>
      <p style="text-align:center;color:#e3c185;margin:0 0 8px">${kindLine(n, 'Melee')}</p>
      <p>${n.text}</p><div class="ranks" style="display:grid;grid-template-columns:auto 1fr;gap:2px 12px">${n.ranks.map((v, i) =>
        `<span style="color:#9aa294">Rank ${i + 1}</span><span style="color:${i + 1 === n.rank ? '#eadfc6' : i === n.rank ? '#85df8b' : '#c8c7a7'}">${n.what} ${v}${i + 1 === n.rank ? ' (current)' : ''}</span>`).join('')}</div>
      <p style="color:#9aa294">On the action bar: key ${n.bar}. Drag the row onto the bar, or press a number key while holding right-click.</p></div>`;
    s += `<div class="smallbtn" style="left:908px;top:592px;height:30px;font-size:16px">Reset</div>`;
    return s + buttonRow('Skills', false);
  },
  notes: [
    ['What it is', ['No new button: Skills gains a second page, toggled in its header (Skills | Talents), so the native five buttons stay.',
      'Rows exactly like the skill rows: Lucida, a pale blue row is one you can raise now (whole-row click learns the next rank), grey is locked, ivory is maxed or waiting for points; n/max where the skill level is.',
      'A small icon before each name, round for actives and square for passives. Held right-click opens the native inspect popup (Create title, Smallnum body) with the per-rank numbers.']],
    ['For', ['Most native: it reads as part of the MM Skills page and teaches nothing new.', 'Keeps the five buttons and the paperdoll.', 'Fits many more nodes.'], 'pro'],
    ['Against', ['Text-first: actives are small to recognise for the action bar.', 'Ranks as n/max are less vivid than pips.', 'The header toggle is easy to miss.'], 'con'],
  ],
};

// ---------- the Standard ruleset ----------
VIEWS.std = {
  tab: 'Standard / party', title: 'Standard ruleset, or any party game: nothing changes',
  stageClass: 'plain',
  render()
  {
    return '<div class="caption" style="top:600px">Standard ruleset or a party game: no Talents button or page; the screen is unchanged.</div>';
  },
  notes: [
    ['Rule', ['Talents exist only in an augmented solo run under MAW. In Standard (solo or party) and in MAW party games the character screen is exactly today\'s: five buttons, no Talents page, no points shown.',
      'A MAW solo run that is loaded under another ruleset build does not exist: the run\'s ruleset is fixed at new game.']],
  ],
};

// ---------- page ----------
const ORDER = ['a', 'b', 'c', 'std'];
const params = new URLSearchParams(location.search);
const state = {
  view: ORDER.includes(params.get('view')) ? params.get('view') : 'a',
  tree: Math.min(Math.max(Number(params.get('tree') ?? 0) || 0, 0), 2),
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
      // Some hosts refuse URL changes; the view still switches.
    }
    render();
  }));
}

function renderControls()
{
  const treeSwitch = state.view === 'b'
    ? `<label>Tree <span class="seg">${TREES.map((t, i) => `<button data-t="${i}" aria-pressed="${i === state.tree}">${t.name}</button>`).join('')}</span></label>`
    : '';
  document.getElementById('controls').innerHTML = treeSwitch + `<span>${VIEWS[state.view].title}</span>`;
  document.querySelectorAll('#controls .seg button').forEach((b) => b.addEventListener('click', () =>
  {
    state.tree = Number(b.dataset.t);
    renderControls();
    renderStage();
  }));
}

function renderStage()
{
  const v = VIEWS[state.view];
  const stage = document.getElementById('stage');
  stage.className = `stage ${v.stageClass ?? ''}`;
  stage.innerHTML = v.render();
  fit();
}

function renderNotes()
{
  const common = [['Shared in every variant', ['Points: one per 10 levels; the header shows the points to spend and the next point\'s level.',
    'Locks (proposal): passives are always open; actives need the matching MM skill at Expert (Whirlwind and Spell Surge at Master).',
    'Reset button shown; the respec rule (free, gold, at a trainer) is open.',
    'Icons are existing game art as placeholders. New icons needed: Weapon Training, Cleave, Whirlwind, Frenzy, Charge, Shield Wall, Marksman, Volley, Disengage, Pinning Shot, Steady Aim, Attunement, Blink, Spell Surge, Mana Font, Purify and Resolve (all 17).']]];
  document.getElementById('notes').innerHTML = VIEWS[state.view].notes.concat(state.view === 'std' ? [] : common)
    .map(([h, items, kind]) => `<section><h3>${h}</h3><ul>${items.map((t) => `<li class="${kind ?? ''}">${t}</li>`).join('')}</ul></section>`).join('');
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
render();
