"""Talent variants of the gear cases (pool_<difficulty>.yml from gen_pool.py) for the harness.

Variants (talents_v2.py):
  v1   the current tree, points from levels only; the solo run's passives through MAW's rules ("solo" option)
  v2   tree v2: points from levels, Lone Discipline (Bodybuilding cap), keystones by level
The harness applies what the game code has: the passives (Weapon Training, Marksman, Attunement, Resolve, Mana Font)
and the Bodybuilding mastery. talentfight.py adds the rest. Writes pool_<variant>_<difficulty>.yml.
"""
import json, sys, yaml
from simdir import S, CODE
import talents_v2 as T

sys.argv = ['gen.py', S + '/caps.txt', '/dev/null', '/dev/null']
src = open(CODE + '/gen.py').read().split("DIFFS = [")[0]
exec(src)   # CAPS, mastery(), thresholds()
for line in open(S + '/caps2.txt'):
    if line.startswith('CAPS '):
        head, rest = line[5:].split(':', 1); cls, _, race = head.split()
        CAPS[(cls, int(race))] = {kv.split('=')[0]: LETTER[kv.split('=')[1]] for kv in rest.split()}

meta = json.load(open(S + '/pool_meta.json'))
BUILD = {b['key']: b for b in B}


def replan(c, m, dk, bb_cap):
    """gen_pool's skill plan for this case again, with the Bodybuilding cap raised and its weight at least 0.8."""
    b = BUILD[m['build']]
    caps = dict(CAPS[(c['class'], c['race'])]); caps['Bodybuilding'] = bb_cap
    Lc, P = m['Lc'], m['P']
    alchemy = ALCHEMY[Lc]
    trans = 5*(P//50)**2 + 15*(P//50) if Lc >= 200 else 0
    budget = level_up_points(m['actual_level']) + trans
    weights = {k: v for k, v in b['weights'].items() if caps.get(k, 0) > 0}
    weights['Bodybuilding'] = max(weights.get('Bodybuilding', 0), 0.8)
    stage_caps = {k: v[Lc] for k, v in b['extra'].get('stage_caps', {}).items()}
    skills, _ = allocate(c['class'], budget, weights, {'Alchemy': alchemy}, stage_caps)
    return {k: [int(v), mastery(k, v, caps.get(k, 0), MODE[dk])] for k, v in skills.items()
            if caps.get(k, 0) > 0 or k in SOLO_MASTERY}
MODE = {'normal': 'free', 'maw': 'free', 'hard': 'free', 'hell': 'free', 'nightmare': 'free', 'doom': 'horizontal',
        'insanity': 'insanity', 'madness': 'madness'}
BASE_CLASS = {'knight_sns': 'Knight', 'knight_2h': 'Knight', 'troll_knight': 'Knight', 'vamp_knight': 'Knight',
              'minotaur_dual': 'Minotaur', 'minotaur_one': 'Minotaur', 'dk_minotaur': 'DeathKnight',
              'dk_vampire': 'DeathKnight', 'dk_minotaur_dual': 'DeathKnight', 'minotaur_knight_dual': 'Knight',
              'troll': 'Troll', 'troll_staff': 'Troll', 'nosferatu': 'Vampire', 'dragon': 'Dragon', 'archer': 'Archer',
              'seraph': 'Seraphim', 'assassin': 'Thief', 'monk': 'Monk', 'archmage': 'Sorcerer',
              'elementalist': 'Elementalist', 'shaman': 'Shaman', 'priest': 'Cleric'}
VARIANTS = {'v1': 'v1', 'v2': 'v2'}
diffs = sys.argv_diffs if hasattr(sys, 'argv_diffs') else list(MODE)
summary = {}
for dk in diffs:
    spec = yaml.safe_load(open(f'{S}/pool_{dk}.yml'))
    for var, tree in VARIANTS.items():
        cases = []
        for c in spec['cases']:
            m = meta[c['id']]
            c = dict(c)
            alloc = T.allocation(m['build'], m['actual_level'], m['skills'], tree)
            c['options'] = c['options'] + ':solo'
            c['talents'] = {k: v for k, v in alloc['ranks'].items() if k in T.HARNESS_PASSIVES}
            if tree == 'v2' and 'Bodybuilding' in c['skills']:
                race = c['race']
                class_cap = CAPS.get((c['class'], race), {}).get('Bodybuilding', 0)
                promoted = m['promoted'] >= 1
                first_tier = c['class'] != BASE_CLASS[m['build']]
                cap = T.bodybuilding_cap(promoted, first_tier, class_cap)
                if cap > class_cap:
                    # With Bodybuilding open the solo plans its skill points again with Bodybuilding weighted like
                    # the natural Grandmaster classes (0.8): the levels come out of its other skills, not for free.
                    c['skills'] = replan(c, m, dk, cap)
                    c['cap_raise'] = {'Bodybuilding': cap}
            cases.append(c)
            summary.setdefault(var, {})[m['build']] = alloc
        yaml.safe_dump({'world': 'mm8', 'cases': cases}, open(f'{S}/pool_{var}_{dk}.yml', 'w'),
                       default_flow_style=True, width=100000)
print({v: len(s) for v, s in summary.items()})
