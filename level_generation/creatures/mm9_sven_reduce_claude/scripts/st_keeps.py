#!/usr/bin/env python3
"""See-through keeps (the PeasantM1 project's extra_keeps_pm1.py rule): faces hit by the hole pixels of the probes
(work/probe/*.json, scripts/st_probe.py on the installed GLB and a candidate at the clip/frame/views where the candidate's
holes rose) -> every face of the cut parts with its rest centroid within NEAR m of a hit face (either GLB). Probe rest centroids
are Blender's re-based import: glTF y = probe y + OFFSET (mpqem.py's BLENDER OFFSET).
-> work/keep_st.npy (glb_parts.npz order). Usage: st_keeps.py  (env OFFSET, NEAR default 0.04, ZONES=1, PARTS comma list, default all
but the face shell)"""
import glob, json, os, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio, cfg  # noqa: E402
_, _, _, D = glbio.load(HERE / 'before' / cfg.GLB, cfg.NODE)
g = np.load(HERE / 'work' / 'glb_parts.npz'); part = g['part']
P = np.concatenate([D[k]['P'] for k in cfg.PR]); T = np.concatenate([D[k]['T'] + g['voff'][i] for i, k in enumerate(cfg.PR)])
C = P[T].mean(1); OFFSET = float(os.environ['OFFSET']); NEAR = float(os.environ.get('NEAR', '0.04'))
# ZONES=1: per probe only the hits in the zone(s) whose maximum rose there (work/probe_jobs_*.txt comments "# <zone> +<px>")
zones = {}
if os.environ.get('ZONES') == '1':
    for jf in glob.glob(str(HERE / 'work' / 'probe_jobs_*.txt')):
        for line in open(jf):
            a = line.split('#')[0].split(); z = line.split('#')[1].strip().rsplit(' ', 1)[0]
            zones.setdefault(f'{a[1]}_{a[3]}_{a[4]}_{a[5]}', set()).add(z)
    # both GLBs of a probe take the zones of either label at that clip/frame/view
    by_key = {}
    for k, v in zones.items():
        by_key.setdefault(k.split('_', 1)[1], set()).update(v)
hits = []; inst = []
for f in sorted(glob.glob(str(HERE / 'work' / 'probe' / '*.json'))):
    stem = os.path.basename(f)[:-5]; want = by_key.get(stem.split('_', 1)[1]) if zones else None
    for o in json.load(open(f))['faces']:
        if want is not None and o['zone'] not in want:
            continue
        x, y, z = o['rest_gltf']; hits.append((x, y + OFFSET, z)); inst.append(os.path.basename(f).startswith('before_'))
hits = np.array(hits); inst = np.array(inst)
dist = cKDTree(C).query(hits[inst])[0]
print('hit faces', len(hits), 'installed hits matched to a GLB face centroid: p50 / max mm', np.round(np.median(dist) * 1000, 2), np.round(dist.max() * 1000, 2))
parts = [int(x) for x in os.environ['PARTS'].split(',')] if os.environ.get('PARTS') else [p for p in np.unique(part) if p != 20]
keep = (cKDTree(hits).query(C)[0] < NEAR) & np.isin(part, parts)
np.save(HERE / 'work' / 'keep_st.npy', keep)
print('see-through keep', int(keep.sum()), {int(p): int((keep & (part == p)).sum()) for p in np.unique(part[keep])})
