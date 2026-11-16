"""Builds the harness spec: concrete solo builds per class, stage (character level), difficulty and monster level.
Every rule here is taken from the C++ (file references in comments); the harness then asks the engine for the numbers."""
import math, json, sys, yaml

# --- experience (MawExperienceCurve.cpp) -------------------------------------------------------------------------
def step(L): return 1000*L*max(1+(L-100)*0.005, 1)
EXP = [0.0]*2002
for l in range(2, 2002): EXP[l] = EXP[l-1] + step(l-1)
def exp_for(L):
    w = int(math.floor(L)); return EXP[w] + (L-w)*step(w)
def level_for(x):
    lo, hi = 1.0, 2000.0
    for _ in range(80):
        mid = (lo+hi)/2
        lo, hi = (mid, hi) if exp_for(mid) < x else (lo, mid)
    return lo

# --- skill points (mawLevelUpPoints) and raise costs (mawSharedRaiseCost, mawIsSharedCostSkill) --------------------
def level_up_points(L): return sum(5 + i//10 for i in range(2, L+1))
WEAPONS = {'Staff', 'Sword', 'Dagger', 'Axe', 'Spear', 'Bow', 'Mace', 'Blaster'}
MAGIC = {'FireMagic', 'AirMagic', 'WaterMagic', 'EarthMagic', 'SpiritMagic', 'MindMagic', 'BodyMagic', 'LightMagic',
         'DarkMagic', 'DarkElfAbility', 'VampireAbility'}
HYBRID_LINES = {'Seraphim', 'Angel', 'Archangel', 'DeathKnight', 'DeathLord', 'LichKing', 'Shaman', 'Sekhem', 'Marabou',
                'Thief', 'Rogue', 'Assassin', 'Spy'}
LEVEL_CAP = {'Alchemy': 60, 'Cover': 30, 'ManaShield': 50, 'Retaliation': 50}   # mawSkillLevelCap

def shared(skill, cls):
    return skill in MAGIC or (cls not in HYBRID_LINES and skill in WEAPONS)

def raise_cost(skills, name, cls):
    new = skills[name] + 1
    if not shared(name, cls) or new > 1000:
        return new
    n = sum(1 for k, v in skills.items() if k != name and shared(k, cls) and v >= new)
    return math.ceil(new/(1+n))

def allocate(cls, budget, weights, fixed, caps=None):
    caps = caps or {}
    skills = {k: 1 for k in list(weights) + list(fixed)}
    spent = 0
    for k, target in fixed.items():           # fixed skills (Alchemy) first
        while skills[k] < target:
            c = raise_cost(skills, k, cls)
            if spent + c > budget: break
            spent += c; skills[k] += 1
    while True:
        cands = [k for k in weights if skills[k] < min(LEVEL_CAP.get(k, 10**6), caps.get(k, 10**6))]
        if not cands: break
        k = min(cands, key=lambda k: skills[k]/weights[k])
        c = raise_cost(skills, k, cls)
        if spent + c > budget: break
        spent += c; skills[k] += 1
    return skills, spent

LETTER = {'N': 1, 'E': 2, 'M': 3, 'G': 4}
def thresholds(mode):   # mawMasteryRequiredLevel: E/M/G
    return {'free': (4, 7, 10), 'horizontal': (6, 12, 20), 'insanity': (8, 16, 25), 'madness': (10, 24, 40)}[mode]
SOLO_MASTERY = {'IdentifyItem', 'Merchant', 'RepairItem', 'Perception', 'DisarmTraps', 'IdentifyMonster', 'Alchemy'}

def mastery(skill, level, cap, mode):
    if skill in SOLO_MASTERY:   # a party of one masters these at 1/4/7/10 whatever the class (MawSoloMasterySkills)
        return 4 if level >= 10 else 3 if level >= 7 else 2 if level >= 4 else 1
    e, m, g = thresholds(mode)
    best = 1 if level >= e else 1
    for mm, need in ((2, e), (3, m), (4, g)):
        if level >= need: best = mm
    return min(best, cap)

# --- caps (from the harness's "solo caps" dump of the MAW tables) --------------------------------------------------
CAPS = {}
for line in open(sys.argv[1]):
    if line.startswith('CAPS '):
        head, rest = line[5:].split(':', 1)
        cls, _, race = head.split()
        CAPS[(cls, int(race))] = {kv.split('=')[0]: LETTER[kv.split('=')[1]] for kv in rest.split()}

# --- stages ----------------------------------------------------------------------------------------------------------
STAGES = [10, 50, 200, 500]
def pace_level(Lc): return level_for(exp_for(Lc)/5)   # a solo's level bank: a fifth of its experience
ALCHEMY = {10: 4, 50: 10, 200: 30, 500: 60}
GEAR = {10: ('uncommon', 0), 50: ('epic', 10), 200: ('ancient', 40), 500: ('legendary', 100)}   # crafted = level/5

def potion_power(M, alchemy):
    """Best reagent from map drops: drop level min(map level, total level)/3 (MawItemRules::rollPlainItem), top
    reagents base 30 (items_patch), power base(1 + IL/80) + 0.75 IL (mawReagentBasePower); Master adds half the Alchemy
    level, GM all of it (reagentPower); catalysts reach Alchemy x mastery / 2 (catalystMixPower)."""
    il = round(M/3)
    m = 4 if alchemy >= 10 else 3 if alchemy >= 7 else 2 if alchemy >= 4 else 1
    reagent = math.floor(30*(1 + il*0.25/20) + 0.75*il)
    reagent += alchemy if m == 4 else alchemy/2 if m == 3 else 0
    return int(min(max(reagent, alchemy*m/2), 500))

def potion_auras(Lc, P):
    a = {5: P, 51: P, 46: P, 38: P}                       # Haste, Heroism, Bless, Stone Skin (aura potions)
    if Lc >= 50:
        a.update({17: P, 3: P, 14: P, 25: P, 36: P, 58: P, 69: P})   # Shield; Elemental and Self Resistance
    if Lc >= 200:
        a[83] = P                                          # Divine Blessing (Day of the Gods)
    return a

def stats(kind, Lc, P):
    pure = 20*math.floor(P/50) if Lc >= 200 else 0      # Pure Power / Wisdom / Resilience, +20 per 50 power
    if kind == 'melee':
        s = dict(might=30, intellect=10, personality=10, endurance=25, accuracy=20, speed=20, luck=15)
    elif kind == 'caster':
        s = dict(might=10, intellect=30, personality=25, endurance=20, accuracy=15, speed=20, luck=15)
    else:   # hybrid
        s = dict(might=25, intellect=20, personality=20, endurance=20, accuracy=15, speed=20, luck=15)
    return {k: v + pure for k, v in s.items()}

# --- builds ----------------------------------------------------------------------------------------------------------
# name, class, race, stat kind, weights, gear, extra case fields
B = []
def build(key, label, cls, race, kind, weights, gear, **extra):
    B.append(dict(key=key, label=label, cls=cls, race=race, kind=kind, weights=weights, gear=gear, extra=extra))

build('knight_sns', 'Champion, sword + shield', 'Champion', 0, 'melee',
      {'Sword': 1.0, 'Armsmaster': 1.0, 'Shield': 0.7, 'PlateArmor': 0.7, 'Bodybuilding': 0.7},
      dict(main='Sword', off='Shield', armor='PlateArmor'))
build('knight_2h', 'Champion, two-handed axe', 'Champion', 0, 'melee',
      {'Axe': 1.0, 'Armsmaster': 1.0, 'PlateArmor': 0.7, 'Bodybuilding': 0.8},
      dict(main='Axe', two_handed=True, armor='PlateArmor'))
build('troll_knight', 'Champion (Troll race), sword + shield', 'Champion', 4, 'melee',
      {'Sword': 1.0, 'Armsmaster': 1.0, 'Shield': 0.6, 'PlateArmor': 0.6, 'Bodybuilding': 0.6, 'Regeneration': 0.6},
      dict(main='Sword', off='Shield', armor='PlateArmor'))
build('vamp_knight', 'Black Knight (Vampire race), two-handed sword', 'BlackKnight', 1, 'melee',
      {'Sword': 1.0, 'Armsmaster': 1.0, 'PlateArmor': 0.7, 'Bodybuilding': 0.8},
      dict(main='Sword', two_handed=True, armor='PlateArmor'))
build('minotaur_dual', 'Minotaur Lord, two two-handed axes', 'MinotaurLord', 3, 'melee',
      {'Axe': 1.0, 'Armsmaster': 0.8, 'Bodybuilding': 0.8, 'ChainArmor': 0.6, 'Regeneration': 0.4},
      dict(main='Axe', two_handed=True, off='Axe', off_two_handed=True, armor='ChainArmor'))
build('minotaur_one', 'Minotaur Lord, one two-handed axe', 'MinotaurLord', 3, 'melee',
      {'Axe': 1.0, 'Armsmaster': 0.8, 'Bodybuilding': 0.8, 'ChainArmor': 0.6, 'Regeneration': 0.4},
      dict(main='Axe', two_handed=True, armor='ChainArmor'))
build('dk_minotaur', 'Lich King (Minotaur race), two-handed axe', 'LichKing', 3, 'melee',
      {'Axe': 1.0, 'BodyMagic': 0.7, 'WaterMagic': 0.7, 'DarkMagic': 0.7, 'PlateArmor': 0.6, 'Bodybuilding': 0.4,
       'Regeneration': 0.4},
      dict(main='Axe', two_handed=True, armor='PlateArmor'))
build('dk_vampire', 'Lich King (Vampire race), two-handed axe', 'LichKing', 1, 'melee',
      {'Axe': 1.0, 'BodyMagic': 0.7, 'WaterMagic': 0.7, 'DarkMagic': 0.7, 'PlateArmor': 0.6, 'Bodybuilding': 0.4,
       'Regeneration': 0.4},
      dict(main='Axe', two_handed=True, armor='PlateArmor'))
build('dk_minotaur_dual', 'Lich King (Minotaur race), two two-handed axes', 'LichKing', 3, 'melee',
      {'Axe': 1.0, 'BodyMagic': 0.7, 'WaterMagic': 0.7, 'DarkMagic': 0.7, 'PlateArmor': 0.6, 'Bodybuilding': 0.4,
       'Regeneration': 0.4},
      dict(main='Axe', two_handed=True, off='Axe', off_two_handed=True, armor='PlateArmor'))
build('minotaur_knight_dual', 'Champion (Minotaur race), two two-handed axes', 'Champion', 3, 'melee',
      {'Axe': 1.0, 'Armsmaster': 1.0, 'PlateArmor': 0.6, 'Bodybuilding': 0.8},
      dict(main='Axe', two_handed=True, off='Axe', off_two_handed=True, armor='PlateArmor'))
build('troll', 'War Troll, mace + shield', 'WarTroll', 4, 'melee',
      {'Mace': 1.0, 'Regeneration': 1.0, 'Bodybuilding': 0.8, 'LeatherArmor': 0.6, 'Armsmaster': 0.5, 'Shield': 0.4},
      dict(main='Mace', off='Shield', armor='LeatherArmor'))
build('troll_staff', 'War Troll, two-handed staff', 'WarTroll', 4, 'melee',
      {'Staff': 1.0, 'Regeneration': 1.0, 'Bodybuilding': 0.8, 'LeatherArmor': 0.6, 'Armsmaster': 0.5},
      dict(main='Staff', two_handed=True, armor='LeatherArmor'))
build('nosferatu', 'Nosferatu (Vampire), two daggers', 'Nosferatu', 1, 'melee',
      {'Dagger': 1.0, 'Armsmaster': 0.8, 'Regeneration': 0.8, 'Bodybuilding': 0.5, 'LeatherArmor': 0.5},
      dict(main='Dagger', off='Dagger', armor='LeatherArmor'))
build('dragon', 'Great Wyrm (Dragon), bite + breath', 'GreatWyrm', 5, 'melee',
      {'DragonAbility': 1.0, 'Regeneration': 0.9, 'Bodybuilding': 0.8, 'Unarmed': 0.6},
      dict(dragon_slots=True))
build('archer', 'Master Archer, bow', 'MasterArcher', 0, 'melee',
      {'Bow': 1.0, 'ChainArmor': 0.6, 'Bodybuilding': 0.6, 'Armsmaster': 0.4},
      dict(main='Sword', bow=True, armor='ChainArmor'))
build('seraph', 'Archangel (Seraph), two-handed sword + shield', 'Archangel', 0, 'hybrid',
      {'Sword': 1.0, 'LightMagic': 0.8, 'BodyMagic': 0.6, 'SpiritMagic': 0.6, 'PlateArmor': 0.5, 'Shield': 0.4,
       'Bodybuilding': 0.3},
      dict(main='Sword', two_handed=True, off='Shield', armor='PlateArmor'))
build('assassin', 'Assassin, two daggers', 'Assassin', 0, 'melee',
      {'Dagger': 1.0, 'Dodging': 0.8, 'EarthMagic': 0.7, 'FireMagic': 0.5, 'AirMagic': 0.5, 'WaterMagic': 0.5,
       'LeatherArmor': 0.6, 'Bodybuilding': 0.3},
      dict(main='Dagger', off='Dagger', armor='LeatherArmor'))
build('monk', 'Master (Monk), staff + Unarmed', 'Master', 0, 'melee',
      {'Staff': 1.0, 'Unarmed': 0.8, 'Dodging': 0.6, 'Bodybuilding': 0.7, 'LeatherArmor': 0.4, 'Regeneration': 0.3},
      dict(main='Staff', two_handed=True, armor='LeatherArmor'))
build('archmage', 'Arch Mage, Fire', 'ArchMage', 0, 'caster',
      {'FireMagic': 1.0, 'AirMagic': 0.5, 'Learning': 0.8, 'Meditation': 0.6, 'ManaShield': 0.7, 'Bodybuilding': 0.5},
      dict(main='Staff', two_handed=True, armor='LeatherArmor'), learn_school_spells=True,
      spells=['Incinerate', 'Fireball', 'Fire Bolt', 'Lightning Bolt'], stage_caps={'Learning': {10: 2, 50: 8, 200: 15, 500: 35}})
build('elementalist', 'Master of Elements, four elements', 'MasterOfElements', 0, 'caster',
      {'FireMagic': 1.0, 'AirMagic': 1.0, 'WaterMagic': 1.0, 'EarthMagic': 1.0, 'ManaShield': 0.5, 'Meditation': 0.3},
      dict(main='Staff', two_handed=True, armor='LeatherArmor'), learn_school_spells=True,
      spells=['Incinerate', 'Fireball', 'Fire Bolt', 'Lightning Bolt'], elemental_stacks=5)
build('shaman', 'Marabou (Shaman), axe + seven schools', 'Marabou', 0, 'hybrid',
      {'Axe': 1.0, 'FireMagic': 0.6, 'AirMagic': 0.6, 'WaterMagic': 0.6, 'EarthMagic': 0.6, 'SpiritMagic': 0.6,
       'MindMagic': 0.6, 'BodyMagic': 0.6, 'LeatherArmor': 0.5},
      dict(main='Axe', two_handed=True, armor='LeatherArmor'), learn_school_spells=True, spells=['Lightning Bolt'])
build('priest', 'Priest of Light', 'PriestLight', 0, 'caster',
      {'LightMagic': 1.0, 'BodyMagic': 0.7, 'SpiritMagic': 0.5, 'Learning': 0.8, 'Meditation': 0.4, 'ManaShield': 0.4,
       'ChainArmor': 0.4},
      dict(main='Mace', off='Shield', armor='ChainArmor'), learn_school_spells=True, spells=['Light Bolt'],
      stage_caps={'Learning': {10: 2, 50: 8, 200: 15, 500: 35}})

DIFFS = [('normal', 'normal:free', 'free'), ('maw', 'maw:free', 'free'), ('hard', 'hard:free', 'free'),
         ('hell', 'hell:free', 'free'), ('nightmare', 'nightmare:free', 'free'),
         ('doom', 'nightmare:doom:horizontal', 'horizontal'), ('insanity', 'nightmare:road_to_insanity:horizontal', 'insanity'),
         ('madness', 'nightmare:beyond_madness:horizontal', 'madness')]

cases = []; meta = {}
for b in B:
    caps = CAPS[(b['cls'], b['race'])]
    for Lc in STAGES:
        Mp = max(1, round(pace_level(Lc)))
        alchemy = ALCHEMY[Lc]
        P = potion_power(Mp, alchemy)
        trans = 5*(P//50)**2 + 15*(P//50) if Lc >= 200 else 0
        budget = level_up_points(Lc) + trans
        weights = {k: v for k, v in b['weights'].items() if caps.get(k, 0) > 0}
        stage_caps = {k: v[Lc] for k, v in b['extra'].get('stage_caps', {}).items()}
        skills, spent = allocate(b['cls'], budget, weights, {'Alchemy': alchemy}, stage_caps)
        rarity, crafted = GEAR[Lc]
        for dkey, opts, mode in DIFFS:
            sk = {k: [int(v), mastery(k, v, caps.get(k, 0), mode)] for k, v in skills.items() if caps.get(k, 0) > 0
                  or k in SOLO_MASTERY}
            for mtag, M in (('pace', Mp), ('par', Lc)):
                spells = b['extra'].get('spells', [None])
                for spell in spells:
                    cid = f"{b['key']}|{Lc}|{dkey}|{mtag}" + (f"|{spell}" if spell else '')
                    PORTRAIT = {0: 1, 1: 13, 3: 21, 4: 23, 5: 25}
                    case = dict(id=cid, portrait=PORTRAIT[b['race']], options=opts, **{'class': b['cls']}, race=b['race'], level=Lc, monster_level=M, bank_level=Mp,
                                stats=stats(b['kind'], Lc, P), skills=sk,
                                gear=dict(level=Mp, rarity=rarity, crafted_power=crafted, seed=7, **b['gear']),
                                potions=dict(auras=potion_auras(Lc, P), **({'regen': P} if Lc >= 50 else {})), potion_power=P)
                    if b['extra'].get('learn_school_spells'): case['learn_school_spells'] = True
                    if spell: case['quick_spell'] = spell
                    if b['extra'].get('elemental_stacks'): case['elemental_stacks'] = b['extra']['elemental_stacks']
                    cases.append(case)
                    meta[cid] = dict(build=b['key'], label=b['label'], Lc=Lc, diff=dkey, mtag=mtag, M=M, Mp=Mp, P=P,
                                     budget=budget, spent=spent, skills=sk, spell=spell, alchemy=alchemy)

yaml.safe_dump({'world': 'mm8', 'cases': cases}, open(sys.argv[2], 'w'), default_flow_style=None, width=200)
json.dump(meta, open(sys.argv[3], 'w'))
print(len(cases), 'cases;', 'pace levels', {Lc: round(pace_level(Lc), 1) for Lc in STAGES},
      'potion power', {Lc: potion_power(round(pace_level(Lc)), ALCHEMY[Lc]) for Lc in STAGES},
      'skill points', {Lc: level_up_points(Lc) for Lc in STAGES})
