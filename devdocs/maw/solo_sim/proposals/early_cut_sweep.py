"""Early-game monster cut: by how much the monsters' HP and damage must be divided for a solo to beat whole groups.

For every build, difficulty and seed at stages 10, 50 and 200, bisects power_gap_sweep.py's `mon` lever (the
character's damage x k and every damage taken x 1/k, the same as dividing the monsters' HP and damage by k) until the
share of monsters in whole groups beaten at once, without potions and without talents, reaches the target: 90 % and
100 % (every group of the ten maps around the stage, the largest included). k is capped at 64 ("inf" in the JSON).

Usage: python3 early_cut_sweep.py          -> <work dir>/early_cut.json, then prints the table (median over seeds)
       python3 early_cut_sweep.py tables   -> prints the table from the JSON
Results of 2026-11-15: devdocs/solo_action/POWER_CURVE_DIRECTION.md.
"""
import sys, os, json, math, statistics, collections, multiprocessing

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'scripts'))
_argv = sys.argv
sys.argv = ['power_gap_sweep.py']
import power_gap_sweep as P
sys.argv = _argv

DIFFS = ['maw', 'nightmare', 'doom', 'insanity', 'madness']
STAGES = [int(x) for x in os.environ.get('CUT_STAGES', '10,50,200').split(',')]
# 0.9 and 1.0, or with CUT_TARGET=party the share the party-of-five reference beats at the same stage (data_curve.json
# of the curve run, scripts/agg_curve.py): the cut that makes a solo's whole groups as beatable as a party finds them.
PARTY = os.environ.get('CUT_TARGET') == 'party'
TARGETS = ['party'] if PARTY else [0.9, 1.0]
PARTY_OK = {(r['d'], r['L']): r['ok']/100 for r in json.load(open(P.H + '/data_curve.json')) if r['b'] == 'party'} \
    if PARTY else {}
CAP = 64.0
OUT = P.H + ('/early_cut_party.json' if os.environ.get('CUT_TARGET') == 'party' else '/early_cut.json')


def share(group, gs):
    return P.run(group, gs, 'ok')[0]


def job(a):
    case, group, target = a
    label = target
    gs = P.case_groups(case)
    if target == 'party':
        target = PARTY_OK.get((case[2], case[1]))
    if not gs or target is None:
        return (case, label, None)
    if share(group, gs) >= target - 1e-9:
        return (case, label, 1.0)
    lo, hi = 1.0, CAP
    if share(P.scale(group, 'mon', hi), gs) < target - 1e-9:
        return (case, label, math.inf)
    for _ in range(9):
        mid = math.sqrt(lo*hi)
        if share(P.scale(group, 'mon', mid), gs) >= target - 1e-9:
            hi = mid
        else:
            lo = mid
    return (case, label, hi)


def sweep():
    cases = P.load_cases(DIFFS)
    jobs = [(c, g, t) for c, g in cases.items() if c[1] in STAGES for t in TARGETS]
    with multiprocessing.Pool() as pool:
        res = pool.map(job, jobs, chunksize=4)
    json.dump([[list(c), t, (k if k is None or math.isfinite(k) else 'inf')] for c, t, k in res], open(OUT, 'w'))


def tables():
    by = collections.defaultdict(list)
    for (b, L, d, s), t, k in json.load(open(OUT)):
        if k is not None:
            by[(d, L, t, b)].append(CAP if k == 'inf' else k)
    agg = collections.defaultdict(dict)
    for (d, L, t, b), v in by.items():
        agg[(d, L, t)][b] = statistics.median(v)
    for t in TARGETS:
        goal = 'as the party of five beats them' if t == 'party' else f'>= {t:.0%}'
        print(f'\nMonsters divided by k: whole groups beaten {goal} (median build / knight_sns / archer / archmage '
              f'/ worst but the Priest)\n')
        print('| Difficulty | ' + ' | '.join(f'Level {L}' for L in STAGES) + ' |')
        print('| --- |' + ' --- |'*len(STAGES))
        for d in DIFFS:
            cells = []
            for L in STAGES:
                m = agg[(d, L, t)]
                if not m:
                    cells.append('–'); continue
                rest = [v for b, v in m.items() if b != 'priest']
                cells.append(f"{statistics.median(m.values()):.1f} / {m['knight_sns']:.1f} / {m['archer']:.1f} / "
                             f"{m['archmage']:.1f} / {max(rest):.1f}")
            print(f'| {d} | ' + ' | '.join(cells) + ' |')


if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] != 'tables':
        sweep()
    tables()
