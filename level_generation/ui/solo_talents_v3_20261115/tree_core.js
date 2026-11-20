// Solo talent tree v3 mockups: the rules and the build model, without any page. Needs tree_data.js and
// party_line_data.js. Everything here is a design draft.
(function () {
  var T = window.TALENT_TREE, PL = window.PARTY_LINE;
  var byId = {};
  T.nodes.forEach(function (n) { byId[n.id] = n; });
  var keystoneById = {};
  T.keystones.forEach(function (k) { keystoneById[k.id] = k; });
  var existingIcons = ['attunement', 'binding_circle', 'blink', 'bloodthirst', 'charge', 'cheat_death', 'cleave', 'marksman',
    'multishot', 'onslaught', 'overload', 'piercing_arrows', 'pinning_shot', 'quickfoot', 'resolve', 'shield_wall',
    'spell_surge', 'steady_aim', 'sweeping_blows', 'unbroken', 'weapon_training'];

  function spent(ranks) { var s = 0; for (var id in ranks) { s += ranks[id]; } return s; }
  function spentIn(ranks, path) {
    var s = 0;
    for (var id in ranks) { if (byId[id] && byId[id].path === path) { s += ranks[id]; } }
    return s;
  }
  // Points in the tiers of a path below `tier`: what opens that tier.
  function belowTier(ranks, path, tier) {
    var s = 0;
    for (var id in ranks) { if (byId[id] && byId[id].path === path && byId[id].tier < tier) { s += ranks[id]; } }
    return s;
  }
  function tierOpen(ranks, path, tier) { return belowTier(ranks, path, tier) >= T.tierGates[tier - 1]; }
  function keystoneSlots(level) { return T.keystoneLevels.filter(function (l) { return level >= l; }).length; }

  // Why a rank cannot be added now ('' when it can). Class and mastery requirements are shown, not enforced.
  function refusal(state, node) {
    var r = state.ranks[node.id] || 0;
    if (r >= node.max) { return 'At its last rank'; }
    if (spent(state.ranks) >= T.points(state.level)) { return 'No points left at level ' + state.level; }
    if (!tierOpen(state.ranks, node.path, node.tier)) {
      return 'Tier ' + node.tier + ' opens with ' + T.tierGates[node.tier - 1] + ' points in the lower tiers of ' +
        pathOf(node.path).name + ' (you have ' + belowTier(state.ranks, node.path, node.tier) + ')';
    }
    if (node.needs && !(state.ranks[node.needs] > 0)) { return 'Needs a rank of ' + byId[node.needs].name; }
    return '';
  }
  function pathOf(id) { return T.paths.filter(function (p) { return p.id === id; })[0]; }

  // Taking a rank away must leave every other rank legal: for every tier that holds ranks, the points in the tiers
  // below it still reach its gate, and every `needs` is still met.
  function canRemove(state, node) {
    var r = state.ranks[node.id] || 0;
    if (r <= 0) { return false; }
    var after = Object.assign({}, state.ranks);
    after[node.id] = r - 1;
    for (var id in after) {
      var n = byId[id];
      if (!(after[id] > 0)) { continue; }
      var below = 0;
      for (var other in after) {
        if (byId[other].path === n.path && byId[other].tier < n.tier) { below += after[other]; }
      }
      if (below < T.tierGates[n.tier - 1]) { return false; }
      if (n.needs && !(after[n.needs] > 0)) { return false; }
    }
    return true;
  }

  function valueAt(node, rank) {
    if (rank <= 0) { return null; }
    if (node.vals) { return node.vals[Math.min(rank, node.vals.length) - 1]; }
    var v = node.per * rank;
    return Math.round(v * 10) / 10;
  }
  function textAt(node, rank) { return node.text.replace('{v}', valueAt(node, Math.max(rank, 1))); }

  // An ordinary build of the class with `points` points: the plan in order, then small nodes round and round.
  function exampleBuild(classId, level) {
    var cls = T.classes.filter(function (c) { return c.id === classId; })[0] || T.classes[0];
    var state = { level: level, ranks: {} };
    var plan = T.plans[cls.plan];
    var progressed = true;
    function tryAdd(id, target) {
      var node = byId[id], did = false;
      while ((state.ranks[id] || 0) < Math.min(target, node.max) && refusal(state, node) === '') {
        state.ranks[id] = (state.ranks[id] || 0) + 1; did = true;
      }
      return did;
    }
    // Follow the plan step by step; a step that is not open yet waits while cheap small nodes open its tier.
    var mainPath = cls.plan === 'dragon' ? 'bulwark' : cls.plan.replace('_shield', '');
    var fillers = T.nodes.filter(function (n) {
      return n.kind === 'small' && (n.path === mainPath || n.path === 'bulwark') && Object.keys(n.e).length > 0;
    });
    for (var i = 0; i < plan.length && spent(state.ranks) < T.points(level); i++) {
      var node = byId[plan[i][0]], guard = 0;
      while ((state.ranks[node.id] || 0) < plan[i][1] && spent(state.ranks) < T.points(level) && guard++ < 400) {
        if (refusal(state, node) === '') { state.ranks[node.id] = (state.ranks[node.id] || 0) + 1; continue; }
        // Closed tier: put a point in the path's lowest small node that still takes one.
        var opener = T.nodes.filter(function (n) {
          return n.path === node.path && n.tier < node.tier && (n.kind === 'small' || n.kind === 'passive') &&
            refusal(state, n) === '';
        }).sort(function (a, b) { return (state.ranks[a.id] || 0) / a.max - (state.ranks[b.id] || 0) / b.max; })[0];
        if (node.needs && !(state.ranks[node.needs] > 0) && refusal(state, byId[node.needs]) === '') { opener = byId[node.needs]; }
        if (!opener) { break; }
        state.ranks[opener.id] = (state.ranks[opener.id] || 0) + 1;
      }
    }
    // Then the small nodes of the build's path and of Bulwark, evenly; then whatever else helps, nearest path first.
    var rest = T.nodes.filter(function (n) { return fillers.indexOf(n) < 0 && Object.keys(n.e).length > 0; })
      .sort(function (a, b) {
        function near(n) { return n.path === mainPath ? 0 : n.path === 'bulwark' ? 1 : n.path === 'lore' ? 2 : 3; }
        return near(a) - near(b) || a.tier - b.tier;
      });
    while (progressed && spent(state.ranks) < T.points(level)) {
      progressed = false;
      fillers.sort(function (a, b) { return (state.ranks[a.id] || 0) / a.max - (state.ranks[b.id] || 0) / b.max; });
      for (var f = 0; f < fillers.length && !progressed; f++) {
        progressed = tryAdd(fillers[f].id, (state.ranks[fillers[f].id] || 0) + 1);
      }
      for (var g = 0; g < rest.length && !progressed; g++) {
        // Nothing of another weapon's path: a bow talent does nothing for a swordsman.
        if (rest[g].path !== mainPath && rest[g].path !== 'bulwark' && rest[g].path !== 'lore' && !rest[g].e.hp) { continue; }
        progressed = tryAdd(rest[g].id, (state.ranks[rest[g].id] || 0) + 1);
      }
    }
    var keystones = ['unbroken', 'cheat_death', 'blood_pact', 'juggernaut', 'duelist', 'wayfarer'].slice(0, keystoneSlots(level));
    return { ranks: state.ranks, keystones: keystones };
  }

  // The build model: damage and toughness multipliers of a build for an attack style ('m', 'b' or 's'), and its
  // strength in the simulation's unit (monster HP and damage both scaled): the root of damage times toughness.
  function power(ranks, keystones, style) {
    var dmgKey = { m: 'dm', b: 'db', s: 'ds' }[style], spdKey = { m: 'asm', b: 'asb', s: 'ass' }[style];
    var aoeKey = { m: 'am', b: 'ab', s: 'as_' }[style];
    var out = { damage: 1, speed: 1, area: 1, hp: 1, taken: 1, other: 1, sustain: 1 };
    function apply(e, r) {
      if (e[dmgKey]) { out.damage *= 1 + e[dmgKey] * r; }
      if (e[spdKey]) { out.speed *= 1 + e[spdKey] * r; }
      if (e[aoeKey]) { out.area *= 1 + e[aoeKey] * r; }
      if (e.hp) { out.hp *= 1 + e.hp * r; }
      if (e.tk) { out.taken *= 1 - e.tk * r; }
      if (e.eh) { out.other *= 1 + e.eh * r; }
      if (e.su) { out.sustain *= 1 + e.su * r; }
    }
    for (var id in ranks) { if (ranks[id] > 0) { apply(byId[id].e, ranks[id]); } }
    (keystones || []).forEach(function (k) { if (keystoneById[k]) { apply(keystoneById[k].e, 1); } });
    out.taken = Math.max(out.taken, 0.5);
    out.D = out.damage * out.speed * out.area;
    out.E = out.hp / out.taken * out.other * out.sustain;
    out.h = Math.sqrt(out.D * out.E);
    return out;
  }

  function lerpTable(table, x) {
    if (x <= table[0][0]) { return table[0][1]; }
    for (var i = 1; i < table.length; i++) {
      if (x <= table[i][0]) {
        var a = table[i - 1], b = table[i];
        return a[1] + (b[1] - a[1]) * (x - a[0]) / (b[0] - a[0]);
      }
    }
    return table[table.length - 1][1];
  }
  function cutAt(level) { return lerpTable(T.earlyCut, level); }

  // The solo's strength against the party of five at a level (plain MAW, no solo rule), from the simulation's stages:
  // interpolated in the logarithm of both; flat beyond the last stage.
  function baseRatio(classId, diff, level) {
    var rows = PL[diff] || PL.nightmare;
    var table = rows.map(function (r) {
      var v = classId === 'typical' ? r.typical : (r.b[classId] !== undefined ? r.b[classId] : r.typical);
      return [Math.log(r.level), Math.log(v)];
    });
    return Math.exp(lerpTable(table, Math.log(Math.max(level, 1))));
  }
  function lastStageLevel(diff) { var rows = PL[diff] || PL.nightmare; return rows[rows.length - 1].level; }

  window.TreeCore = {
    T: T, byId: byId, keystoneById: keystoneById, hasIcon: function (id) { return existingIcons.indexOf(id) >= 0; },
    spent: spent, spentIn: spentIn, belowTier: belowTier, tierOpen: tierOpen, keystoneSlots: keystoneSlots, refusal: refusal,
    canRemove: canRemove, valueAt: valueAt, textAt: textAt, exampleBuild: exampleBuild, power: power, cutAt: cutAt,
    baseRatio: baseRatio, lastStageLevel: lastStageLevel, pathOf: pathOf,
    styleOf: function (classId) { var c = T.classes.filter(function (x) { return x.id === classId; })[0]; return c ? c.style : 'm'; },
    DIFFS: [['maw', 'MAW'], ['nightmare', 'Nightmare'], ['doom', 'Doom'], ['insanity', 'Road to Insanity'], ['madness', 'Beyond Madness']]
  };
})();
