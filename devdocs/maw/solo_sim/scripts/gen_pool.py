"""Cases for the playthrough-loot gear: each build at each stage, difficulty and seed, gear chosen from that run's loot.

Stages are the route's snapshots: the solo's level stages (prep/_common.STAGES; 1 is the start, before the first map)
and the end of the run (END). The party reference run (route/out_<dk>_party.jsonl, prep/7_party_routes.py) gives the
same stages for a party of five (PARTY): ids start with "party:", the members share the loot and the materials, and
their cases carry party_count 5. Skill, alchemy and stage tables follow the character's actual level. Solo builds
train under Lone Discipline (Bodybuilding and Regeneration open to every class); the party's members do not."""
import json, statistics, sys, yaml, copy
from simdir import S, CODE
sys.argv=['gen.py', S+'/caps.txt', '/dev/null', '/dev/null']
src=open(CODE+'/gen.py').read().split("DIFFS = [")[0]
exec(src)   # builds, allocator, stats, potions from gen.py
for line in open(S+'/caps2.txt'):
    if line.startswith('CAPS '):
        head, rest = line[5:].split(':', 1); cls, _, race = head.split()
        CAPS[(cls, int(race))] = {kv.split('=')[0]: LETTER[kv.split('=')[1]] for kv in rest.split()}
# Class ladders (class_extra.txt and MAW's patch): base, first promotion, final.
LADDER = {'knight_sns': ('Knight', 'Cavalier'), 'knight_2h': ('Knight', 'Cavalier'), 'troll_knight': ('Knight', 'Cavalier'),
          'vamp_knight': ('Knight', 'Cavalier'), 'minotaur_dual': ('Minotaur', None), 'minotaur_one': ('Minotaur', None),
          'dk_minotaur': ('DeathKnight', 'DeathLord'), 'dk_vampire': ('DeathKnight', 'DeathLord'),
          'dk_minotaur_dual': ('DeathKnight', 'DeathLord'), 'minotaur_knight_dual': ('Knight', 'Cavalier'),
          'troll': ('Troll', None), 'troll_staff': ('Troll', None), 'nosferatu': ('Vampire', None), 'dragon': ('Dragon', None),
          'archer': ('Archer', 'WarriorMage'), 'seraph': ('Seraphim', 'Angel'), 'assassin': ('Thief', 'Rogue'),
          'monk': ('Monk', 'Initiate'), 'archmage': ('Sorcerer', 'Wizard'), 'elementalist': ('Elementalist', 'ElementalAdept'),
          'shaman': ('Shaman', 'Sekhem'), 'priest': ('Cleric', 'Priest')}
MAPS = json.load(open(S+'/inv/maps.json'))
FIRST_PROMOTION_SHARE, FINAL_PROMOTION_SHARE = 0.15, 0.4
DIFFS = {'normal': ('normal:free', 'free'), 'maw': ('maw:free', 'free'), 'hard': ('hard:free', 'free'),
         'hell': ('hell:free', 'free'), 'nightmare': ('nightmare:free', 'free'),
         'doom': ('nightmare:doom:horizontal', 'horizontal'),
         'insanity': ('nightmare:road_to_insanity:horizontal', 'insanity'),
         'madness': ('nightmare:beyond_madness:horizontal', 'madness')}
PORTRAIT = {0: 1, 1: 13, 3: 21, 4: 23, 5: 25}
MERIT = {'archer': 'bow', 'dragon': 'breath', 'archmage': 'spell', 'elementalist': 'spell', 'priest': 'spell'}
# The stage of a run's end snapshot (every run has one; runs end at different levels).
END = 9999
# Lone Discipline, the solo run's innate rule (MawSkillRules::masteryCap): every class may train Bodybuilding to Expert
# at once, Master after its first promotion and Grandmaster after the final one, and Regeneration to Expert at once
# and Master after the final promotion. A solo then trains them: Regeneration at this weight (the user: "the start
# would always be: get Regeneration"), Bodybuilding at least as the natural Grandmaster classes do when its cap is
# lifted. LONE=0 in the environment gives the cases without it (the 2026-11-15 first curve run).
import os
LONE_DISCIPLINE = os.environ.get('LONE', '1') != '0'
REGENERATION_WEIGHT, LIFTED_BODYBUILDING_WEIGHT = 0.6, 0.8
# The party of five the solo is compared against: two fighters, an archer, a healer and a mage.
PARTY = ['knight_sns', 'knight_2h', 'archer', 'priest', 'archmage']


def interp(points, level):
    """Piecewise-linear value of a stage table (level -> value) at any level; flat outside its ends."""
    keys = sorted(points)
    if level <= keys[0]: return points[keys[0]]
    if level >= keys[-1]: return points[keys[-1]]
    for lo, hi in zip(keys, keys[1:]):
        if lo <= level <= hi:
            return points[lo] + (points[hi] - points[lo])*(level - lo)/(hi - lo)


ALCHEMY_AT = {1: 1, **ALCHEMY}


def wanted_kinds(gear, kinds):
    """The pool's item kinds (equip stat|skill group) a build's gear plan can wear."""
    want = {k for k in kinds if k.split('|')[0] in ('Helm', 'Belt', 'Cloak', 'Gauntlets', 'Boots', 'Amulet', 'Ring')}
    def weapon(skill, two):
        return {f'Weapon2|{skill}'} if two else {f'Weapon|{skill}', f'Weapon1or2|{skill}'}
    if gear.get('main'): want |= weapon(gear['main'], gear.get('two_handed', False))
    if gear.get('off') == 'Shield': want.add('Shield|Shield')
    elif gear.get('off'): want |= weapon(gear['off'], gear.get('off_two_handed', False))
    if gear.get('bow'): want.add('Missile|Bow')
    if gear.get('armor'): want.add('Armor|' + gear['armor'].replace('Armor', ''))
    return want & set(kinds)


def party_draft(pool):
    """The party shares the loot: every kind several members can wear is dealt round among them."""
    builds = {b['key']: b for b in B}
    wants = [wanted_kinds(builds[key]['gear'], pool) for key in PARTY]
    shares = [[] for _ in PARTY]
    for kind, items in pool.items():
        takers = [i for i, w in enumerate(wants) if kind in w]
        for n, item in enumerate(items):
            if takers:
                shares[takers[n % len(takers)]].append(item)
    return shares


cases = []; meta = {}; fightsOut = {}
import collections
for dk, (opts, mode) in DIFFS.items():
    totals = collections.Counter(MAPS[m['file']]['continent'] for m in json.load(open(f'{S}/route/route_{dk}.json'))['maps'])
    for party in (False, True):
        path = f'{S}/route/out_{dk}' + ('_party' if party else '') + '.jsonl'
        try:
            lines = open(path).read().splitlines()
        except FileNotFoundError:
            continue
        snaps = {}; trajs = {}
        for line in lines:
            d = json.loads(line)
            if d['kind'] == 'snapshot': snaps[(d['seed'], d['stage'] if d['stage'] > 0 else END)] = d
            if d['kind'] == 'trajectory': trajs[d['seed']] = d['maps']
        tag = dk + ('_party' if party else '')
        for (seed, Lc), snap in snaps.items():
            if seed not in trajs:   # a run still being written
                continue
            Lreal = max(1, int(snap['char_level']))
            traj = trajs[seed][:snap['maps_cleared']]
            recent = [m[1] for m in traj[-10:] if m[1] < 1e7]
            # Promotions: a continent's first-tier quest once 15 % of its maps are cleared, its final quest at 40 %.
            done = collections.Counter(MAPS[m[0]]['continent'] for m in traj)
            shares = {c: done[c] / totals[c] for c in totals}
            promoted = sum(1 for v in shares.values() if v >= FINAL_PROMOTION_SHARE)
            firstTier = any(v >= FIRST_PROMOTION_SHARE for v in shares.values())
            grid = sorted({a[1] for f in snap.get('fights', []) for a in f['actors']})
            fightsOut[f'{tag}|{seed}|{Lc}'] = snap.get('fights', [])
            upcoming = [f['level'] for f in snap.get('fights', []) if f.get('next')]
            M = max(1, round(statistics.median(recent))) if recent else max(1, round(min(upcoming or [1])))
            bank = max(1, round(snap['bank_total']))
            start = snap['maps_cleared'] == 0
            pools = party_draft(snap['pool']) if party else None
            whole = [it for kind in snap['pool'].values() for it in kind]
            materials = {k: v//5 for k, v in snap['materials'].items()} if party else snap['materials']
            alchemy = round(interp(ALCHEMY_AT, Lreal))
            P = potion_power(M, alchemy)
            for b in B:
                if party and b['key'] not in PARTY: continue
                base, mid = LADDER[b['key']]
                cls = b['cls'] if promoted >= 1 else (mid if firstTier and mid else base)
                caps = dict(CAPS[(cls, b['race'])])
                weights = dict(b['weights'])
                lone = None
                if LONE_DISCIPLINE and not party:
                    step = 2 if promoted >= 1 else 1 if cls != base else 0
                    lone = {'Bodybuilding': 4 if step == 2 else 3 if step == 1 else 2, 'Regeneration': 3 if step == 2 else 2}
                    if lone['Bodybuilding'] > caps.get('Bodybuilding', 0):
                        weights['Bodybuilding'] = max(weights.get('Bodybuilding', 0), LIFTED_BODYBUILDING_WEIGHT)
                    weights['Regeneration'] = max(weights.get('Regeneration', 0), REGENERATION_WEIGHT)
                    for skill, cap in lone.items():
                        caps[skill] = max(caps.get(skill, 0), cap)
                trans = 5*(P//50)**2 + 15*(P//50) if Lreal >= 200 else 0
                budget = level_up_points(Lreal) + trans
                weights = {k: v for k, v in weights.items() if caps.get(k, 0) > 0}
                stage_caps = {k: round(interp(v, Lreal)) for k, v in b['extra'].get('stage_caps', {}).items()}
                # A party has one alchemist; its members do not each pay for Alchemy.
                skills, spent = allocate(cls, budget, weights, {} if party else {'Alchemy': alchemy}, stage_caps)
                solo_mastery = set() if party else SOLO_MASTERY
                sk = {k: [int(v), mastery(k, v, caps.get(k, 0), mode) if k not in solo_mastery else
                          (4 if v >= 10 else 3 if v >= 7 else 2 if v >= 4 else 1)]
                      for k, v in skills.items() if caps.get(k, 0) > 0 or k in solo_mastery}
                for spell in b['extra'].get('spells', [None]):
                    cid = ('party:' if party else '') + f"{b['key']}|{Lc}|{dk}|s{seed}" + (f"|{spell}" if spell else '')
                    case = dict(id=cid, options=opts, **{'class': cls}, promotion_worlds=promoted, level_grid=grid, race=b['race'],
                                level=Lreal, monster_level=M, bank_level=bank, portrait=PORTRAIT[b['race']],
                                stats=stats(b['kind'], Lreal, P), skills=sk, merit=MERIT.get(b['key'], 'melee'),
                                potions=dict(auras=potion_auras(Lreal, P), **({'regen': P} if Lreal >= 50 else {})), potion_power=P)
                    if start:
                        # The start: a common weapon and armour of level 1, no jewellery, nothing crafted.
                        case['gear'] = dict(b['gear'], level=1, rarity='common', seed=seed, basic_only=True)
                    else:
                        case.update(gear=dict(b['gear']), pool=pools[PARTY.index(b['key'])] if party else whole, materials=materials)
                    if party: case['party_count'] = 5
                    if lone: case['cap_raise'] = lone
                    if b['extra'].get('learn_school_spells'): case['learn_school_spells'] = True
                    if spell: case['quick_spell'] = spell
                    if b['extra'].get('elemental_stacks'): case['elemental_stacks'] = b['extra']['elemental_stacks']
                    if MERIT.get(b['key']) == 'spell' and not spell: continue
                    cases.append(case)
                    meta[cid] = dict(build=b['key'], label=b['label'], cls=cls, promoted=promoted, Lc=Lc, actual_level=Lreal, diff=dk, seed=seed, M=M, bank=bank, P=P,
                                     skills=sk, spell=spell, maps=snap['maps_cleared'], kills=snap['kills'], chests=snap['chests'], party=party, tag=tag,
                                     items_seen=snap['items_seen'], materials=sum(snap['materials'].values()), mtag='route')
json.dump(meta, open(S+'/pool_meta.json', 'w'))
json.dump(fightsOut, open(S+'/fights.json', 'w'))
# One spec file per difficulty, run kind and seed, for parallel harness runs.
by = {}
for c in cases:
    m = meta[c['id']]
    by.setdefault(f"{m['tag']}_s{m['seed']}", []).append(c)
for name, cs in by.items():
    yaml.safe_dump({'world': 'mm8', 'cases': cs}, open(f'{S}/pool_{name}.yml', 'w'), default_flow_style=True, width=100000)
print(len(cases), 'cases in', len(by), 'spec files')
