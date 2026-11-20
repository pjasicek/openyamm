// Solo talent tree v3: the design draft the mockups show (2026-11-15). Nothing here is in the game.
//
// A node: id, name, path, tier (1-5), kind, max (ranks), isNew (not in the built tree), req (what else it needs),
// needs (another node with a rank), vals (the number per rank, {v} in text), text, and e: its estimated effect per
// rank on the build model of tree_core.js. Effects are fractions per rank:
//   dm db ds   damage of melee, bow, spell attacks        asm asb ass  attack or cast speed
//   am ab as_  clear speed against a group (area hits)     hp           maximum HP
//   tk         damage taken, cut after MAW's 10 % floor    eh           other toughness (wards, dodge, block)
//   su         sustain, counted as toughness               (none)       utility: no combat power
// The effect numbers of actives, sustain and area hits are cautious estimates of what they add over a fight, not
// measured; the solo simulation has to replace them before any value is settled.
window.TALENT_TREE = {
  // One point every 2 levels up to level 20, then one every 5.
  points: function (level) { return level <= 20 ? Math.floor(level / 2) : 10 + Math.floor((level - 20) / 5); },
  keystoneLevels: [150, 300, 450, 600, 750, 900],
  // Points in the lower tiers of a path that open its tiers 1 to 5.
  tierGates: [0, 5, 15, 30, 45],
  // The solo run's early monster cut: [character level, divisor of monster HP and damage], linear between. Sized so
  // that the cut times an ordinary build's talents keeps a typical solo at or under the party on MAW and Nightmare
  // (party_line_data.js): 2.5 at the start as the user set it, gone by level 75.
  earlyCut: [[1, 2.5], [5, 2.5], [10, 2.0], [20, 1.7], [30, 1.55], [50, 1.3], [75, 1.0]],
  paths: [
    { id: 'arms', name: 'Arms', sub: 'melee weapons', color: '#c9643c' },
    { id: 'archery', name: 'Archery', sub: 'bows only', color: '#7fa84a' },
    { id: 'arcana', name: 'Arcana', sub: 'magic schools', color: '#5b8fd6' },
    { id: 'bulwark', name: 'Bulwark', sub: 'any class: staying alive', color: '#b9a06a' },
    { id: 'lore', name: 'Lore', sub: 'any class: skills and tricks', color: '#a77fc4' }
  ],
  root: { id: 'second_wind', name: 'Second Wind', text: 'Free at level 1. Out of combat (no monster alerted for 5 s) you regain 4 % of HP and SP a second; in combat 0.3 %. It replaces the potion spam between fights.' },
  nodes: [
    // ---- Arms ----------------------------------------------------------------------------------------------------
    { id: 'weapon_training', name: 'Weapon Training', path: 'arms', tier: 1, kind: 'passive', max: 5, vals: [2, 4, 6, 8, 10], text: '+{v} % Might, Endurance and Speed', e: { dm: 0.012, hp: 0.004, asm: 0.004 } },
    { id: 'cleave', name: 'Cleave', path: 'arms', tier: 1, kind: 'active', max: 3, req: 'Expert in a melee weapon', vals: [12, 9, 6], text: 'A burst: every monster in the 120° arc in front takes a blow at 150 %; cooldown {v} s', e: { am: 0.03 } },
    { id: 'honed_edge', name: 'Honed Edge', path: 'arms', tier: 1, kind: 'small', max: 15, isNew: true, per: 1, text: '+{v} % melee damage', e: { dm: 0.01 } },
    { id: 'sweeping_blows', name: 'Sweeping Blows', path: 'arms', tier: 2, kind: 'passive', max: 3, needs: 'cleave', vals: [1, 2, 3], text: 'Every swing also strikes {v} more in the arc at 30–50 %', e: { am: 0.048 } },
    { id: 'onslaught', name: 'Onslaught', path: 'arms', tier: 2, kind: 'passive', max: 3, vals: [10, 20, 30], text: 'Each kill: +1 % attack speed, at most {v} stacks for 30 s', e: { asm: 0.02 } },
    { id: 'charge', name: 'Charge', path: 'arms', tier: 2, kind: 'active', max: 3, req: 'Expert in a melee weapon', vals: [18, 15, 12], text: 'Dash to the target, strike and stagger it 1.5 s; cooldown {v} s, 1 s less per attack', e: { dm: 0.01 } },
    { id: 'shield_wall', name: 'Shield Wall', path: 'arms', tier: 2, kind: 'active', max: 3, req: 'a shield', vals: [30, 25, 20], text: 'With a shield: 50 % less damage for 6 s; cooldown {v} s', e: { eh: 0.015 } },
    { id: 'brawn', name: 'Brawn', path: 'arms', tier: 2, kind: 'small', max: 15, isNew: true, per: 1, text: '+{v} % maximum HP', e: { hp: 0.01 } },
    { id: 'ground_slam', name: 'Ground Slam', path: 'arms', tier: 3, kind: 'active', max: 3, isNew: true, req: 'Master in a melee weapon', vals: [80, 100, 120], text: 'Every monster within 4 m takes a blow at {v} % and staggers for 1 s; cooldown 18 s', e: { am: 0.024 } },
    { id: 'war_cry', name: 'War Cry', path: 'arms', tier: 3, kind: 'active', max: 3, isNew: true, vals: [10, 15, 20], text: 'For 12 s: +{v} % melee damage and attack speed; cooldown 45 s', e: { dm: 0.02, asm: 0.01 } },
    { id: 'executioner', name: 'Executioner', path: 'arms', tier: 3, kind: 'notable', max: 3, isNew: true, vals: [10, 20, 30], text: '+{v} % damage to monsters under 30 % HP', e: { dm: 0.025 } },
    { id: 'fighting_style', name: 'Fighting Style', path: 'arms', tier: 3, kind: 'notable', max: 3, isNew: true, vals: [1, 2, 3], text: 'By what you hold, per rank: two-handed +5 % damage; two weapons +4 % attack speed; a shield 3 % less damage taken (rank {v})', e: { dm: 0.04 } },
    { id: 'rend', name: 'Rend', path: 'arms', tier: 4, kind: 'active', max: 3, isNew: true, vals: [60, 80, 100], text: 'A blow that bleeds the target for {v} % weapon damage over 6 s; cooldown 8 s', e: { dm: 0.02 } },
    { id: 'momentum', name: 'Momentum', path: 'arms', tier: 4, kind: 'small', max: 15, isNew: true, per: 0.7, text: '+{v} % attack speed', e: { asm: 0.007 } },
    { id: 'bloodlust', name: 'Bloodlust', path: 'arms', tier: 4, kind: 'notable', max: 3, isNew: true, vals: [2, 3, 4], text: 'Each kill restores {v} % of maximum HP', e: { su: 0.02 } },
    { id: 'bladestorm', name: 'Bladestorm', path: 'arms', tier: 5, kind: 'active', max: 3, isNew: true, req: 'Grandmaster in a melee weapon', vals: [60, 70, 80], text: 'Spin for 3 s while moving: four blows at {v} % on everything in reach; cooldown 40 s', e: { am: 0.03 } },
    { id: 'unstoppable', name: 'Unstoppable', path: 'arms', tier: 5, kind: 'notable', max: 3, isNew: true, vals: [20, 40, 60], text: 'Staggers, slows and holds on you last {v} % shorter', e: { eh: 0.01 } },
    // ---- Archery -------------------------------------------------------------------------------------------------
    { id: 'marksman', name: 'Marksman', path: 'archery', tier: 1, kind: 'passive', max: 5, vals: [2, 4, 6, 8, 10], text: '+{v} % Accuracy and Speed', e: { db: 0.012, asb: 0.004 } },
    { id: 'multishot', name: 'Multishot', path: 'archery', tier: 1, kind: 'active', max: 3, req: 'Expert Bow', vals: [2, 3, 4], text: 'One shot of {v} arrows fanned over ±12°, 75 % each; cooldown 10, 8 or 6 s', e: { ab: 0.036 } },
    { id: 'fletcher', name: 'Fletcher', path: 'archery', tier: 1, kind: 'small', max: 15, isNew: true, per: 1, text: '+{v} % bow damage', e: { db: 0.01 } },
    { id: 'piercing_arrows', name: 'Piercing Arrows', path: 'archery', tier: 2, kind: 'passive', max: 3, vals: [1, 2, 3], text: 'Every arrow flies on through {v} more monsters at 30–50 %', e: { ab: 0.042 } },
    { id: 'pinning_shot', name: 'Pinning Shot', path: 'archery', tier: 2, kind: 'active', max: 3, req: 'Expert Bow', vals: [3, 4, 5], text: 'A shot that slows the target by half for {v} s', e: { eh: 0.01 } },
    { id: 'steady_aim', name: 'Steady Aim', path: 'archery', tier: 2, kind: 'passive', max: 3, vals: [5, 10, 15], text: 'After standing still for 1 s: +{v} % Luck (critical chance)', e: { db: 0.02 } },
    { id: 'quickfoot', name: 'Quickfoot', path: 'archery', tier: 2, kind: 'passive', max: 3, vals: [3, 6, 9], text: '+{v} % movement speed (five times as much out of combat)', e: {} },
    { id: 'hardy', name: 'Hardy', path: 'archery', tier: 2, kind: 'small', max: 15, isNew: true, per: 1, text: '+{v} % maximum HP', e: { hp: 0.01 } },
    { id: 'rain_of_arrows', name: 'Rain of Arrows', path: 'archery', tier: 3, kind: 'active', max: 3, isNew: true, req: 'Master Bow', vals: [30, 40, 50], text: 'A 5 m circle for 4 s: {v} % of a shot twice a second on everything in it; cooldown 25 s', e: { ab: 0.03 } },
    { id: 'hunters_mark', name: "Hunter's Mark", path: 'archery', tier: 3, kind: 'active', max: 3, isNew: true, vals: [10, 15, 20], text: 'The marked monster takes +{v} % from you for 15 s; a kill moves the mark; cooldown 20 s', e: { db: 0.03 } },
    { id: 'first_blood', name: 'First Blood', path: 'archery', tier: 3, kind: 'notable', max: 3, isNew: true, vals: [20, 40, 60], text: 'Shots at a monster on full HP: +{v} % damage', e: { db: 0.025 } },
    { id: 'skirmisher', name: 'Skirmisher', path: 'archery', tier: 3, kind: 'notable', max: 3, isNew: true, vals: [5, 10, 15], text: '+{v} % bow damage for 2 s after you move (the opposite habit to Steady Aim)', e: { db: 0.02 } },
    { id: 'leap_back', name: 'Leap Back', path: 'archery', tier: 4, kind: 'active', max: 3, isNew: true, vals: [120, 150, 180], text: 'Jump 6 m back and loose a shot at {v} %; cooldown 12 s', e: { db: 0.01, eh: 0.01 } },
    { id: 'rapid_fire', name: 'Rapid Fire', path: 'archery', tier: 4, kind: 'small', max: 15, isNew: true, per: 0.7, text: '+{v} % bow attack speed', e: { asb: 0.007 } },
    { id: 'trophy_hunter', name: 'Trophy Hunter', path: 'archery', tier: 4, kind: 'notable', max: 3, isNew: true, vals: [2, 3, 4], text: 'Each kill restores {v} % of maximum HP', e: { su: 0.02 } },
    { id: 'barrage', name: 'Barrage', path: 'archery', tier: 5, kind: 'active', max: 3, isNew: true, req: 'Grandmaster Bow', vals: [6, 8, 10], text: '{v} shots in 2 s at one target, 50 % each; cooldown 40 s', e: { db: 0.03 } },
    { id: 'eagle_eye', name: 'Eagle Eye', path: 'archery', tier: 5, kind: 'notable', max: 3, isNew: true, vals: [10, 20, 30], text: 'Arrows ignore {v} % of the target’s physical resistance', e: { db: 0.03 } },
    // ---- Arcana --------------------------------------------------------------------------------------------------
    { id: 'attunement', name: 'Attunement', path: 'arcana', tier: 1, kind: 'passive', max: 5, vals: [2, 4, 6, 8, 10], text: '+{v} % Intellect, Personality, Endurance, spell damage and healing', e: { ds: 0.02, hp: 0.004 } },
    { id: 'blink', name: 'Blink', path: 'arcana', tier: 1, kind: 'active', max: 3, req: 'Expert in a magic school', vals: [20, 16, 12], text: 'Teleport 15 m forward; cooldown {v} s', e: { eh: 0.02 } },
    { id: 'channeling', name: 'Channeling', path: 'arcana', tier: 1, kind: 'small', max: 15, isNew: true, per: 1, text: '+{v} % spell damage and healing', e: { ds: 0.01 } },
    { id: 'overload', name: 'Overload', path: 'arcana', tier: 2, kind: 'passive', max: 3, vals: [10, 20, 30], text: 'Area spells: +{v} % damage per monster near the target beyond the first (at most 3 more)', e: { as_: 0.048 } },
    { id: 'binding_circle', name: 'Binding Circle', path: 'arcana', tier: 2, kind: 'active', max: 3, req: 'Expert in a magic school', vals: [2, 2.5, 3], text: 'Every hostile within 5 m is held almost still for {v} s; cooldown 20, 18 or 16 s', e: { eh: 0.02 } },
    { id: 'resolve', name: 'Resolve', path: 'arcana', tier: 2, kind: 'passive', max: 5, vals: [2, 4, 6, 8, 10], text: '+{v} % to all resistances', e: { eh: 0.0025 } },
    { id: 'spell_surge', name: 'Spell Surge', path: 'arcana', tier: 2, kind: 'active', max: 3, req: 'Master in a magic school', vals: [45, 35, 25], text: 'The next spell costs no SP and hits 50 % harder; cooldown {v} s', e: { ds: 0.02 } },
    { id: 'wellspring', name: 'Wellspring', path: 'arcana', tier: 2, kind: 'small', max: 15, isNew: true, per: 1.5, text: '+{v} % maximum SP', e: { ds: 0.003, eh: 0.002 } },
    { id: 'arcane_ward', name: 'Arcane Ward', path: 'arcana', tier: 3, kind: 'active', max: 3, isNew: true, vals: [15, 20, 25], text: 'A ward absorbs damage up to {v} % of maximum HP for 10 s; cooldown 40 s', e: { eh: 0.02 } },
    { id: 'echo', name: 'Echo', path: 'arcana', tier: 3, kind: 'notable', max: 3, isNew: true, vals: [10, 20, 30], text: '{v} % chance that a damaging spell repeats at half strength for free', e: { ds: 0.05 } },
    { id: 'focus', name: 'Focus', path: 'arcana', tier: 3, kind: 'notable', max: 3, isNew: true, vals: [5, 10, 15], text: 'Spells cost {v} % less SP', e: { ds: 0.01 } },
    { id: 'mana_tide', name: 'Mana Tide', path: 'arcana', tier: 4, kind: 'active', max: 3, isNew: true, vals: [20, 30, 40], text: 'For 8 s spells cost half and recover {v} % faster; cooldown 60 s', e: { ass: 0.015 } },
    { id: 'quickening', name: 'Quickening', path: 'arcana', tier: 4, kind: 'small', max: 15, isNew: true, per: 0.7, text: 'Spells recover {v} % faster', e: { ass: 0.007 } },
    { id: 'siphon', name: 'Siphon', path: 'arcana', tier: 4, kind: 'notable', max: 3, isNew: true, vals: [2, 3, 4], text: 'Each kill restores {v} % of maximum HP and SP', e: { su: 0.02 } },
    { id: 'stasis', name: 'Stasis', path: 'arcana', tier: 5, kind: 'active', max: 3, isNew: true, req: 'Grandmaster in a magic school', vals: [2, 3, 4], text: 'Every monster within 10 m is frozen for {v} s (bosses are slowed); cooldown 90 s', e: { eh: 0.015 } },
    { id: 'elemental_mastery', name: 'Elemental Mastery', path: 'arcana', tier: 5, kind: 'notable', max: 3, isNew: true, vals: [10, 20, 30], text: 'Spells ignore {v} % of the target’s resistance', e: { ds: 0.03 } },
    // ---- Bulwark -------------------------------------------------------------------------------------------------
    { id: 'vigor', name: 'Vigor', path: 'bulwark', tier: 1, kind: 'small', max: 20, isNew: true, per: 1, text: '+{v} % maximum HP', e: { hp: 0.01 } },
    { id: 'bloodthirst', name: 'Bloodthirst', path: 'bulwark', tier: 1, kind: 'passive', max: 3, vals: [2, 4, 6], text: '+{v} % leech on melee, bow and spells; the leech floor grows', e: { su: 0.015 } },
    { id: 'thick_skin', name: 'Thick Skin', path: 'bulwark', tier: 2, kind: 'small', max: 10, isNew: true, per: 1, text: '{v} % less damage taken, after MAW’s 10 % floor', e: { tk: 0.01 } },
    { id: 'recuperate', name: 'Recuperate', path: 'bulwark', tier: 2, kind: 'active', max: 3, isNew: true, vals: [20, 25, 30], text: 'Heal {v} % of maximum HP over 6 s; cooldown 60 s', e: { su: 0.02 } },
    { id: 'iron_will', name: 'Iron Will', path: 'bulwark', tier: 2, kind: 'notable', max: 3, isNew: true, vals: [25, 50, 75], text: 'Paralysis, stone, sleep and fear on you last {v} % shorter', e: {} },
    { id: 'deflect', name: 'Deflect', path: 'bulwark', tier: 3, kind: 'active', max: 3, isNew: true, vals: [3, 4, 5], text: 'For {v} s every missile aimed at you misses: the answer to homing shots; cooldown 30 s', e: { eh: 0.015 } },
    { id: 'last_stand', name: 'Last Stand', path: 'bulwark', tier: 3, kind: 'notable', max: 3, isNew: true, vals: [10, 20, 30], text: 'Under 30 % HP you take {v} % less damage', e: { eh: 0.015 } },
    { id: 'evasion', name: 'Evasion', path: 'bulwark', tier: 3, kind: 'small', max: 10, isNew: true, per: 0.5, text: '{v} % chance to avoid any hit', e: { eh: 0.0025 } },
    { id: 'spell_ward', name: 'Spell Ward', path: 'bulwark', tier: 4, kind: 'notable', max: 3, isNew: true, vals: [4, 8, 12], text: '{v} % less magic damage taken, after the floor', e: { tk: 0.025 } },
    { id: 'fortitude', name: 'Fortitude', path: 'bulwark', tier: 4, kind: 'small', max: 10, isNew: true, per: 2, text: 'Potions and heals restore {v} % more on you', e: { su: 0.004 } },
    { id: 'stone_form', name: 'Stone Form', path: 'bulwark', tier: 5, kind: 'active', max: 3, isNew: true, vals: [60, 70, 80], text: 'For 4 s you take {v} % less damage and cannot attack; cooldown 90 s', e: { eh: 0.015 } },
    { id: 'second_skin', name: 'Second Skin', path: 'bulwark', tier: 5, kind: 'notable', max: 3, isNew: true, vals: [20, 40, 60], text: 'Second Wind works in combat at {v} % of its resting rate', e: { su: 0.03 } },
    // ---- Lore ----------------------------------------------------------------------------------------------------
    { id: 'bow_training', name: 'Bow Training', path: 'lore', tier: 1, kind: 'unlock', max: 3, isNew: true, vals: ['Expert', 'Master', 'Grandmaster'], text: 'Any class can train Bow to {v} (a class with a higher cap keeps it)', e: {} },
    { id: 'pathfinder', name: 'Pathfinder', path: 'lore', tier: 1, kind: 'small', max: 5, isNew: true, per: 4, text: '+{v} % movement speed out of combat', e: {} },
    { id: 'scavenger', name: 'Scavenger', path: 'lore', tier: 1, kind: 'small', max: 10, isNew: true, per: 2, text: '+{v} % gold and crafting materials found', e: {} },
    { id: 'dodging_training', name: 'Dodging Training', path: 'lore', tier: 2, kind: 'unlock', max: 3, isNew: true, vals: ['Expert', 'Master', 'Grandmaster'], text: 'Any class can train Dodging to {v}', e: { eh: 0.015 } },
    { id: 'armsmaster_training', name: 'Armsmaster Training', path: 'lore', tier: 2, kind: 'unlock', max: 3, isNew: true, vals: ['Expert', 'Master', 'Grandmaster'], text: 'Any class can train Armsmaster to {v}', e: { dm: 0.03 } },
    { id: 'lure', name: 'Lure', path: 'lore', tier: 2, kind: 'active', max: 3, isNew: true, vals: [20, 25, 30], text: 'Throw a stone: one monster within {v} m comes alone, its group stays; cooldown 15 s', e: { eh: 0.015 } },
    { id: 'meditation_training', name: 'Meditation Training', path: 'lore', tier: 3, kind: 'unlock', max: 3, isNew: true, vals: ['Expert', 'Master', 'Grandmaster'], text: 'Any class can train Meditation to {v}', e: { ds: 0.02 } },
    { id: 'shield_training', name: 'Shield Training', path: 'lore', tier: 3, kind: 'unlock', max: 3, isNew: true, vals: ['Expert', 'Master', 'Grandmaster'], text: 'Any class can train Shield to {v}', e: { eh: 0.015 } },
    { id: 'hedge_magic', name: 'Hedge Magic', path: 'lore', tier: 3, kind: 'unlock', max: 3, isNew: true, vals: ['Normal', 'Expert', 'Master'], text: 'Any class can train one of Body, Spirit or Mind magic to {v} (heals and blessings of your own)', e: { su: 0.015 } },
    { id: 'prodigy', name: 'Prodigy', path: 'lore', tier: 3, kind: 'small', max: 10, isNew: true, per: 3, text: '+{v} % skill points from every level, also for levels already gained', e: { dm: 0.004, ds: 0.004, db: 0.004, hp: 0.004 } },
    { id: 'smoke_bomb', name: 'Smoke Bomb', path: 'lore', tier: 4, kind: 'active', max: 3, isNew: true, vals: [3, 4, 5], text: 'Monsters within 8 m lose you for {v} s; cooldown 45 s', e: { eh: 0.015 } },
    { id: 'quartermaster', name: 'Quartermaster', path: 'lore', tier: 4, kind: 'notable', max: 3, isNew: true, vals: [10, 20, 30], text: 'Potions you drink are {v} % stronger and last as much longer', e: { su: 0.01, dm: 0.01, ds: 0.01, db: 0.01 } },
    { id: 'mastermind', name: 'Mastermind', path: 'lore', tier: 5, kind: 'notable', max: 3, isNew: true, vals: [1, 2, 3], text: '+{v} to every skill you have', e: { dm: 0.015, ds: 0.015, db: 0.015, hp: 0.01 } }
  ],
  // Keystones cost no points: one slot per 150 levels. Each one bends the build; none is free power.
  keystones: [
    { id: 'cheat_death', name: 'Cheat Death', text: 'A hit that would kill you leaves 5 % HP, then 2 s of 95 % less damage; 3 minutes cooldown', e: { eh: 0.04 } },
    { id: 'unbroken', name: 'Unbroken', text: 'The part of one hit above 30 % of your maximum HP is halved', e: { eh: 0.04 } },
    { id: 'glass_cannon', name: 'Glass Cannon', isNew: true, text: '+25 % damage dealt; +15 % damage taken', e: { dm: 0.25, db: 0.25, ds: 0.25, tk: -0.15 } },
    { id: 'juggernaut', name: 'Juggernaut', isNew: true, text: '+25 % maximum HP; −10 % damage dealt', e: { hp: 0.25, dm: -0.1, db: -0.1, ds: -0.1 } },
    { id: 'blood_pact', name: 'Blood Pact', isNew: true, text: 'Your leech is doubled; potions heal you half as much', e: { su: 0.025 } },
    { id: 'duelist', name: 'Duelist', isNew: true, text: '+20 % damage to a monster that fights you alone; −10 % while four or more are near', e: {} },
    { id: 'spellblade', name: 'Spellblade', isNew: true, text: 'Weapon hits restore 1 % of maximum SP; spells cost 10 % more', e: {} },
    { id: 'wayfarer', name: 'Wayfarer', isNew: true, text: '+15 % movement speed; −10 % maximum HP', e: { hp: -0.1 } }
  ],
  // The classes the planner knows (the simulation's builds): what they attack with and the order an ordinary build of
  // that kind spends its points in. After the list, the small nodes of its path and of Bulwark fill round and round.
  classes: [
    { id: 'knight_2h', name: 'Champion, two-handed', style: 'm', plan: 'arms' },
    { id: 'knight_sns', name: 'Champion, sword and shield', style: 'm', plan: 'arms_shield' },
    { id: 'minotaur_dual', name: 'Minotaur Lord', style: 'm', plan: 'arms' },
    { id: 'dk_vampire', name: 'Lich King', style: 'm', plan: 'arms' },
    { id: 'troll', name: 'War Troll', style: 'm', plan: 'arms_shield' },
    { id: 'seraph', name: 'Archangel', style: 'm', plan: 'arms' },
    { id: 'monk', name: 'Master (Monk)', style: 'm', plan: 'arms' },
    { id: 'assassin', name: 'Assassin', style: 'm', plan: 'arms' },
    { id: 'dragon', name: 'Great Wyrm', style: 'm', plan: 'dragon' },
    { id: 'archer', name: 'Master Archer', style: 'b', plan: 'archery' },
    { id: 'archmage', name: 'Arch Mage', style: 's', plan: 'arcana' },
    { id: 'elementalist', name: 'Master of Elements', style: 's', plan: 'arcana' },
    { id: 'priest', name: 'Priest of Light', style: 's', plan: 'arcana' }
  ],
  plans: {
    arms: [['cleave', 1], ['vigor', 3], ['weapon_training', 2], ['cleave', 3], ['bloodthirst', 2], ['sweeping_blows', 3], ['vigor', 6], ['recuperate', 1], ['onslaught', 3], ['brawn', 4], ['charge', 1], ['thick_skin', 5], ['weapon_training', 5], ['ground_slam', 2], ['fighting_style', 3], ['executioner', 3], ['war_cry', 2], ['deflect', 1], ['bloodthirst', 3], ['last_stand', 3], ['bloodlust', 3], ['rend', 1], ['iron_will', 2], ['bladestorm', 2], ['spell_ward', 3], ['second_skin', 3], ['unstoppable', 2]],
    arms_shield: [['cleave', 1], ['vigor', 3], ['weapon_training', 2], ['cleave', 3], ['bloodthirst', 2], ['shield_wall', 2], ['sweeping_blows', 3], ['vigor', 6], ['recuperate', 1], ['onslaught', 3], ['brawn', 4], ['thick_skin', 5], ['weapon_training', 5], ['ground_slam', 2], ['fighting_style', 3], ['executioner', 3], ['war_cry', 2], ['deflect', 1], ['bloodthirst', 3], ['last_stand', 3], ['bloodlust', 3], ['iron_will', 2], ['bladestorm', 2], ['spell_ward', 3], ['second_skin', 3]],
    dragon: [['vigor', 5], ['bloodthirst', 3], ['recuperate', 1], ['thick_skin', 5], ['weapon_training', 5], ['deflect', 1], ['last_stand', 3], ['iron_will', 2], ['scavenger', 5], ['spell_ward', 3], ['second_skin', 3]],
    archery: [['multishot', 1], ['vigor', 3], ['marksman', 2], ['multishot', 3], ['bloodthirst', 2], ['piercing_arrows', 3], ['vigor', 6], ['recuperate', 1], ['pinning_shot', 1], ['steady_aim', 3], ['hardy', 4], ['thick_skin', 5], ['marksman', 5], ['rain_of_arrows', 2], ['hunters_mark', 2], ['first_blood', 3], ['deflect', 1], ['quickfoot', 2], ['lure', 1], ['last_stand', 3], ['leap_back', 1], ['trophy_hunter', 3], ['iron_will', 2], ['barrage', 2], ['eagle_eye', 3], ['spell_ward', 3], ['second_skin', 3]],
    arcana: [['blink', 1], ['vigor', 3], ['attunement', 2], ['channeling', 2], ['bloodthirst', 2], ['overload', 3], ['vigor', 8], ['recuperate', 1], ['binding_circle', 1], ['wellspring', 4], ['thick_skin', 5], ['attunement', 5], ['arcane_ward', 2], ['echo', 3], ['focus', 2], ['spell_surge', 1], ['deflect', 1], ['blink', 3], ['last_stand', 3], ['siphon', 3], ['mana_tide', 1], ['iron_will', 2], ['stasis', 2], ['elemental_mastery', 3], ['spell_ward', 3], ['second_skin', 3]]
  }
};
