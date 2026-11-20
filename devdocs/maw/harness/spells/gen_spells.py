import json, re, textwrap

S = '/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/67306c2b-0ca8-4c66-afad-4546c9e2b3bb/scratchpad/spells'
T = json.load(open(S + '/tables.json'))
R = json.load(open(S + '/rules.json'))
RULE = {v['id']: (k, v) for k, v in R.items() if v}

SCHOOLS = ['fire', 'air', 'water', 'earth', 'spirit', 'mind', 'body', 'light', 'dark', 'dark_elf', 'vampire', 'dragon']


def school(i):
    return SCHOOLS[(i - 1) // 11]


# spellPowers, zzMaw-Spells.lua:1892-1933 (add, diceMin, diceMax)
DMG = {2: (8, 1, 2), 6: (0, 1, 8), 7: (0, 1, 10), 8: (10, 1, 30), 9: (2, 1, 1), 10: (12, 1, 7), 11: (19, 1, 21),
       15: (0, 1, 4), 18: (12, 1, 8), 20: (20, 1, 12), 22: (7, 1, 1), 24: (5, 1, 3), 26: (6, 1, 7), 29: (4, 1, 14),
       32: (6, 1, 6), 37: (8, 1, 5), 39: (7, 1, 7), 41: (8, 1, 8), 43: (4, 1, 2), 44: (15, 0.5, 0.5),
       52: (20, 2, 16), 59: (12, 1, 6), 65: (25, 1, 25), 70: (4, 1, 4), 76: (20, 1, 5), 78: (12, 1, 2),
       79: (45, 1, 45), 84: (30, 2, 6), 87: (60, 1, 60), 90: (15, 1, 9), 93: (0, 1, 7), 97: (0, 1, 28),
       98: (50, 1, 1), 99: (25, 1, 5), 103: (46, 1, 28), 111: (0, 1, 22), 123: (0, 1, 25)}
AOE = {6, 7, 8, 9, 10, 15, 22, 24, 32, 41, 43, 84, 93, 97, 98, 99, 123}
# getBaseHealingSpells, zzMaw-Spells.lua:2345-2352 (cost, base, scaling) N/E/M/G
HEAL = {49: ([0, 5, 10, 20], [0, 10, 20, 30], [0, 4, 6, 8]),
        54: ([0, 0, 25, 40], [0, 0, 0, 0], [0, 0, 7, 9]),
        55: ([0, 0, 0, 100], [0, 0, 0, 150], [0, 0, 0, 21]),
        68: ([2, 4, 6, 8], [4, 8, 12, 16], [2, 3, 4, 6]),
        74: ([0, 0, 15, 25], [0, 0, 25, 40], [0, 0, 7, 10]),
        77: ([0, 0, 0, 30], [0, 0, 0, 15], [0, 0, 0, 4])}
HEAL_INSANITY = {49: ([0, 15, 30, 60], [0, 20, 40, 60], [0, 8, 12, 16]),
                 54: ([0, 0, 25, 40], [0, 0, 0, 0], [0, 0, 7, 9]),
                 55: ([0, 0, 0, 300], [0, 0, 0, 450], [0, 0, 0, 50]),
                 68: ([6, 15, 24, 40], [12, 24, 36, 48], [6, 9, 12, 15]),
                 74: ([0, 0, 45, 100], [0, 0, 50, 100], [0, 0, 16, 25]),
                 77: ([0, 0, 0, 150], [0, 0, 0, 50], [0, 0, 0, 12])}
# CCMAP, zzMaw-Spells.lua:1337-1350 (game minutes, school, DR group, path)
CC = {34: (2, 'earth', None, 'engine stun with scripted roll'), 35: (6, 'earth', 1, 'scripted'),
      60: (10, 'mind', 2, 'scripted'), 113: (10, 'dark_elf (bug: spell is vampire)', 2, 'scripted'),
      62: (4.5, 'mind', 2, 'scripted, bypasses engine aim'), 63: (3, 'mind', 2, 'engine path'),
      122: (4, 'mind (bug: spell is dragon)', 2, 'engine path'), 66: (5, 'mind', 2, 'scripted, bypasses engine aim'),
      81: (3, 'light', 3, 'scripted'), 92: (4, 'dark', 1, 'impact, flat duration, m targets'),
      96: (6, 'dark', 1, 'scripted'), 48: (5, 'spirit', 2, 'engine path, undead only'),
      94: (10, 'dark', 2, 'scripted, undead only')}
# buffSpell / utilitySpell, zzMaw-Spells.lua:2608-2642
AURA = {3: 60, 4: 90, 14: 60, 25: 60, 36: 60, 58: 60, 69: 60, 5: 120, 8: 40, 17: 75, 28: 150, 38: 75, 46: 75, 47: 75,
        50: 120, 51: 120, 56: 120, 71: 120, 73: 75, 75: 180, 83: 200, 85: 150, 86: 300, 91: 150, 95: 10}
UTIL = {1: 5, 12: 5, 27: 20}
ASC_DAMAGE = {2, 6, 7, 8, 9, 10, 11, 15, 18, 20, 22, 24, 26, 29, 32, 37, 39, 41, 43, 44, 52, 59, 65, 70, 76, 78, 79,
              84, 87, 90, 93, 97, 98, 99, 103, 111, 123}

NOTES = {
    1: ['utility aura: flat 5 SP reserved, x(1 - EnlightenmentMastery/10) (SP:2636, 3048-3049)',
        'Torch power = holder mastery + 1 (SP:2874-2875); solo party: always on, power >= 3 (SP:2972-2974)'],
    2: ['damage 8 + 1d2 per point'],
    3: ['aura, see buff_auras.yml: Fire res and Intellect %'],
    4: ['aura: party weapons gain fire damage = weapon item-level damage x 10/15/20/25 % by holder mastery, '
        'floor 3/6/12/24 (x2 two-handed) (zzMaw-Items.lua:4280-4300); also added to spells (SP:2021-2037)'],
    5: ['aura, see buff_auras.yml'],
    6: ['damage 0 + 1d8; AoE (weapon-enchant add / 2.5)'],
    7: ['damage 0 + 1d10 per point; Master x8/6, GM x10/6 (SP:1989-1995); delay 150 -> 100'],
    8: ['aura (40 % base reservation); damage 10 + 1d30 per point, Ascension-scaled, AoE'],
    9: ['damage 2 + 1 per point (fixed); cost 20 -> 40; delay x2'],
    10: ['damage 12 + 1d7; cost 25 -> 50'],
    11: ['damage 19 + 1d21'],
    12: ['utility aura: flat 5 SP reserved (SP:2637)', 'solo party or NPC profession 38: always on (power 10, skill 2) '
         '(SP:2968-2983)', 'Shadow/Omnipotent boss within 2000 suppresses it (SP:2992-3005)'],
    14: ['aura, see buff_auras.yml: Air res and Speed %'],
    15: ['damage 0 + 1d4 per point (was 2 + 1 fixed); cost 4/8/10/12; AoE'],
    16: ['solo: Jump scroll (item 315) is refunded (SP:1107-1108)'],
    17: ['aura, see buff_auras.yml'],
    18: ['renamed Chain Lightning (SP:743-746); damage 12 + 1d8',
         'Master/GM cost 20/30 in Lua (SP:1883-1885), table 10/10/10/10',
         'on hit with mastery > 1 a copy (mastery - 1, same skill) flies to the closest living monster within 768 '
         '(any monster, not only hostiles; only the struck monster excluded, so it can bounce back): '
         'N 1, E 2, M 3, GM 4 hits (MawCore/Damage.lua:399-428)'],
    19: ['cannot be cast while the enemy detector is yellow or red (SP:157-161)',
         'duration Master (15 + s) x 1.5 game min, GM (30 + 2s) x 1.5 game min (SP:711-716); '
         'tooltip says 15 + 1.5/pt and 30 + 3/pt (SP:749-750)',
         'Insanity: removed when the detector turns red (SP:3849-3857); 7d11 Wall of Mist forces it on (SP:733-737)'],
    20: ['damage 20 + 1d12'],
    21: ['not an aura (commented out of utilitySpell, SP:2639); unchanged cost',
         'bolster > 100 or Austerity: any party hit on a monster converts Fly into Feather Fall with the same expiry, '
         'except on 11 maps (MawCore/Damage.lua:317-329, SP:1018)',
         'solo: Fly scroll refunded and sets Fly for 7 h at GM, recovery 120 (SP:1109-1117)'],
    22: ['damage 7 + 1 per point (fixed); cost 30 -> 60; delay 90 -> 140'],
    24: ['damage 5 + 1d3; cost 2/4/5/6; AoE'],
    25: ['aura, see buff_auras.yml: Water res and Luck %'],
    26: ['damage 6 + 1d7 (Death Knight Icy Touch reuses this id, see class_perks.yml)'],
    27: ['utility aura: flat 20 SP reserved (SP:2640); solo scroll (item 326) refunded'],
    29: ['damage 4 + 1d14'],
    30: ['MMMerge "catalyst -> Philosopher\'s Stone" conversion disabled (SpellsTweaks.lua:197-210 diff)'],
    31: ['solo: scroll (item 330) refunded; Madness: cannot cast with enemies nearby (SP:3728-3735)'],
    32: ['damage 6 + 1d6; AoE'],
    33: ['solo: scroll (item 332) refunded'],
    34: ['MAW-scripted success roll: chance = 30 / (30 + L/4), L = calcEffectChance(level, Earth res, Earth skill, '
         '0.01), x2 on bosses, cut by map affix 13 (MawCore/Damage.lua:334-357, SP:1855-1865)',
         'on success the engine applies MMMerge stun + paralysis 1 game min + s*m ticks (SpellsTweaks.lua:50-58); '
         'CCMAP duration (2 min) is only printed in the tooltip',
         'cost and delay use the CC formulas (see crowd_control.yml)'],
    35: ['scripted CC (see crowd_control.yml); MMMerge resistance check forced to pass (SpellsTweaks.lua:24-41)'],
    36: ['aura, see buff_auras.yml: Earth res and Endurance %'],
    37: ['damage 8 + 1d5'],
    38: ['aura, see buff_auras.yml'],
    39: ['damage 7 + 1d7; tooltip calls it the only physical spell (SP:2306)'],
    41: ['damage 8 + 1d8; AoE'],
    43: ['damage 4 + 1d2; cost 25 -> 50; delay 180/180/180/160; AoE'],
    44: ['damage = (15 % + 0.5 % x skill) of t.HP (SP:1939-1942), then / sqrt(bolster mult: 100 -> 1, 150 -> 1.4, '
         '200 -> 1.8, 300 -> 3, Doom 3.33 x (1 + lvl/75), boss x2 x (1 + lvl/80)), x4 Austerity, '
         'x max(1, (level/250)^2) (MawCore/Damage.lua:363-396)',
         'GM cost = ceil(min(LevelBase,255)^1.4 / 12.5 x personality factor) (SP:2275-2277); '
         'MMMerge resistance check forced to pass (SpellsTweaks.lua:24-41)'],
    46: ['aura (SingleBuff 1 on every member), see buff_auras.yml'],
    47: ['aura (SingleBuff 4 on every member), see buff_auras.yml'],
    48: ['engine-path CC, undead only (see crowd_control.yml)'],
    49: ['Remove Curse becomes a heal that also cures Curse: E/M/G base 10/20/30 + 4/6/8 per point, '
          'cost 5/10/20 (healing table); auto-target on quick cast (SP:178-222, 1307-1312)'],
    50: ['aura (party-wide), see buff_auras.yml'],
    51: ['aura, see buff_auras.yml'],
    52: ['damage 20 + 2d16 per point (diceMin 2); Master range forced to 0x180 = 384 (SP:1009-1014)'],
    53: ['GM: also clears Dead/Eradicated/Unconscious and sets HP >= 1 (SP:250-260)'],
    54: ['rewritten: participants (not Dead/Eradicated/Stoned), highest HP first, stop when the running total would '
          'go below 0; pool = their HP + heal, redistributed evenly up to max HP, never kills (SP:824-1003)',
          'heal = (Base + Scaling x s / 2) x heal mult - 3s (M) / -4s (G), floor 0; Base 0, Scaling 7/9; '
          'M/G cost 25/40 from the healing table override the table value 12 (SP:2397-2399)'],
    55: ['GM: heal 150 + 21 per point on the target, works on Dead/Eradicated (HP = max(hp + heal, heal)) '
          '(SP:262-316); cost 100 (healing table); delay GM 1000 -> 300',
          'quick-cast auto-target is broken (uses undefined idx and Greater Heal numbers, SP:1287-1294)'],
    56: ['Telepathy replaced by the Meditation aura (party SP regen), see buff_auras.yml'],
    58: ['aura, see buff_auras.yml: Mind res and Personality %'],
    59: ['damage 12 + 1d6; delay 120/110/100/90'],
    60: ['scripted CC (Mind Charm; no const name in MMExt)'],
    62: ['scripted CC, quick-cast bypasses engine aiming (SP:1546-1579)'],
    63: ['engine-path CC; cost 15 -> 40; delay 80 -> 200'],
    65: ['damage 25 + 1d25'],
    66: ['scripted CC, quick-cast bypasses engine aiming'],
    68: ['heal N/E/M/G 4/8/12/16 + 2/3/4/6 per point, cost 2/4/6/8 (healing table); engine heal 5 + (m+1)s is '
          'subtracted so the net is the MAW value (SP:319-374); Death Knights cannot cast it; auto-target'],
    69: ['aura, see buff_auras.yml: Body res and Might %'],
    70: ['damage 4 + 1d4'],
    71: ['aura, see buff_auras.yml'],
    73: ['aura, see buff_auras.yml'],
    74: ['renamed Greater Heal: M/G 25/40 + 7/10 per point, cost 15/25, also cures Disease (SP:397-449, 765-768); '
          'Death Knights cannot cast it; auto-target'],
    75: ['aura (180 %): Power 50 / Skill 4 re-set every 0.5 s, so charges never run out; also blocks Unconscious '
          '(SP:676-685, 2904-2907)'],
    76: ['damage 20 + 1d5 (Death Knight Asphyxiate reuses this id)'],
    77: ['heal GM 15 + 4 per point to every member (engine 10 + 5s subtracted) (SP:461-543)'],
    78: ['damage 12 + 1d2'],
    79: ['damage 45 + 1d45; cost 10 -> 50'],
    81: ['scripted CC (Light), DR group 3'],
    82: ['cost 25/50/75/100; if the engine did not summon, MAW spawns monster 97 at power C (id 99) while fewer '
          'than 2m - 3 wisps live (M 3, GM 5) (SP:3435-3455)'],
    83: ['aura, see buff_auras.yml'],
    84: ['damage 30 + 2..6 per point (diceMin 2); AoE'],
    85: ['aura, see buff_auras.yml'],
    86: ['aura, see buff_auras.yml (Haste + Shield + Stone Skin + Fate at skill / 1.5)'],
    87: ['damage 60 + 1d60'],
    90: ['damage 15 + 1d9'],
    91: ['renamed Vampiric Aura: party +5 % melee, +2.5 % ranged and spell leech (zzMaw-Items.lua:3272-3276)'],
    92: ['impact-applied CC; mastery buys targets (1 + (m-1) extra within 512 of the impact), flat duration '
          '(SP:1658-1732)'],
    93: ['damage 0 + 1d7; AoE'],
    94: ['scripted CC, undead only'],
    95: ['aura (10 %): engine Pain Reflection on every member'],
    96: ['scripted CC: ArmorHalved + Slow + DamageHalved (-30 % monster damage) + MeleeOnly '
          '(SP:1348, MawCore/Damage.lua:1575-1578); Death Knight Death Grasp reuses the id'],
    97: ['damage 0 + 1d28; AoE'],
    98: ['damage 50 + 1 per point (numbers unchanged, now Ascension-scaled); AoE'],
    99: ['damage 25 + 1d5; object spell rewritten to 201 for the leech fix (SP:3781-3790); AoE'],
    103: ['damage 46 + 1d28; cost 30 -> 20'],
    111: ['damage 0 + 1d22 per point, Master x5/3, GM x7/3 (SP:1996-2002, object spell 200); cost 5/5/10/15; '
           'delay E/M/G 90 -> 100'],
    113: ['Vampire Charm = const.Spells.Charm in MM8: scripted CC but CCMAP school is DarkElfAbility '
           '(SP:1341), so a vampire caster reads skill 0 -> 0.5 duration step'],
    114: ['Mistform: -75 % physical damage taken (SP:790, MawCore/Damage.lua:1729-1731, zzMaw-Stats.lua:690-715)'],
    122: ['engine-path CC; cost fixed 15/15/25/30 (SP:1385-1389, 2189-2194); delay fixed 120 '
           '(zzMaw-Stats.lua:167); duration ignores Ascension and resistance; CCMAP school Mind (bug)'],
    123: ['class spell, see class_perks.yml (damage 0 + 1d25 placeholder, scaled in zzClasses)'],
}


def eq(a, b):
    return a == b


def fmt(v):
    if isinstance(v, list):
        return '[' + ', '.join(fmt(x) for x in v) + ']'
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def q(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'


out = []
out.append('# draft extracted from MAW ef23ee17')
out.append('# Spell data for an OpenYAMM "MAW" ruleset. Generated from MAW Data/Tables/Spells2.txt, base')
out.append('# reference/mmmerge/Data/Tables/Spells2.txt, OpenYAMM assets_dev/engine/data_tables/spells.txt and the')
out.append('# BackendSpellRule switch in game/party/PartySpellSystem.cpp, plus the Lua overrides in')
out.append('# Scripts/General/zzMaw-Spells.lua (SP:line). Spec: ../CLASSES_SPELLS_SPEC.md section 1.')
out.append('#')
out.append('# Fields')
out.append('#   cost / delay: [Normal, Expert, Master, GM]; cost in SP before Ascension and the personality factor,')
out.append('#                 delay in recovery ticks before Speed, Haste, Ascension and armour (spec section 1.2).')
out.append('#   damage: {add, dice_min, dice_max}: add + sum over skill points of rand(dice_min..dice_max);')
out.append('#           dice_min == dice_max means a fixed amount per point (SP:1976-1986).')
out.append('#   base: reference/mmmerge Spells2.txt.  openyamm: spells.txt row plus the explicit BackendSpellRule')
out.append('#   values that override it (rule_*; empty = rule falls back to the table).  maw: MAW values.')
out.append('#   ascension: damage | heal | cc | none.  kind: damage | heal | aura | utility_aura | cc | other.')
out.append('#   change: which OpenYAMM fields a MAW ruleset has to change.')
out.append('# Class-specific spell variants (Death Knight, Assassin, Elementalist, Dragon) are under class_variants.')
out.append('')
out.append('ascension_scope:')
out.append('  damage_spells: [' + '\n    '.join(textwrap.wrap(', '.join(str(x) for x in sorted(ASC_DAMAGE)), 100)) + ']  # SP:1888')
out.append('  healing_spells: [49, 54, 55, 68, 74, 77]  # SP:2108, 2169')
out.append('  cc_spells: [34, 35, 48, 60, 62, 63, 66, 81, 92, 94, 96, 113, 122]  # CCMAP keys, SP:1337-1350')
out.append('  # weapon enchant damage / 2.5 on these, SP:2094')
out.append('  aoe_enchant_divisor_spells: ' + fmt(sorted(AOE)))
out.append('')
out.append('spells:')
for i in range(1, 133):
    r = T[str(i)]
    m, w, o = r['mm'], r['maw'], r['oy']
    if not m or m['name'].startswith('Unused'):
        continue
    out.append('  - id: %d' % i)
    out.append('    name: %s' % q(m['name']))
    out.append('    school: %s' % school(i))
    out.append('    base: {cost: %s, delay: %s, damage: {add: %d, dice: %d}}' % (fmt(m['cost']), fmt(m['delay']),
                                                                             m['add'], m['dice']))
    oyparts = []
    if o:
        tdiff = []
        if o['cost'] != m['cost']:
            tdiff.append('cost: %s' % fmt(o['cost']))
        if o['delay'] != m['delay']:
            tdiff.append('delay: %s' % fmt(o['delay']))
        if (o['add'], o['dice']) != (m['add'], m['dice']):
            tdiff.append('damage: {add: %d, dice: %d}' % (o['add'], o['dice']))
        oyparts.append('table: %s' % ('same_as_base' if not tdiff else '{' + ', '.join(tdiff) + '}'))
    ru = RULE.get(i)
    if ru:
        name, v = ru
        a = v['args']
        rparts = ['line: %d' % v['line']]
        if len(a) > 3 and a[3] != '{}':
            rparts.append('rule_cost: ' + a[3].replace('{', '[').replace('}', ']'))
        if len(a) > 4 and a[4] != '{}':
            rparts.append('rule_delay: ' + a[4].replace('{', '[').replace('}', ']'))
        if len(a) > 7:
            rparts.append('rule_damage: {add: %s, dice: %s, linear: %s}' % (a[6], a[7], a[8] if len(a) > 8 else 'false'))
        oyparts.append('rule:')
        for x in rparts:
            oyparts.append('  ' + x.replace('rule_', '').replace(': ', ': ', 1))
    else:
        oyparts.append('rule: none')
    out.append('    openyamm:')
    for x in oyparts:
        out.append('      ' + x)
    # MAW block
    cost = list(w['cost'])
    if i == 18:
        cost = [10, 10, 20, 30]
    kind = 'other'
    asc = 'none'
    mw = []
    if i in HEAL:
        c, b, sc = HEAL[i]
        kind, asc = 'heal', 'heal'
        mw.append('heal: {cost: %s, base: %s, per_point: %s}' % (fmt(c), fmt(b), fmt(sc)))
        mw.append('heal_insanity: {cost: %s, base: %s, per_point: %s}  # SP:2336-2343' % (
            fmt(HEAL_INSANITY[i][0]), fmt(HEAL_INSANITY[i][1]), fmt(HEAL_INSANITY[i][2])))
    if i in DMG:
        a, dmin, dmax = DMG[i]
        kind, asc = 'damage', 'damage'
        mw.append('damage: {add: %s, dice_min: %s, dice_max: %s%s}' % (fmt(float(a)), fmt(float(dmin)), fmt(float(dmax)),
                                                                     ', aoe: true' if i in AOE else ''))
    if i in AURA:
        kind = 'aura'
        mw.append('aura: {reserve_cost: %d}  # SP cost set to 0, see buff_auras.yml' % AURA[i])
    if i in UTIL:
        kind = 'utility_aura'
        mw.append('aura: {flat_reserve: %d}' % UTIL[i])
    if i in CC:
        d, sch, g, path = CC[i]
        kind, asc = 'cc', 'cc'
        mw.append('cc: {base_minutes: %s, school: %s, dr_group: %s, path: %s}' % (fmt(float(d)), q(sch),
                                                                                'none' if g is None else g, q(path)))
    if i in (8,):
        kind = 'aura'
    out.append('    maw:')
    out.append('      kind: %s' % kind)
    out.append('      ascension: %s' % asc)
    cmt = '  # Lua, SP:1883-1885' if i == 18 else ''
    if i in AURA or i in UTIL:
        cmt = '  # Game.Spells cost forced to 0 (SP:2483-2496); Spells2 %s unused' % fmt(cost)
        cost = [0, 0, 0, 0]
    elif i in HEAL:
        cmt = '  # healing table replaces Spells2 %s (SP:2387-2434)' % fmt(cost)
        cost = HEAL[i][0]
    elif i == 122:
        cmt = '  # fixed in Lua (SP:1385-1389)'
        cost = [15, 15, 25, 30]
    out.append('      cost: %s%s' % (fmt(cost), cmt))
    out.append('      delay: %s' % fmt(w['delay']))
    for x in mw:
        out.append('      ' + x)
    notes = NOTES.get(i)
    if notes:
        out.append('      notes:')
        for n in notes:
            lines = textwrap.wrap(n, 100)
            out.append('        - "' + lines[0].replace('"', '\\"'))
            for ln in lines[1:]:
                out.append('          ' + ln.replace('"', '\\"'))
            out[-1] += '"'
    # change summary
    ch = []
    ref = o if o else m
    if cost != ref['cost'] and i not in AURA and i not in UTIL and i not in HEAL:
        ch.append('spells.txt mana')
    if w['delay'] != ref['delay']:
        ch.append('spells.txt recovery')
    if i in DMG:
        a, dmin, dmax = DMG[i]
        if (a, dmax) != (ref['add'], ref['dice']) or dmin != 1:
            ch.append('spells.txt DamageBase/DiceSides' + (' + new DiceMin column' if dmin != 1 else ''))
    if ru:
        a = ru[1]['args']
        if (len(a) > 3 and a[3] != '{}' and (i not in AURA and i not in UTIL)) and \
                [int(x) for x in a[3].strip('{}').split(',')] != cost:
            ch.append('BackendSpellRule mana')
        if len(a) > 4 and a[4] != '{}' and [int(x) for x in a[4].strip('{}').split(',')] != w['delay']:
            ch.append('BackendSpellRule recovery')
        if len(a) > 7 and i in DMG:
            ch.append('BackendSpellRule damage')
    if i in AURA or i in UTIL:
        ch.append('aura system (mana 0, reservation)')
    if i in HEAL:
        ch.append('heal table')
    if i in CC:
        ch.append('CC table')
    if ch:
        out.append('    change:')
        for x in ch:
            out.append('      - %s' % x)
    else:
        out.append('    change: []')

open('/home/pjasicek/github/OpenYAMM/devdocs/maw/data/spells.yml', 'w').write('\n'.join(out) + '\n')
print(len(out))

# merge the class-variant entries written by the classes pass
cv = open(S + '/../spells_class_variants.yml').read().splitlines()
body = []
for ln in cv:
    if ln.startswith('# draft extracted') or ln.startswith('# Class-specific spell variants (merge'):
        continue
    body.append(('  ' + ln) if ln.strip() else '')
txt = open('/home/pjasicek/github/OpenYAMM/devdocs/maw/data/spells.yml').read()
txt += '\n# Class-specific spell variants (Death Knight, Assassin, Elementalist, Dragon, Seraphim); see spec section 5.\n'
txt += 'class_variants:\n' + '\n'.join(body) + '\n'
open('/home/pjasicek/github/OpenYAMM/devdocs/maw/data/spells.yml', 'w').write(txt)
