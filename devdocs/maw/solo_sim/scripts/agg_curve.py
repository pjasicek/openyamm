"""The power curve: every solo build and the party-of-five reference at every stage of the route.

Reads the real-group fights (real_pool_out_<dk>.json and real_pool_out_<dk>_party.json) and writes data_curve.json:
one row per build (or "party"), stage and difficulty, the median over the seeds of

  level      the character's level there (a party member's level for the party)
  ok, okp    share of monsters in whole groups beaten at once, without / with potions
  ok4, ok4p  the same with the groups pulled four at a time
  maps0      share of the stage's maps cleared with every group taken whole and no potion drunk
  maps       share of the stage's maps fully cleared, potions allowed, a group split in fours when it cannot be beaten
             whole ("best effort": what a player who wants the map's completion reward does)
  drinks     potions drunk per 100 monsters on that best effort (beaten groups)
  spm        seconds of fighting per monster on it
  deaths     party members lost per 100 monsters (a solo's death is a failed group, so 0 for solos)

`python3 agg_curve.py tables` prints the comparison tables from data_curve.json.
"""
import json, glob, statistics, collections, sys

from simdir import S
END = 9999
DIFFS = ['normal', 'maw', 'hard', 'hell', 'nightmare', 'doom', 'insanity', 'madness']
MELEE = ['knight_sns', 'knight_2h', 'troll_knight', 'vamp_knight', 'minotaur_dual', 'minotaur_one', 'dk_minotaur',
         'dk_vampire', 'dk_minotaur_dual', 'minotaur_knight_dual', 'troll', 'troll_staff', 'nosferatu', 'seraph',
         'assassin', 'monk', 'shaman']


def aggregate():
    by = collections.defaultdict(list)
    for f in glob.glob(S + '/real_pool_out_*.json'):
        for r in json.load(open(f)):
            by[(r['build'], r['Lc'], r['diff'])].append(r)
    rows = []
    for (build, Lc, diff), runs in by.items():
        per_seed = []
        for r in runs:
            groups = [g for m in r['maps'] for g in m['groups']]
            mons = sum(g['n'] for g in groups)
            if not mons:
                continue
            maps = [m for m in r['maps'] if m['groups']]
            beaten = [g for g in groups if not g['deadp'] or not g['dead4p']]
            whole = lambda g: not g['deadp']
            per_seed.append(dict(
                level=r.get('level', Lc),
                ok=sum(g['n'] for g in groups if not g['dead'])/mons,
                okp=sum(g['n'] for g in groups if not g['deadp'])/mons,
                ok4=sum(g['n'] for g in groups if not g['dead4'])/mons,
                ok4p=sum(g['n'] for g in groups if not g['dead4p'])/mons,
                maps0=sum(1 for m in maps if all(not g['dead'] and not g.get('deaths') for g in m['groups']))/len(maps),
                maps=sum(1 for m in maps if all(not g['deadp'] or not g['dead4p'] for g in m['groups']))/len(maps),
                drinks=100*sum(g['drinks'] if whole(g) else g['drinks4'] for g in beaten)/max(1, sum(g['n'] for g in beaten)),
                spm=sum(g['time'] if whole(g) else g['time4'] for g in beaten)/max(1, sum(g['n'] for g in beaten)),
                deaths=100*sum(g.get('deaths', 0) if whole(g) else g.get('deaths4', 0) for g in beaten)
                    /max(1, sum(g['n'] for g in beaten)) if r.get('party') else 0.0,
                gmed=statistics.median(g['n'] for g in groups), gmax=max(g['n'] for g in groups),
                mlv=statistics.median(m['level'] for m in maps)))
        if len(per_seed) < 3:
            continue
        med = lambda k: statistics.median(p[k] for p in per_seed)
        rows.append(dict(b=build, L=Lc, d=diff, level=round(med('level')), mlv=round(med('mlv')),
                         ok=round(100*med('ok')), okp=round(100*med('okp')), ok4=round(100*med('ok4')),
                         ok4p=round(100*med('ok4p')), maps0=round(100*med('maps0')), maps=round(100*med('maps')),
                         drinks=round(med('drinks'), 1), spm=round(med('spm'), 2), deaths=round(med('deaths'), 2),
                         gmed=med('gmed'), gmax=round(med('gmax'))))
    json.dump(rows, open(S + '/data_curve.json', 'w'), separators=(',', ':'))
    print(len(rows), 'rows')


def tables():
    rows = json.load(open(S + '/data_curve.json'))
    at = {(r['b'], r['L'], r['d']): r for r in rows}
    stages = sorted({r['L'] for r in rows})
    name = lambda L: 'end' if L == END else 'start' if L == 1 else str(L)

    def typical(d, L, key, builds=None):
        v = [r[key] for r in rows if r['d'] == d and r['L'] == L and r['b'] != 'party' and (not builds or r['b'] in builds)]
        return (statistics.median(v), min(v), max(v)) if v else None

    for d in DIFFS:
        if not any(r['d'] == d for r in rows):
            continue
        print(f'\n### {d}\n')
        print('| Stage | Level solo / party | Monsters | Maps cleared: party | solo typical (weakest–best) | Whole groups, no potions:'
              ' party | solo | Potions per 100 monsters: party | solo | Seconds per monster: party | solo | Party deaths per 100 |')
        print('| --- |' + ' --- |'*11)
        for L in stages:
            p = at.get(('party', L, d)); t = typical(d, L, 'maps')
            if not t:
                continue
            f = lambda key, fmt='{:.0f}': fmt.format(typical(d, L, key)[0])
            lv = typical(d, L, 'level')[0]
            pv = lambda key, fmt='{:.0f}': fmt.format(p[key]) if p else '–'
            print(f"| {name(L)} | {lv:.0f} / {pv('level')} | {typical(d, L, 'mlv')[0]:.0f} | {pv('maps')} % | "
                  f"{t[0]:.0f} % ({t[1]:.0f}–{t[2]:.0f}) | {pv('ok')} % | {f('ok')} % | {pv('drinks', '{:.1f}')} | "
                  f"{f('drinks', '{:.1f}')} | {pv('spm', '{:.1f}')} | {f('spm', '{:.1f}')} | {pv('deaths', '{:.1f}')} |")


if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] != 'tables':
        aggregate()
    tables()
