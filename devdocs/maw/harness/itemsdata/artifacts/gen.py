import json, re, textwrap

D = '/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/67306c2b-0ca8-4c66-afad-4546c9e2b3bb/scratchpad/itemsdata/'
P = json.load(open(D + 'artifacts/parsed.json'))
C = {int(k): v for k, v in json.load(open(D + 'artifacts/calc.json')).items()}
POWER = {int(k): v for k, v in P['power'].items()}
ONHIT = {int(k): v for k, v in P['onhit'].items()}
OUT = '/home/pjasicek/github/OpenYAMM/devdocs/maw/data/artifacts.yml'

I = 'zzMaw-Items.lua'
A = 'zzzMaw_Artifacts.lua'


def load(path, enc='cp1252'):
    rows = {}
    with open(path, encoding=enc, errors='replace') as f:
        for line in f:
            c = line.rstrip('\r\n').split('\t')
            if c and c[0].strip().isdigit():
                rows[int(c[0])] = c
    return rows


ours = load('/home/pjasicek/github/OpenYAMM/assets_dev/engine/data_tables/items.txt', 'utf-8')
maw = load(D + 'maw/ITEMS.txt')
base = load(D + 'base/ITEMS.txt')

items_src = open('/home/pjasicek/github/Maw-Mod-MMMerge/Scripts/General/zzMaw-Items.lua').read().split('\n')
LIST = [int(x) for x in re.search(r'^mawArtifacts=\{([^}]*)\}', items_src[4480]).group(1).split(',')]
UNIQUE = sorted(set(LIST))

SLOT = {0: 'weapon_1h', 1: 'weapon_2h', 2: 'bow', 3: 'armor', 4: 'shield', 5: 'helm', 6: 'belt', 7: 'cloak',
        8: 'gauntlets', 9: 'boots', 10: 'ring', 11: 'amulet'}
SCHOOL = {12: 'Fire', 13: 'Air', 14: 'Water', 15: 'Earth', 16: 'Spirit', 17: 'Mind', 18: 'Body', 19: 'Light',
          20: 'Dark'}

SPELL_BONUS = {516: ([16, 18, 17], 3843), 521: ([20], 3845), 530: ([12, 13, 14, 15], 3847), 535: ([14], 3849),
               1314: ([14], 3851), 1315: ([17, 20], 3853), 1317: ([20], 3855), 1321: ([16], 3857),
               1323: ([19], 3859), 1325: ([12], 3861), 1329: ([17, 18], 3863), 1330: ([16], 3865),
               1347: ([16], 3867), 1348: ([13], 3869), 2032: ([19, 20], 3871), 2033: ([16, 18, 17], 3873),
               2034: ([12, 13, 14, 15], 3875)}
HP_REGEN = [509, 520, 1337, 1331, 1335, 2027]
SP_REGEN = [513, 1334, 1331, 2024, 2032, 2033, 2034]
WEAR = {504: ('Minotaurs only', 'GetRace(pl) == const.Race.Minotaur', '635-636'),
        508: ('Vampires only', 'GetRace(pl) == const.Race.Vampire', '638-639'),
        514: ('Dark Elves only', 'GetRace(pl) == const.Race.DarkElf', '641-642'),
        515: ('Knights only', 'pl.Class >= 16 and pl.Class <= 19', '644-645'),
        516: ('Clerics only', 'Game.ClassesExtra[pl.Class].Kind == 2', '647-648'),
        521: ('Liches only', 'pl.Class == 45', '650-651'),
        529: ('Necromancers and Liches only', 'pl.Class == 44 or pl.Class == 45', '653-654'),
        532: ('Elves only', 'race is DarkElf or Elf', '656-660'),
        1333: ('Goblins only', 'GetRace(pl) == const.Race.Goblin', '662-663'),
        1334: ('Humans only', 'GetRace(pl) == const.Race.Human', '665-666'),
        1335: ('Elves only', 'race is DarkElf or Elf', '668-672'),
        1336: ('Dwarves only', 'GetRace(pl) == const.Race.Dwarf', '674-675'),
        1337: ('Men only', 'Game.CharacterPortraits[pl.Face].DefSex == 0', '677-680'),
        1338: ('Women only', 'Game.CharacterPortraits[pl.Face].DefSex == 1', '682-685')}
BUFFS = {1306: ('{Shield: 3}', '736'), 1318: ('{WaterBreathing: 0}', '737'), 1322: ('{Shield: 3}', '738'),
         1333: ('{Shield: 3}', '739'), 1338: ('{WaterBreathing: 0}', '740'), 1347: ('{Preservation: 3}', '741'),
         1406: ('{WaterBreathing: 0}', '742'), 2023: ('{Bless: 3}', '743'),
         2026: ('{Shield: 3, Stoneskin: 20}', '744-745'), 2027: ('{Stoneskin: 20}', '746'),
         2028: ('{Shield: 3}', '747'), 2043: ('{Shield: 3}', '748')}
ALLCOND = '[Insane, Disease1, Disease2, Disease3, Paralyze, Stone, Poison1, Poison2, Poison3, Asleep]'
IMMUNE = {1307: (ALLCOND, '802-811'), 1309: ('[Paralyze]', '813'), 1322: ('[Stone]', '815'),
          1332: (ALLCOND, '817-826'), 1341: ('[Stone]', '828'), 2030: ('[Poison1, Poison2, Poison3]', '830-832'),
          2043: ('[Stone]', '834')}
SPEED = {515: '857', 1302: '858', 2024: '859', 2025: '860'}

SPELLS = {
    523: ['castAt(const.Spells.Slow) = evt.CastSpell(35 Slow) at the target, wielder Sword skill/mastery (A:127)'],
    525: ['castAt(const.Spells.Slow) = evt.CastSpell(35 Slow) at the target, wielder Sword skill/mastery (A:136)'],
    1308: ['CastSpellDirect(125, skill, mastery): spell 125 = "Wing Buffet" in mmmerge Spells.txt (A:181)',
           'castAt(6 Fireball) at the target, wielder Axe skill/mastery (A:182)'],
    2021: ['CastSpellDirect(125, 7, 3): fixed skill 7 mastery 3 (A:233)',
           'castAt(18 Lightning Bolt) only if t.Monster.HP - t.Result > 0, wielder Mace skill/mastery (A:234-236)'],
    2025: ['castAt(6 Fireball) at the target, wielder Bow skill/mastery (A:258)'],
    2035: ['CastSpellDirect(29 Acid Burst, skill, mastery): wielder Sword skill/mastery, no target coordinates '
           '(A:268-269)'],
}

NOTES = {
    502: [],
    504: ['zzzMaw_Artifacts.lua:90 says "Swift ... live elsewhere", but 504 is not in artifactAttackSpeed: no '
          'attack-speed bonus anywhere.'],
    506: ['MAW note prints "Swift"; 506 is not in artifactAttackSpeed.'],
    508: ['No artifactPower entry: no stat budget.', 'Vampiric flag is dead (see open questions).'],
    511: ['No rule data in any table (no budget, on-hit, immunity, buff). The MAW note\'s "of Shielding; Immune to '
          'disease, paralysis, and poison" is not implemented; only the generic artifact base damage applies.'],
    512: ['MAW note prints "Swift"; 512 is not in artifactAttackSpeed.'],
    518: ['MAW note prints "Swift, Immunity to Sleep"; neither is in the behaviour tables.'],
    519: ['Ring: resistance coefficients are halved by the ring read transform (Formulas.lua:14-19).'],
    521: ['Helm with Mod2 = 0 counts as a hat: slot multiplier 1.25 * 1.5 = 1.875 (zzMaw-Items.lua:4421-4423).'],
    522: ['MAW note prints "Feather Falling"; no buff entry.'],
    527: ['Vampiric flag is dead (see open questions).'],
    528: ['MAW note prints "Water Breathing"; no buff entry.'],
    530: ['Comment at zzMaw-Items.lua:3589: the four spell schools are the item, the AC is the price.'],
    531: ['Not in artWeap1h/2h: base damage reads the ladder tier of its NotIdentifiedName run instead of tier 6.'],
    533: ['Listed twice in mawArtifacts (zzMaw-Items.lua:4481): two pity slots, about double drop weight.'],
    534: ['MAW note prints immunity to Fear, Stone, Paralysis and Sleep; no artifactImmunities entry.'],
    535: ['Ring: no resistance coefficients, so the ring transform does not apply.'],
    536: ['Helm with Mod2 = 0 counts as a hat: slot multiplier 1.875.'],
    537: ['MAW note prints "Immune to Fear"; not implemented.'],
    542: ['material is Special (not Artifact/Relic) in MAW, base and OpenYAMM tables.',
           'No artifactPower entry: no stat budget.',
           'zzzMaw_Artifacts.lua:168-169 calls this the "of Carnage" enchant; enchant 46 is "of The Dragon" in '
           'MAW SPCITEMS.TXT (Carnage is 3).'],
    1303: ['EquipStat is Weapon2 but the id sits in artWeap1h (zzMaw-Items.lua:2330): the legacy dice upscaler '
           'doubles instead of triples. The damage model still treats it as two-handed (IsTwoHandedWeapon reads '
           'EquipStat).'],
    1306: ['Reference AC comes from 1315 Ruler\'s Ring (0) because the whole 1302-1315 run shares the '
           'NotIdentifiedName "Artifact": no level AC growth (see open questions).'],
    1307: ['Reference AC 0 from 1315 Ruler\'s Ring: no level AC growth.'],
    1308: ['Flat FireResistance 65000 is the immunity threshold (zzMaw-Stats.lua:1145).'],
    1309: ['No artifactPower entry: no stat budget.'],
    1310: ['No artifactPower entry: no stat budget.', 'MAW note prints only slaying; no other effect.'],
    1311: ['No rule data in any table (no budget, no on-hit): only the generic artifact base damage.'],
    1313: ['Reference AC 0 from 1315 Ruler\'s Ring: no level AC growth.'],
    1314: ['Reference AC 0 from 1315 Ruler\'s Ring: no level AC growth.'],
    1315: ['No artifactPower entry; the item is its spell-school bonus only.'],
    1317: ['Not in artWeap1h/2h: base damage reads ladder tier 1.357 of the 1316-1330 "Relic" run, '
           'flat 16*(1.357-1)/5 = 1.143 instead of 16.',
           'Meditation skill bonus is subject to the 2x base skill cap (zzMaw-Items.lua:2605-2611).'],
    1318: ['Reference AC 17 borrowed from 1330 Mekorig\'s Hammer (Mod2 15 + dice count 2).',
           'MAW note prints "Water Walking"; the buff table grants WaterBreathing instead.'],
    1321: ['Reference AC 17 borrowed from 1330 Mekorig\'s Hammer.'],
    1322: ['Reference AC 17 borrowed from 1330 Mekorig\'s Hammer.',
           '"Half damage from missile attacks" is the Shield buff.'],
    1323: ['Reference AC 17 borrowed from 1330 Mekorig\'s Hammer.'],
    1324: ['Reference AC 17 borrowed from 1330 Mekorig\'s Hammer.'],
    1325: ['Helm with Mod2 = 0 counts as a hat: slot multiplier 1.875.',
           'Not in artArmors: worn AC stays 0, but the tooltip prints round(17*power/40) (Tooltip.lua:546-554).'],
    1326: ['Reference AC 17 borrowed from 1330 Mekorig\'s Hammer.'],
    1327: ['Reference AC 17 borrowed from 1330 Mekorig\'s Hammer.'],
    1329: ['MAW note prints "Undead slaying"; there is no artifactOnHit entry.'],
    1331: ['MAW note prints "Feather Falling"; no buff entry. NotIdentifiedName is "Sandals" (own ladder run).'],
    1332: ['Budget is drawbacks only; the item is its immunities.'],
    1333: ['EquipStat is Weapon2 but the id sits in artWeap1h: legacy dice upscaler doubles instead of triples.',
           '"Of Shielding" is the Shield buff.'],
    1338: ['Ring: resistance coefficients halved.',
           'MAW note prints "Water walking, Feather falling"; the buff table grants WaterBreathing instead.'],
    2024: ['SP coefficient goes through the vitality read transform.'],
    2026: ['Reference AC 3 borrowed from 2034 Morgan (whole 2020-2034 run is "Artifact").'],
    2027: ['Reference AC 3 borrowed from 2034 Morgan.'],
    2028: ['Reference AC 3 borrowed from 2034 Morgan.'],
    2029: ['Not in artArmors: worn AC stays 5, but the tooltip prints 5 + round(3*power/40).',
           'SP coefficient goes through the vitality read transform.'],
    2030: ['Reference AC 3 borrowed from 2034 Morgan.'],
    2031: ['Reference AC 3 borrowed from 2034 Morgan.'],
    2032: ['Not in artArmors: worn AC stays 2, tooltip prints 2 + round(3*power/40).'],
    2033: ['Not in artArmors: worn AC stays 2, tooltip prints 2 + round(3*power/40).'],
    2034: ['Not in artArmors: worn AC stays 3, tooltip prints 3 + round(3*power/40).'],
    2035: ['On-hit coefficient 2 is paid for by the -0.1 leech (comment zzzMaw_Artifacts.lua:261-262).'],
    2041: ['Reference AC 6 borrowed from 2049 Hera (whole 2035-2049 run is "Relic").'],
    2042: ['Reference AC 6 borrowed from 2049 Hera.'],
    2043: ['Reference AC 6 borrowed from 2049 Hera.'],
    2044: ['Not in artArmors: worn AC stays 10, tooltip prints 10 + round(6*power/40).'],
    2045: ['Reference AC 6 borrowed from 2049 Hera.'],
    2046: ['Reference AC 6 borrowed from 2049 Hera.'],
    2047: ['Not in artArmors: worn AC stays 4, tooltip prints 4 + round(6*power/40).'],
    2048: ['Not in artArmors: worn AC stays 4, tooltip prints 4 + round(6*power/40).'],
    2049: ['Not in artArmors: worn AC stays 6, tooltip prints 6 + round(6*power/40).',
           'HP and SP coefficients go through the vitality read transform.'],
    # other_artifact_rules
    516: ['Not in mawArtifacts: never dropped or chest re-rolled. In artArmors (level AC growth).',
          'Value 0 in ITEMS.txt.'],
    532: ['Not in mawArtifacts, yet has an artifactPower entry. Not in artWeap1h/2h: ladder tier 3.5 base damage.',
          'MAW note prints "Swift"; 532 is not in artifactAttackSpeed.'],
    538: ['Not in mawArtifacts. In artWeap1h: tier-6 base damage at party total level, but IsArtifactId is true.',
          'Comment: "its VarA special, stripped at roll time".'],
    539: ['Not in mawArtifacts. In artWeap1h.'],
    540: ['Not in mawArtifacts. In artWeap2h.'],
    541: ['Not in mawArtifacts. In artWeap2h.'],
    543: ['Not in mawArtifacts, yet has an artifactPower entry and the Cycle of Life rule.',
           'Ring, Endurance coefficient (not a resistance), so no ring transform.'],
    1341: ['Not in mawArtifacts. Immunity entry only.'],
    1347: ['Not in mawArtifacts. Buff and spell-school entries only.'],
    1348: ['Not in mawArtifacts. Spell-school entry only.'],
    2020: ['Not in mawArtifacts (keep-list comment calls it already outside). In artWeap1h.',
           'Vampiric flag is dead (see open questions). ITEMS.txt dice: MAW 2d6 15, base/OpenYAMM 2d3 10.'],
}

# names of the stats as const.Stats keys in MAW
def flow(pairs):
    return '{' + ', '.join('%s: %s' % (k, v) for k, v in pairs) + '}'


def emit_flow(indent, key, pairs):
    head = ' ' * indent + key + ': {'
    parts = ['%s: %s' % (k, v) for k, v in pairs]
    one = head + ', '.join(parts) + '}'
    if len(one) <= 120:
        emit(one)
        return
    cur = head
    pad = ' ' * len(head)
    for n, part in enumerate(parts):
        piece = part + (', ' if n < len(parts) - 1 else '}')
        if len(cur) + len(piece.rstrip()) > 120:
            emit(cur.rstrip())
            cur = pad
        cur += piece
    emit(cur.rstrip())


def q(s):
    return json.dumps(s, ensure_ascii=False)


lines = []


def emit(s=''):
    lines.append(s)


def emit_str(indent, key, s):
    one = ' ' * indent + key + ': ' + q(s)
    if len(one) <= 120:
        emit(one)
        return
    emit(' ' * indent + key + ': >-')
    for w in textwrap.wrap(s, 120 - indent - 2, break_long_words=False, break_on_hyphens=False):
        emit(' ' * (indent + 2) + w)


def emit_list(indent, key, items):
    if not items:
        return
    emit(' ' * indent + key + ':')
    for it in items:
        one = ' ' * (indent + 2) + '- ' + q(it)
        if len(one) <= 120:
            emit(one)
        else:
            emit(' ' * (indent + 2) + '- >-')
            for w in textwrap.wrap(it, 120 - indent - 6, break_long_words=False, break_on_hyphens=False):
                emit(' ' * (indent + 6) + w)


def rarity(mat):
    m = mat.strip().lower()
    return {'artifact': 'Artifact', 'relic': 'Relic', 'special': 'Special'}.get(m, 'Common')


def note_powers(i):
    n = maw[i][16].strip().strip('"') if len(maw[i]) > 16 else ''
    m = re.match(r'\(([^)]*)\)', n)
    s = re.search(r'\(Special Powers?:([^)]*)\)', n)
    out = (m.group(1) if m else '') or (re.sub(r'\s+', ' ', s.group(1)).strip() if s else '')
    return out.strip()


def openyamm_check(i):
    o = ours.get(i)
    m = maw[i]
    if not o:
        return {'exists': False}
    res = []
    if o[2].strip() != m[2].strip():
        res.append('name differs: ours "%s", MAW "%s"' % (o[2].strip(), m[2].strip()))
    if (o[6].strip(), o[7].strip()) != (m[6].strip(), m[7].strip()):
        b = base[i]
        res.append('Mod1/Mod2 ours %s %s (= base MMMerge %s %s), MAW %s %s' % (
            o[6].strip(), o[7].strip(), b[6].strip(), b[7].strip(), m[6].strip(), m[7].strip()))
    if o[4].strip().lower() != m[4].strip().lower():
        res.append('Equip Stat text ours "%s", MAW "%s" (same item type)' % (o[4].strip(), m[4].strip()))
    if o[8].strip() != m[8].strip():
        res.append('material ours "%s", MAW "%s"' % (o[8].strip(), m[8].strip()))
    if o[3].strip() != m[3].strip():
        res.append('Value ours %s, MAW %s' % (o[3].strip(), m[3].strip()))
    return {'exists': True, 'material': o[8].strip(), 'rarity': rarity(o[8]), 'mismatch': res}


def base_model(i):
    c = C[i]
    eq = c['eq']
    d = {}
    if eq in (0, 1, 2):
        two = eq == 1
        if c['artWeap']:
            d['model'] = 'artifact_weapon'
            d['list'] = 'artWeap%s (zzMaw-Items.lua:%s)' % (c['artWeap'], 2330 if c['artWeap'] == '1h' else 2331)
            d['tier'] = 6
            d['tier_flat'] = 16
        else:
            lt = c['ladder']
            d['model'] = 'ladder_weapon'
            d['list'] = 'not in artWeap1h/2h'
            d['tier'] = lt
            d['tier_flat'] = round(16 * (min(max(lt, 1), 6) - 1) / 5, 3)
            d['ladder_run'] = '%d-%d' % tuple(c['ladder_run'])
        d['two_handed'] = two
        d['dice_count'] = int(re.match(r'(\d+)', c['mod1']).group(1))
    else:
        sk = c['skill']
        is_armor_skill = sk in ('Shield', 'Leather', 'Chain', 'Plate', 'Misc')
        ac = 0
        mm = re.match(r'(\d+)', c['mod1'])
        ac = (int(mm.group(1)) if mm else 0) + int(c['mod2'] or 0)
        if c['artArmor']:
            d['model'] = 'artifact_armor'
            d['list'] = 'artArmors (zzMaw-Items.lua:2332)'
        elif is_armor_skill:
            d['model'] = 'flat_ac'
            d['list'] = 'not in artArmors'
        d['printed_ac'] = ac
        if 'refAC' in c:
            d['reference_ac'] = c['refAC']
            if c['refAC_from'] != i:
                d['reference_ac_from'] = c['refAC_from']
    d['slot_mult'] = c['slotMult']
    d['base_multiplier'] = 1
    return d


def emit_entry(i, in_list):
    c = C[i]
    m = maw[i]
    emit('  %d:' % i)
    emit('    name: %s' % q(m[2].strip()))
    emit('    slot: %s' % SLOT.get(c['eq'], 'none'))
    emit('    equip_stat: %s' % q(m[4].strip()))
    emit('    skill: %s' % c['skill'])
    emit('    material: %s' % m[8].strip())
    if in_list:
        n = LIST.count(i)
        emit('    drop_list: {slots: %d, source: "zzMaw-Items.lua:4481"}' % n)
    val = int(m[3].strip() or 0)
    if in_list:
        emit('    chest_reroll: {value: %d, rerolled_if_placed: %s, source: "zzMaw-Items.lua:4523-4535"}' % (
            val, 'true' if val >= 20000 else 'false'))
    oc = openyamm_check(i)
    emit('    openyamm_check:')
    emit('      exists: %s' % ('true' if oc['exists'] else 'false'))
    if oc['exists']:
        emit('      material: %s' % oc['material'])
        emit('      rarity: %s' % oc['rarity'])
        if oc['mismatch']:
            emit_list(6, 'mismatch', oc['mismatch'])
        else:
            emit('      mismatch: none')
    # budget
    p = POWER.get(i)
    if p:
        emit('    budget:')
        if p['stats']:
            emit_flow(6, 'stats', p['stats'])
        if p['skills']:
            emit_flow(6, 'skills', p['skills'])
        if p['flat']:
            emit('      flat: ' + flow(p['flat']))
        emit('      source: "%s:%d-%d"' % (I, p['lines'][0], p['lines'][1]) if p['lines'][0] != p['lines'][1]
             else '      source: "%s:%d"' % (I, p['lines'][0]))
    else:
        emit('    budget: none  # no artifactPower entry (%s:3506-3834)' % I)
    # base
    b = base_model(i)
    emit('    base:')
    for k, v in b.items():
        if isinstance(v, bool):
            v = 'true' if v else 'false'
        elif isinstance(v, str) and not re.match(r'^[A-Za-z_0-9\-]+$', v):
            v = q(v)
        emit('      %s: %s' % (k, v))
    # on hit
    o = ONHIT.get(i)
    if o:
        emit('    on_hit:')
        emit('      damage_kind: %s' % (o['kind'] or 'Phys  # default, no DamageKind'))
        if o['damage']:
            emit('      damage: %s' % o['damage'])
        if o['multvs']:
            emit('      mult_vs: ' + flow(o['multvs']))
        if o['vamp']:
            emit('      vampiric: true  # dead flag, see open questions')
        if o['text']:
            emit('      text: %s' % q(o['text']))
        if i in SPELLS:
            emit_list(6, 'spells', [s.replace('(A:', '(zzzMaw_Artifacts.lua:') for s in SPELLS[i]])
        emit('      source: "%s:%d-%d"' % (A, o['lines'][0], o['lines'][1]))
    if i == 1317:
        emit('    drain: {hp_per_regen_tick: -3, exempt_class: Lich, source: "zzzMaw_Artifacts.lua:604-606,616-625"}')
    if i == 2035:
        emit('    leech: {melee_life_leech_add: -0.1, source: "zzzMaw_Artifacts.lua:612-614; zzMaw-Items.lua:3257-3271"}')
    if i == 543:
        emit('    cycle_of_life: {rule: shared_life, source: "zzzMaw_Artifacts.lua:568-600,616-625"}')
    if i in WEAR:
        t, chk, ln = WEAR[i]
        emit('    wear_requirements:')
        emit('      text: %s' % q(t))
        emit('      check: %s' % q(chk))
        emit('      source: "%s:%s"' % (A, ln))
    if i in BUFFS:
        bf, ln = BUFFS[i]
        emit('    buffs: {powers: %s, source: "%s:%s"}' % (bf, A, ln))
    if i in IMMUNE:
        im, ln = IMMUNE[i]
        emit('    immunities:')
        emit('      monster_bonus: %s' % im)
        emit('      source: "%s:%s"' % (A, ln))
    if i in SPEED:
        emit('    attack_speed: {mod: -20, delay_mult: 0.9, source: "%s:%s"}' % (A, SPEED[i]))
    if i in HP_REGEN:
        emit('    hp_regen: {source: "zzMaw-Items.lua:3836"}')
    if i in SP_REGEN:
        emit('    sp_regen: {source: "zzMaw-Items.lua:3837"}')
    if i in SPELL_BONUS:
        sk, ln = SPELL_BONUS[i]
        emit('    spell_bonus: {skills: [%s], source: "zzMaw-Items.lua:%d"}' % (
            ', '.join('%d %s' % (s, SCHOOL[s]) for s in sk), ln))
    np = note_powers(i)
    if np:
        emit_str(4, 'maw_note', np)
    emit_list(4, 'notes', NOTES.get(i, []))


emit_entries = emit_entry

HEADER = open(D + 'artifacts/header.yml').read().rstrip('\n').split('\n')
lines.extend(HEADER)
emit('')
emit('artifacts:  # %d unique ids from mawArtifacts (zzMaw-Items.lua:4481; 104 entries, 533 twice)' % len(UNIQUE))
for i in UNIQUE:
    emit_entry(i, True)
emit('')
OTHER = [516, 532, 538, 539, 540, 541, 543, 1341, 1347, 1348, 2020]
LIST_ONLY = [1340, 1342, 1343, 1344, 1345, 1346, 1349, 1350, 1351, 1352, 1353, 1354, 2118, 866, 867, 1666, 1667]
for _i in LIST_ONLY:
    _n = ['Not in mawArtifacts and in no behaviour table. Its only artifact rule is membership in '
          + ('artArmors (level AC growth)' if C[_i]['artArmor'] else 'artWeap1h/2h (tier-6 damage)')
          + ', which makes it IsArtifactItem: level = party total level.']
    if _i == 2118:
        _n.append('Outside the IsArtifactId bands; material column 5.')
    if _i in (866, 867, 1666, 1667):
        _n.append('ancientWeapons: excluded from IsEnchantableItem; tooltip shows artifact base stats '
                  '(Tooltip.lua:538).')
    if _i in (867, 1667):
        _n.append('EquipStat is Weapon (one-handed) but listed in artWeap2h: two_handed false in the damage model.')
    NOTES[_i] = _n
OTHER += LIST_ONLY
emit('other_artifact_rules:  # ids with rules in the behaviour tables that are NOT in mawArtifacts')
for i in OTHER:
    emit_entry(i, False)
lines.extend(open(D + 'artifacts/tail.yml').read().rstrip('\n').split('\n'))
open(OUT, 'w').write('\n'.join(lines) + '\n')
print('written', len(lines), 'lines;', len(UNIQUE), 'artifacts;', len(OTHER), 'other')
