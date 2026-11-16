"""Talent tree v2 rows for the generic-pack tables ("Every build, every difficulty", "One stage in detail").

Appends to out_route_<seed>.jsonl and meta_route.json (written by rebuild_tail.sh) the harness rows of the v2 variant
(pool_out_v2_<difficulty>.jsonl: Lone Discipline, the passives) with the rest of tree v2 applied as sim.py fields:
the Oath, Unbroken, Archon, Sweeping Blows, Overload, Bloodthirst, Mana Font. Tag: route_v2. Not in this model:
actives (Cleave, Frenzy, Charge, Shield Wall, Blink, Binding Circle, Disengage, Pinning Shot, Volley, Spell Surge) and
range; talentfight.py has those.
"""
import json, math, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from simdir import S
import talents_v2 as T

DIFFS = ('normal', 'maw', 'hard', 'hell', 'nightmare', 'doom', 'insanity', 'madness')
LEECH_DIV = [5, 4, 3, 2.5]
SWEEP_TARGETS = [1, 2, 3]
WEAPONS = ('Sword', 'Axe', 'Mace', 'Spear', 'Staff', 'Dagger', 'Unarmed', 'Armsmaster')


def apply(d, m, cfg):
    d = dict(d)
    build = m['build']
    ks = cfg['keystones']; rk = cfg['ranks']
    oath = T.OATH[build] if 'oath' in ks and build in T.OATH else (None, 1.0, 1.0, 1.0)
    dmg = oath[3]
    deadeye = 1.3 if 'deadeye' in ks else 1.0
    d['emp_melee_per_attack'] *= dmg
    d['spell_dps'] *= dmg
    d['ranged_dps'] *= dmg*deadeye
    d['breath_per_attack'] *= dmg   # Archery (Deadeye) never touches a dragon's breath
    tp, tm = (1.0, 1.0) if build == 'archer' else (oath[1], oath[2])   # the Ranger Oath needs no monster adjacent
    d['tf_tp'] = max(T.CLAMP, tp); d['tf_tm'] = max(T.CLAMP, tm)
    d['tf_unbroken'] = 'unbroken' in ks
    d['tf_archon'] = 'archon' in ks
    if rk.get('sweeping_blows'):
        ws = max([m['skills'].get(k, [0, 0])[0] for k in WEAPONS] + [0])
        d['tf_sweep_n'] = SWEEP_TARGETS[rk['sweeping_blows'] - 1] + (1 if 'warlord' in ks else 0)
        d['tf_sweep_share'] = 0.5 if 'warlord' in ks else min(0.5, 0.30 + 0.0025*ws)
    d['tf_overload'] = 0.1*rk.get('overload', 0)
    bt = rk.get('bloodthirst', 0)
    d['tf_leech_div'] = LEECH_DIV[bt]
    for k in ('leech_melee', 'leech_ranged', 'leech_spell'):
        d[k] += 0.02*bt
    d['sp_per_s'] += rk.get('mana_font', 0)*(m['actual_level']/10)/5
    return d


def main():
    pm = json.load(open(f'{S}/pool_meta.json'))
    meta = json.load(open(f'{S}/meta_route.json'))
    outs = {s: open(f'{S}/out_route_{s}.jsonl', 'a') for s in range(1, 6)}
    n = 0
    for dk in DIFFS:
        for line in open(f'{S}/pool_out_v2_{dk}.jsonl'):
            d = json.loads(line); m = pm[d['id']]
            cfg = T.allocation(m['build'], m['actual_level'], m['skills'], 'v2')
            row = apply(d, m, cfg)
            nid = re.sub(r'\|s\d+', '|route_v2', d['id']); row['id'] = nid
            mm = dict(m); mm['mtag'] = 'route_v2'; meta[nid] = mm
            outs[m['seed']].write(json.dumps(row) + '\n'); n += 1
    for o in outs.values():
        o.close()
    json.dump(meta, open(f'{S}/meta_route.json', 'w'))
    print('talent rows', n)


if __name__ == '__main__':
    main()
