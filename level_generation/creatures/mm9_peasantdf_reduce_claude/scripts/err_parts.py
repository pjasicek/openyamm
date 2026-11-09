#!/usr/bin/env python3
"""Where a mpqem_df step deviates from the installed DF1 LOD0: every clip at 10 Hz, both directions (vertex -> nearest point of
the other surface, sampled densely at ~1.5 mm), attributed to the part of the source face (make_sets_df.py parts).
Usage: err_parts.py <mp npz> [sets tag]"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE / 'scripts'))
from glb_pose import Glb, Model  # noqa: E402
import bglbio  # noqa: E402
mp = np.load(sys.argv[1]); sets = np.load(HERE / 'work' / f"glb_sets_{sys.argv[2] if len(sys.argv) > 2 else 'a'}.npz")
src = HERE / 'before' / 'mm9_peasantdf1.glb'
m = Model(Glb(str(src))); doc, b = bglbio.read(src)
node = next(n for n in doc['nodes'] if n.get('name') == 'PeasantDF' and 'mesh' in n)
prs = bglbio.prims(doc, b, node['mesh'])
T0 = [p['T'] for p in prs]; T1 = [mp[p['material']].astype(int) for p in prs]
nb = len(T0[0]); part = sets['part']; parts = [part[:nb], part[nb:]]
names = {0: 'dress', 1: 'skirt', 2: 'boots', 3: 'stockings', 4: 'forearms', 5: 'small', 9: 'twins', 10: 'head', 11: 'hair', 12: 'ears', 13: 'hands'}


def samples(X, T, step=0.0015):
    """dense surface samples, vectorised per subdivision level"""
    V = X[T]; L = np.max(np.linalg.norm(V - np.roll(V, 1, 1), axis=2), 1)
    K = np.clip((L / step).astype(int), 1, 40); pts, fid = [], []
    for k in np.unique(K):
        fs = np.flatnonzero(K == k); i, j = np.meshgrid(np.arange(k + 1), np.arange(k + 1)); mm = i + j <= k
        w = np.stack([i[mm], j[mm], k - i[mm] - j[mm]], 1) / k
        pts.append(np.einsum('sk,fkc->fsc', w, V[fs]).reshape(-1, 3)); fid.append(np.repeat(fs, len(w)))
    return np.concatenate(pts), np.concatenate(fid)


worst = {}; allv = []; per = {}; wv = {}
for clip in m.clips:
    t1 = m.clip_times(clip)[-1]
    for t in np.append(np.arange(0, t1, 0.1), t1):
        posed = [p for p, _ in m.skinned_positions(m.world(m.sample(clip, t)))]
        for pi in range(2):
            X = posed[pi]
            s1, _ = samples(X, T1[pi]); s0, f0 = samples(X, T0[pi])
            # source vertices -> candidate surface; candidate vertices -> source surface (attributed to the nearest source face)
            v0 = np.unique(T0[pi]); d0, _ = cKDTree(s1).query(X[v0])
            v1 = np.unique(T1[pi]); d1, i1 = cKDTree(s0).query(X[v1])
            # part of a source vertex: part of any face using it
            vp = np.full(len(X), -1); vp[T0[pi].ravel()] = np.repeat(parts[pi], 3)
            for d, vv in ((d0, v0), (d1, v1)):
                allv.append(d)
                for p_ in np.unique(vp[vv]):
                    per.setdefault(names.get(int(p_), str(p_)), []).append(d[vp[vv] == p_])
                for k_ in np.argsort(-d)[:3]:
                    key_ = (pi, int(vv[k_]))
                    if d[k_] > wv.get(key_, (0,))[0]:
                        wv[key_] = (d[k_], f'{clip}:{t:.1f}')
                for p_ in np.unique(vp[vv]):
                    sel = vp[vv] == p_; mx = d[sel].max(); key = names.get(int(p_), str(p_))
                    if mx > worst.get(key, (0,))[0]:
                        worst[key] = (mx, f'{clip}:{t:.1f}', np.percentile(d[sel], 99))
a = np.concatenate(allv)
print(f'ALL p99 {np.percentile(a, 99) * 1000:.2f} mm max {a.max() * 1000:.2f} mm (sample spacing 1.5 mm adds up to ~0.5 mm)')
for k, (mx, at, p99) in sorted(worst.items(), key=lambda kv: -kv[1][0]):
    print(f'  {k:10s} max {mx * 1000:6.2f} mm at {at:16s} (p99 in that frame {p99 * 1000:.2f})')
for k, v in per.items():
    v = np.concatenate(v); print(f'  {k:10s} all frames p99 {np.percentile(v, 99) * 1000:.2f} p99.9 {np.percentile(v, 99.9) * 1000:.2f} mm')
jn = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]
for (pi, v), (d, at) in sorted(wv.items(), key=lambda kv: -kv[1][0])[:15]:
    pr = prs[pi]
    print(f'  worst prim{pi} v{v} {d * 1000:.1f} mm at {at} rest {pr["POSITION"][v].round(3)} joints {[jn[j] for j in pr["JOINTS_0"][v][:2]]} w {pr["WEIGHTS_0"][v][:2].round(2)}')
