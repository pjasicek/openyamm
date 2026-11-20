"""Aggregate realfight results: per build, stage and difficulty, the median over seeds."""
import json, glob, statistics, collections

from simdir import S, CODE
MAPS = json.load(open(S + '/inv/maps.json'))
by = collections.defaultdict(list)
for f in glob.glob(S + '/real_pool_out_*.json'):
    for r in json.load(open(f)):
        by[(r['build'], r['Lc'], r['diff'])].append(r)

PROMO = {0: '', 1: '', 2: 'Elder ', 3: 'Ultimate '}
rows = []
for (build, Lc, diff), runs in by.items():
    per_seed = []
    for r in runs:
        mons = sum(g['n'] for m in r['maps'] for g in m['groups'])
        if not mons:
            continue
        ok = sum(g['n'] for m in r['maps'] for g in m['groups'] if not g['dead'])
        okp = sum(g['n'] for m in r['maps'] for g in m['groups'] if not g['deadp'])
        groups = [g for m in r['maps'] for g in m['groups']]
        biggest = max([g['n'] for g in groups if not g['dead']] or [0])
        per_map_t = [sum(g['time'] for g in m['groups'] if not g['deadp']) for m in r['maps']]
        per_map_d = [sum(g['drinks'] for g in m['groups'] if not g['deadp']) for m in r['maps']]
        per_map_n = [m['monsters'] for m in r['maps']]
        kill_rate = sum(per_map_t)/max(1, sum(per_map_n))     # seconds of fighting per monster
        drink_rate = sum(per_map_d)/max(1, sum(per_map_n))*100
        worst = sorted((g for g in groups if g['deadp']), key=lambda g: -g['n'])[:3]
        ok4 = sum(g['n'] for g in groups if not g['dead4'])
        ok4p = sum(g['n'] for g in groups if not g['dead4p'])
        t4 = sum(g['time4'] for g in groups if not g['dead4p'])/max(1, ok4p)
        d4 = sum(g['drinks4'] for g in groups if not g['dead4p'])/max(1, ok4p)*100
        per_seed.append(dict(ok4=ok4/mons, ok4p=ok4p/mons, spm4=t4, dpm4=d4, ok=ok/mons, okp=okp/mons, big=biggest, spm=kill_rate, dpm=drink_rate,
                             gmed=statistics.median(g['n'] for g in groups), gmax=max(g['n'] for g in groups),
                             worst=[[g['n'], g['lv'], ', '.join(f'{c}× {n}' for n, c in g['names'])] for g in worst],
                             cls=PROMO[r['promoted'] if r['cls'] and r['promoted'] >= 2 else 0] + (r['cls'] or ''),
                             maps=r['maps'], hp=r['hp']))
    if len(per_seed) < 3:
        continue
    med = lambda k: statistics.median(p[k] for p in per_seed)
    # the seed whose standing share is the median, for the map details
    mid = sorted(per_seed, key=lambda p: p['ok'])[len(per_seed)//2]
    maps = [dict(f=MAPS.get(m['file'], {}).get('name', m['file']), nx=m['next'], lv=round(m['level']), n=m['monsters'],
                 g=[[g['n'], g['lv'], ', '.join(f'{c}× {n}' for n, c in g['names']), int(g['dead']) + int(g['deadp']),
                     round(g['time']), g['drinks'], round(100*g['dps'], 1), int(g['dead4']) + int(g['dead4p'])] for g in sorted(m['groups'], key=lambda g: -g['dps'])[:5]],
                 ng=len(m['groups']), ok=sum(1 for g in m['groups'] if not g['dead']), ok4=sum(1 for g in m['groups'] if not g['dead4']),
                 gmed=statistics.median(g['n'] for g in m['groups']) if m['groups'] else 0, gmax=max([g['n'] for g in m['groups']] or [0]))
            for m in mid['maps']]
    rows.append(dict(b=build, L=Lc, d=diff, cls=mid['cls'], ok4=round(100*med('ok4')), ok4p=round(100*med('ok4p')),
                     spm4=round(med('spm4'), 1), dpm4=round(med('dpm4')), ok=round(100*med('ok')), okp=round(100*med('okp')),
                     big=round(med('big')), spm=round(med('spm'), 1), dpm=round(med('dpm')), gmed=med('gmed'),
                     gmax=round(med('gmax')), worst=mid['worst'], maps=maps))
json.dump(rows, open(S + '/data_real.json', 'w'), separators=(',', ':'))
print(len(rows), 'rows')
