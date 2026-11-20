// Solo talent tree v3 mockups: the Talents planner page. window.LAYOUT is 'columns' (mockup A) or 'web' (mockup B).
// URL: ?class=knight_2h&diff=nightmare&level=120&build=example|empty&tip=<node id>
(function () {
  var C = window.TreeCore, T = C.T;
  var q = new URLSearchParams(location.search);
  var state = {
    cls: q.get('class') || 'knight_2h', diff: q.get('diff') || 'nightmare', level: +(q.get('level') || 120),
    ranks: {}, keystones: [], tip: q.get('tip') || null, tipKind: 'node'
  };
  function loadExample() {
    var b = C.exampleBuild(state.cls, state.level);
    state.ranks = b.ranks; state.keystones = b.keystones;
  }
  if (q.get('build') !== 'empty') { loadExample(); }

  var stage = document.getElementById('stage');
  function fit() {
    var s = Math.min(innerWidth / 1280, innerHeight / 720);
    stage.style.transform = 'scale(' + s + ')';
    stage.style.left = Math.max(0, (innerWidth - 1280 * s) / 2) + 'px';
    stage.style.top = Math.max(0, (innerHeight - 720 * s) / 2) + 'px';
  }
  addEventListener('resize', fit);

  function el(tag, cls, html) { var e = document.createElement(tag); if (cls) { e.className = cls; } if (html !== undefined) { e.innerHTML = html; } return e; }
  function mark(node, pathColor) {
    var m = el('span', 'mark ' + (node.kind || 'keystone'));
    m.style.setProperty('--pc', pathColor);
    if (C.hasIcon(node.id)) { m.innerHTML = '<img alt="" src="art/talent_' + node.id + '.png">'; }
    else { m.textContent = node.name.split(' ').map(function (w) { return w[0]; }).join('').slice(0, 2); }
    if (node.isNew) { m.appendChild(el('span', 'newdot')); }
    return m;
  }
  function trimmed(state) { // drop ranks the level no longer pays for, highest tiers first
    var guard = 0;
    while (C.spent(state.ranks) > T.points(state.level) && guard++ < 500) {
      var ids = Object.keys(state.ranks).filter(function (id) { return state.ranks[id] > 0 && C.canRemove(state, C.byId[id]); })
        .sort(function (a, b) { return C.byId[b].tier - C.byId[a].tier; });
      if (!ids.length) { break; }
      state.ranks[ids[0]]--;
    }
    state.keystones = state.keystones.slice(0, C.keystoneSlots(state.level));
  }
  function add(node) { if (C.refusal(state, node) === '') { state.ranks[node.id] = (state.ranks[node.id] || 0) + 1; } }
  function remove(node) { if (C.canRemove(state, node)) { state.ranks[node.id]--; } }

  // ---- header ------------------------------------------------------------------------------------------------------
  var top = el('div', 'top');
  top.innerHTML = '<h1>Talents</h1>' +
    '<div class="field"><label for="cls">Class</label><select id="cls"></select></div>' +
    '<div class="field"><label for="diff">Difficulty</label><select id="diff"></select></div>' +
    '<div class="field"><label for="lvl">Character level</label><div class="level"><input id="lvl" type="range" min="1" max="1000" step="1">' +
    '<output id="lvlOut" for="lvl"></output></div></div>' +
    '<button class="btn" id="example" type="button">Ordinary build</button><button class="btn" id="clear" type="button">Clear</button>' +
    '<div class="points" id="points"></div>';
  stage.appendChild(top);
  var board = el('div', 'board'); stage.appendChild(board);
  var side = el('div', 'side'); stage.appendChild(side);
  var clsSel = top.querySelector('#cls'), diffSel = top.querySelector('#diff'), lvl = top.querySelector('#lvl');
  T.classes.forEach(function (c) { var o = el('option', '', c.name); o.value = c.id; clsSel.appendChild(o); });
  C.DIFFS.forEach(function (d) { var o = el('option', '', d[1]); o.value = d[0]; diffSel.appendChild(o); });
  clsSel.value = state.cls; diffSel.value = state.diff; lvl.value = state.level;
  clsSel.onchange = function () { state.cls = clsSel.value; loadExample(); render(); };
  diffSel.onchange = function () { state.diff = diffSel.value; render(); };
  lvl.oninput = function () { state.level = +lvl.value; trimmed(state); render(); };
  top.querySelector('#example').onclick = function () { loadExample(); render(); };
  top.querySelector('#clear').onclick = function () { state.ranks = {}; state.keystones = []; render(); };

  // ---- the board ---------------------------------------------------------------------------------------------------
  function nodeState(node) {
    var r = state.ranks[node.id] || 0;
    return (r > 0 ? 'has ' : '') + (r === 0 && !C.tierOpen(state.ranks, node.path, node.tier) ? 'locked ' : '') +
      (state.tip === node.id ? 'tip' : '');
  }
  function wire(e, node) {
    e.onmouseenter = function () { state.tip = node.id; state.tipKind = 'node'; renderSide(); };
    e.onclick = function () { add(node); render(); };
    e.oncontextmenu = function (ev) { ev.preventDefault(); remove(node); render(); };
  }
  function rankMark(node) {
    var r = state.ranks[node.id] || 0;
    if (node.max > 5) { return '<span class="rank">' + r + '/' + node.max + '</span>'; }
    var s = '<span class="pips">';
    for (var i = 0; i < node.max; i++) { s += '<i class="' + (i < r ? 'on' : '') + '"></i>'; }
    return s + '</span>';
  }
  function renderColumns() {
    var wrap = el('div', 'columns');
    T.paths.forEach(function (p) {
      var col = el('div', 'col');
      col.appendChild(el('h2', '', '<span style="color:' + p.color + '">' + p.name + '</span><small>' + p.sub + '</small>'));
      var total = T.nodes.filter(function (n) { return n.path === p.id; }).reduce(function (a, n) { return a + n.max; }, 0);
      col.appendChild(el('div', 'count', C.spentIn(state.ranks, p.id) + ' of ' + total + ' ranks'));
      if (p.id === 'bulwark') {
        var free = el('div', 'row free', '<span class="mark unlock" style="--pc:#3f7a52">SW</span><span class="name">Second Wind</span><span class="rank">free</span>');
        free.onmouseenter = function () { state.tip = 'second_wind'; state.tipKind = 'root'; renderSide(); };
        col.appendChild(free);
      }
      for (var t = 1; t <= 5; t++) {
        var open = C.tierOpen(state.ranks, p.id, t);
        col.appendChild(el('div', 'tier' + (open ? ' open' : ''), 'Tier ' + t + (t > 1 ? ' · ' + T.tierGates[t - 1] + ' points below' : '')));
        T.nodes.filter(function (n) { return n.path === p.id && n.tier === t; }).forEach(function (n) {
          var row = el('div', 'row ' + nodeState(n));
          row.appendChild(mark(n, p.color));
          row.appendChild(el('span', 'name', n.name));
          row.insertAdjacentHTML('beforeend', rankMark(n));
          wire(row, n);
          col.appendChild(row);
        });
      }
      wrap.appendChild(col);
    });
    board.replaceChildren(wrap);
  }
  function renderWeb() {
    var W = 940, H = 632, cx = W / 2, cy = H / 2 + 6, radii = [92, 146, 198, 250, 298];
    var web = el('div', 'web'), svg = '<svg viewBox="0 0 ' + W + ' ' + H + '" aria-hidden="true">';
    var nodesHtml = [];
    T.paths.forEach(function (p, i) {
      var mid = (-90 + i * 72) * Math.PI / 180, half = 31 * Math.PI / 180;
      svg += '<line x1="' + cx + '" y1="' + cy + '" x2="' + (cx + Math.cos(mid) * radii[4]) + '" y2="' + (cy + Math.sin(mid) * radii[4]) +
        '" stroke="' + p.color + '" stroke-opacity=".35" stroke-width="1.5" fill="none"/>';
      for (var t = 1; t <= 5; t++) {
        var list = T.nodes.filter(function (n) { return n.path === p.id && n.tier === t; });
        var r = radii[t - 1], open = C.tierOpen(state.ranks, p.id, t);
        var a0 = mid - half, a1 = mid + half;
        svg += '<path d="M' + (cx + Math.cos(a0) * r) + ' ' + (cy + Math.sin(a0) * r) + ' A' + r + ' ' + r + ' 0 0 1 ' + (cx + Math.cos(a1) * r) + ' ' +
          (cy + Math.sin(a1) * r) + '" stroke="' + p.color + '" stroke-opacity="' + (open ? .55 : .18) + '" stroke-width="1.5" fill="none"/>';
        list.forEach(function (n, k) {
          var a = list.length === 1 ? mid : a0 + (a1 - a0) * (k + 0.5) / list.length;
          nodesHtml.push([n, p, cx + Math.cos(a) * r, cy + Math.sin(a) * r]);
        });
      }
      var lr = radii[4] + 26;
      var lab = el('div', 'label', '<span style="color:' + p.color + '">' + p.name + '</span><small>' + C.spentIn(state.ranks, p.id) + ' ranks</small>');
      lab.style.left = (cx + Math.cos(mid) * lr * 1.02) + 'px'; lab.style.top = Math.min(H - 16, Math.max(14, cy + Math.sin(mid) * lr * 0.985)) + 'px';
      web.appendChild(lab);
    });
    web.insertAdjacentHTML('afterbegin', svg + '</svg>');
    nodesHtml.forEach(function (it) {
      var n = it[0], e = el('div', 'node ' + nodeState(n));
      e.style.left = it[2] + 'px'; e.style.top = it[3] + 'px';
      e.style.setProperty('--s', { small: 16, passive: 22, active: 24, notable: 26, unlock: 21 }[n.kind] + 'px');
      e.appendChild(mark(n, it[1].color));
      e.appendChild(el('small', '', (state.ranks[n.id] || 0) + '/' + n.max));
      wire(e, n);
      web.appendChild(e);
    });
    var hub = el('div', 'hub', 'Second<br>Wind');
    hub.style.left = cx + 'px'; hub.style.top = cy + 'px';
    hub.onmouseenter = function () { state.tip = 'second_wind'; state.tipKind = 'root'; renderSide(); };
    web.appendChild(hub);
    board.replaceChildren(web);
  }

  // ---- the side ----------------------------------------------------------------------------------------------------
  var KIND = { active: 'Active skill', passive: 'Passive', small: 'Small node', notable: 'Notable', unlock: 'Skill unlock' };
  function detailHtml() {
    if (state.tipKind === 'root') {
      return '<h3>' + T.root.name + '</h3><div class="kind">Innate · every solo character</div><p>' + T.root.text + '</p>';
    }
    if (state.tipKind === 'keystone' && C.keystoneById[state.tip]) {
      var k = C.keystoneById[state.tip];
      return '<h3>' + k.name + '</h3><div class="kind">Keystone · costs no points' + (k.isNew ? ' · new' : ' · in the game') + '</div><p>' + k.text +
        '</p><p class="dim">One keystone slot opens every 150 levels. Click a socket to bind the next keystone, right click to empty it.</p>';
    }
    var n = C.byId[state.tip];
    if (!n) {
      return '<h3>How to read this</h3><p>Click a row to learn a rank, right click to take it back. A tier opens with points in the tiers below it.</p>' +
        '<p class="dim">Squares with a rim are active skills, hexagons are notables, diamonds are small nodes, circles unlock a skill for any class. A green dot marks what the built tree does not have yet.</p>';
    }
    var r = state.ranks[n.id] || 0, p = C.pathOf(n.path), why = C.refusal(state, n);
    var h = '<h3>' + n.name + '</h3><div class="kind">' + KIND[n.kind] + ' · ' + p.name + ' tier ' + n.tier + ' · rank ' + r + ' of ' + n.max +
      (n.isNew ? ' · new' : ' · in the game') + '</div>';
    if (r > 0) { h += '<p>' + C.textAt(n, r) + '</p>'; }
    if (r < n.max) { h += '<p class="next">' + (r > 0 ? 'Next rank: ' : 'At rank 1: ') + C.textAt(n, r + 1) + '</p>'; }
    if (n.req) { h += '<p class="dim">Needs ' + n.req + '.</p>'; }
    if (why && r < n.max) { h += '<p class="no">' + why + '.</p>'; }
    return h;
  }
  function gaugeHtml(base, cut, tree) {
    var lo = Math.log(0.2), hi = Math.log(6);
    function x(v) { return Math.max(0, Math.min(100, (Math.log(v) - lo) / (hi - lo) * 100)); }
    var pins = [[base, 'var(--series-1)'], [base * cut, 'var(--series-2)'], [base * cut * tree, 'var(--series-3)']];
    var h = '<div class="gauge"><div class="track"></div><div class="over" style="left:' + x(1) + '%;right:0"></div>';
    [0.25, 0.5, 2, 4].forEach(function (v) { h += '<span class="tick" style="left:' + x(v) + '%">' + v + '</span>'; });
    h += '<div class="party" style="left:' + x(1) + '%"><span>a party of five</span></div>';
    pins.forEach(function (p) { h += '<span class="pin" style="left:' + x(p[0]) + '%;background:' + p[1] + '"></span>'; });
    return h + '</div>';
  }
  function renderSide() {
    var style = C.styleOf(state.cls), pw = C.power(state.ranks, state.keystones, style);
    var base = C.baseRatio(state.cls, state.diff, state.level), cut = C.cutAt(state.level), total = base * cut * pw.h;
    var f = function (v) { return '×' + v.toFixed(2); };
    var past = state.level > C.lastStageLevel(state.diff);
    var slots = C.keystoneSlots(state.level), sockets = '';
    for (var i = 0; i < 6; i++) {
      var k = C.keystoneById[state.keystones[i]];
      sockets += '<button type="button" class="socket ' + (k ? 'bound' : i < slots ? 'open' : '') + '" data-i="' + i + '" aria-label="Keystone slot ' + (i + 1) + '">' +
        (k ? k.name.split(' ').map(function (w) { return w[0]; }).join('') : i < slots ? '+' : '') + '<small>' + T.keystoneLevels[i] + '</small></button>';
    }
    side.innerHTML =
      '<div class="card">' + detailHtml() + '</div>' +
      '<div class="card"><h3>What this build does</h3><dl class="stats">' +
      '<dt>Damage (hits, speed, area)</dt><dd>' + f(pw.D) + '</dd><dt>Toughness (HP, cuts, sustain)</dt><dd>' + f(pw.E) + '</dd>' +
      '<dt>Strength in monster terms</dt><dd style="color:var(--brass)">' + f(pw.h) + '</dd></dl>' +
      '<p class="dim" style="margin-top:4px">Estimates: the build can face monsters with ' + f(pw.h).slice(1) + ' times the HP and damage.</p></div>' +
      '<div class="card"><h3>Against a party of five</h3>' + gaugeHtml(base, cut, pw.h) + '<div class="legend">' +
      '<span><i style="background:var(--series-1)"></i>MAW alone, no solo rules<b>' + base.toFixed(2) + '</b></span>' +
      '<span><i style="background:var(--series-2)"></i>with the early monster cut (÷' + cut.toFixed(2) + ')<b>' + (base * cut).toFixed(2) + '</b></span>' +
      '<span><i style="background:var(--series-3)"></i>with these talents<b style="color:' + (total > 1.05 ? 'var(--bad)' : 'var(--good)') + '">' + total.toFixed(2) + '</b></span></div>' +
      '<p class="dim" style="margin-top:4px">' + (total > 1.05 ? 'Ahead of a party. To hold the line, a solo’s monsters here would be ×' + total.toFixed(2) + '.' :
        'At or under the party line.') + (past ? ' Past the simulated run: the last measured stage is used.' : '') + '</p></div>' +
      '<div class="card"><h3>Keystones <span class="dim" style="font-family:Lucida,sans-serif;font-size:10.5px">' + slots + ' of 6 slots open</span></h3>' +
      '<div class="sockets">' + sockets + '</div><p class="knote">' +
      state.keystones.map(function (id) { return C.keystoneById[id].name; }).join(', ') + '</p></div>';
    side.querySelectorAll('.socket').forEach(function (b) {
      var i = +b.dataset.i;
      b.onmouseenter = function () { if (state.keystones[i]) { state.tip = state.keystones[i]; state.tipKind = 'keystone'; renderSide(); } };
      b.onclick = function () {
        if (i >= slots) { return; }
        var free = T.keystones.filter(function (k) { return state.keystones.indexOf(k.id) < 0; });
        if (state.keystones.length <= i) { if (free.length) { state.keystones.push(free[0].id); } }
        else { // cycle the socket through the keystones not bound elsewhere
          var all = T.keystones.map(function (k) { return k.id; }), at = all.indexOf(state.keystones[i]);
          for (var s = 1; s <= all.length; s++) {
            var cand = all[(at + s) % all.length];
            if (state.keystones.indexOf(cand) < 0) { state.keystones[i] = cand; break; }
          }
        }
        state.tip = state.keystones[Math.min(i, state.keystones.length - 1)]; state.tipKind = 'keystone';
        render();
      };
      b.oncontextmenu = function (ev) { ev.preventDefault(); if (state.keystones[i]) { state.keystones.splice(i, 1); render(); } };
    });
  }
  function render() {
    top.querySelector('#lvlOut').textContent = state.level;
    var pts = T.points(state.level), used = C.spent(state.ranks);
    top.querySelector('#points').innerHTML = 'Points spent <b>' + used + '</b> of <b>' + pts + '</b><br><span style="color:var(--muted)">' +
      (state.level < 20 ? 'one every 2 levels up to 20' : 'one every 5 levels; next at level ' + (Math.floor(state.level / 5) * 5 + 5)) + '</span>';
    if (window.LAYOUT === 'web') { renderWeb(); } else { renderColumns(); }
    renderSide();
  }
  fit(); render();
})();
