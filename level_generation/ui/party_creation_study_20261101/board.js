// Party skill board ("bingo"): skills as rows, the five members as columns, shared by approaches B and C.
'use strict';

function cellHtml(mi, s) {
  const m = App.members[mi];
  const st = skillState(m, s);
  const planned = m.plan.includes(s);
  const focus = App.focus && App.focus.m === mi && App.focus.skill === s;
  const glyph = st === 'fixed' || st === 'chosen' || st === 'option' ? `<span class="sg ${st}"></span>` : '';
  const content = st === 'none' ? '·' : glyph + mastery(capNow(m, s), capBest(m, s));
  return `<span class="cell ${st}${planned ? ' planned' : ''}${mi === App.sel ? ' selcol' : ''}${focus ? ' focus' : ''}" data-skill="${s}" data-m="${mi}">${content}</span>`;
}

function halfHtml(groups) {
  let heads = '';
  for (let i = 0; i < 5; i++) {
    const m = App.members[i];
    if (m) {
      const p = portraitById(m.portrait);
      heads += `<button class="mhead${i === App.sel ? ' sel' : ''}" data-select="${i}">${badge(i)}<span class="portrait">${portraitImg(p)}</span><span class="cl">${esc(className(m.cls))}</span></button>`;
    } else {
      heads += `<button class="mhead add" ${i === App.members.length ? 'data-add' : 'disabled'} style="${i === App.members.length ? '' : 'opacity:.3'}"><span class="portrait">+</span><span class="cl">add</span></button>`;
    }
  }
  let rows = '';
  for (const [group, skills] of groups) {
    rows += `<div class="bgroup">${group}</div>`;
    for (const s of skills) {
      const cov = coverage(s);
      const covered = cov.length > 0;
      const bestCovered = Math.max(0, ...cov.map(c => capBest(App.members[c.i], s)));
      let cells = '';
      for (let i = 0; i < 5; i++) cells += App.members[i] ? cellHtml(i, s) : '<span class="cell"></span>';
      rows += `<div class="brow${covered ? ' covered' : partyBest(s) ? ' open' : ''}"><span class="nm" data-skill="${s}" data-m="${App.sel}">${esc(skillName(s))}${raceMarks(App.members[App.sel], s)}</span>${cells}
        <span class="best">${covered ? `<span class="mc${bestCovered}">${LETTER_SHOW[bestCovered]}</span>` : '<span class="dim">–</span>'}</span></div>`;
    }
  }
  return `<div class="bhalf"><div class="bhead"><span class="t">Skill</span>${heads}<span class="t" style="text-align:center">Party</span></div>${rows}</div>`;
}


function boardHtml() {
  const groups = skillGroups();
  const left = groups.filter(([g]) => ['Weapons', 'Armour', 'Racial'].includes(g));
  const right = groups.filter(([g]) => !['Weapons', 'Armour', 'Racial'].includes(g));
  return `<div class="board stone">${halfHtml(left)}${halfHtml(right)}</div>`;
}
function boardSummary() {
  const all = skillList().filter(s => partyBest(s) > 0);
  const covered = all.filter(s => coverage(s).length);
  const gm = covered.filter(s => Math.max(...coverage(s).map(c => capBest(App.members[c.i], s))) === 4);
  return `Party covers <b style="color:#f0dfb5;font-weight:normal">${covered.length}</b> of ${all.length} reachable skills · ${gm.length} to Grandmaster`;
}
