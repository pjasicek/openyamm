"""The solo against the party, in monster strength: how strong the monsters may be for each to beat 90 % of them.

For every stage and difficulty, the factor h by which monster HP and damage can both be multiplied while the share of
monsters in whole groups beaten at once, without potions, stays at 90 % (h < 1: the monsters have to be weaker).
Computed for every solo build (five seeds, median) and for the party-of-five reference, with power_gap_sweep.py's
`mon` lever (a character's damage x k and damage taken x 1/k is the monsters divided by k; h = 1/k).

solo h / party h is the solo's strength against the party's at that stage: below 1 the solo is behind, above 1 ahead.
It is the budget the solo run's rules (the early cut, talents) may fill before a solo is "better than a full party".

Usage: python3 party_line_sweep.py          -> <work dir>/party_line.json, then prints the tables
       python3 party_line_sweep.py tables
Results of 2026-11-15: devdocs/maw/solo_sim/CURVE_RESULTS.md, "The party line".
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
TARGET = 0.9
LO, HI = 1/64, 64.0
OUT = P.H + '/party_line.json'
END = 9999
party_fight = P.RF['party_fight']


def share(case, groups, k):
    """Share of monsters in whole groups beaten with the monsters divided by k."""
    party = case[0] == 'party'
    scaled = [P.scale(g, 'mon', k) for g in groups] if party else P.scale(groups, 'mon', k)
    gs = fights(case)
    total = sum(len(a) for a in gs)
    won = 0
    for actors in gs:
        f = party_fight(scaled, actors, False) if party else P.fight(scaled, actors, False)
        won += 0 if f['dead'] or f.get('deaths') else len(actors)
    return won/total if total else None


def fights(case):
    build, Lc, tag, seed = case
    gs = []
    for mp in P.FIGHTS.get(f'{tag}|{seed}|{Lc}', []):
        groups = collections.defaultdict(list)
        for a in mp['actors']:
            groups[a[4]].append(a)
        gs.extend(groups.values())
    return gs


def job(a):
    case, groups = a
    if not fights(case):
        return (case, None)
    if share(case, groups, HI) < TARGET:
        return (case, LO)            # not even with the monsters at 1/64
    if share(case, groups, LO) >= TARGET:
        return (case, 1/LO)
    lo, hi = LO, HI                  # share(lo) < TARGET <= share(hi)
    for _ in range(11):
        mid = math.sqrt(lo*hi)
        if share(case, groups, mid) >= TARGET:
            hi = mid
        else:
            lo = mid
    return (case, 1/hi)


def sweep():
    jobs = []
    for diff in DIFFS:
        solo = collections.defaultdict(dict)
        for line in open(f'{P.H}/pool_out_{diff}.jsonl'):
            d = json.loads(line); m = P.meta[d['id']]
            solo[(m['build'], m['Lc'], diff, m['seed'])][m['spell'] or 'none'] = (d, m)
        jobs += list(solo.items())
        members = collections.defaultdict(lambda: collections.defaultdict(dict))
        for line in open(f'{P.H}/pool_out_{diff}_party.jsonl'):
            d = json.loads(line); m = P.meta[d['id']]
            members[('party', m['Lc'], diff + '_party', m['seed'])][m['build']][m['spell'] or 'none'] = (d, m)
        jobs += [(case, list(g.values())) for case, g in members.items()]
    with multiprocessing.Pool() as pool:
        res = pool.map(job, jobs, chunksize=2)
    json.dump([[list(c), h] for c, h in res], open(OUT, 'w'))


def tables():
    by = collections.defaultdict(list)
    for (b, L, tag, seed), h in json.load(open(OUT)):
        if h is not None:
            by[(b, L, tag.replace('_party', ''))].append(h)
    med = {k: statistics.median(v) for k, v in by.items() if len(v) >= 3}
    stages = sorted({k[1] for k in med})
    name = lambda L: 'end' if L == END else 'start' if L == 1 else str(L)
    focus = ['knight_2h', 'knight_sns', 'minotaur_dual', 'troll', 'seraph', 'dragon', 'archer', 'archmage', 'priest']
    for d in DIFFS:
        print(f'\n### {d}\n')
        print('| Stage | Party h | Solo h, typical | Solo / party: typical | weakest | best | ' + ' | '.join(focus) + ' |')
        print('| --- |' + ' --- |'*(5 + len(focus)))
        for L in stages:
            p = med.get(('party', L, d))
            solo = {k[0]: v for k, v in med.items() if k[1] == L and k[2] == d and k[0] != 'party'}
            if not p or not solo:
                continue
            r = {b: v/p for b, v in solo.items()}
            print(f"| {name(L)} | {p:.2f} | {statistics.median(solo.values()):.2f} | {statistics.median(r.values()):.2f} | "
                  f"{min(r.values()):.2f} | {max(r.values()):.2f} | " + ' | '.join(f'{r[b]:.2f}' if b in r else '–' for b in focus) + ' |')


if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] != 'tables':
        sweep()
    tables()
