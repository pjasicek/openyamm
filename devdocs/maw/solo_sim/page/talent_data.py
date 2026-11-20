"""Adds the talent-tree simulations (talentfight.py: tf_main.json, tf_norange.json, tf_ablate.json) to
the page's data.json as DATA.tf, and copies the talent page mockups into the page's deploy folder."""
import json, os, shutil, statistics, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts'))
from simdir import S, REPO
import talents_v2 as T

main = json.load(open(f'{S}/tf_main.json'))
norange = json.load(open(f'{S}/tf_norange.json'))
ablate = json.load(open(f'{S}/tf_ablate.json'))

r1 = lambda v: None if v is None else round(v, 1)
cells = {}
for src, rename in ((main, None), (norange, 'old')):
    for k, r in src.items():
        diff, L, b, c = k.split('|')
        c = rename or c
        e = [round(r['ok4']*100), round(r['ok']*100), r1(r['spm4']), r1(r['spm'])]
        if c in ('v1', 'v2'):
            e.append({t: [round(u, 1), round(r['dmg_share'].get(t, 0)*100)] for t, u in r['use_per_min'].items()})
            e.append(dict(r=r['cfg']['ranks'], k=r['cfg']['keystones'], p=r['cfg']['points']))
        cells[f'{diff}|{L}|{b}|{c}'] = e

# Melee summary: min and median of pulls of four, median seconds per monster.
MELEE = sorted(T.MELEE - {'dragon'})
summary = {}
for diff in ('normal', 'maw', 'hard', 'hell', 'nightmare', 'doom', 'insanity', 'madness'):
    for L in (10, 50, 200, 500):
        for c in ('old', 'today', 'v1', 'v2'):
            v = [cells.get(f'{diff}|{L}|{b}|{c}') for b in MELEE]
            v = [x for x in v if x]
            if not v:
                continue
            ok = [x[0] for x in v]; sp = [x[2] for x in v if x[2] is not None]
            summary[f'{diff}|{L}|{c}'] = [min(ok), statistics.median(ok), r1(statistics.median(sp)) if sp else None]

# Ablations: change in pulls of four when one keystone or talent is taken away, per build.
abl = {}
for k, r in ablate.items():
    diff, L, b, c = k.split('|')
    base = ablate.get(f'{diff}|{L}|{b}|v2')
    if c == 'v2' or not base:
        continue
    cut = c[3:]
    if cut not in base['cfg']['keystones'] and not base['cfg']['ranks'].get(cut):
        continue      # the build does not have it
    abl[f'{diff}|{b}|{cut}'] = round((r['ok4'] - base['ok4'])*100)

data_path = f'{S}/page/data.json'
data = json.load(open(data_path))
data['tf'] = dict(cells=cells, summary=summary, ablate=abl)
json.dump(data, open(data_path, 'w'), separators=(',', ':'))

# Mockup images for the deploy folder (the artifact gets them through its files map).
src = os.path.join(REPO, 'level_generation', 'ui', 'solo_talents_v2_20261114', 'previews')
dst = os.path.join(S, 'page', 'deploy', 'mockups')
os.makedirs(dst, exist_ok=True)
for f in ('a.png', 'a_tip_sweeping.png', 'b.png', 'b_trees.png'):
    shutil.copy(os.path.join(src, f), os.path.join(dst, f))
print('tf cells', len(cells), 'summary', len(summary), 'ablate', len(abl), 'size', os.path.getsize(data_path))
