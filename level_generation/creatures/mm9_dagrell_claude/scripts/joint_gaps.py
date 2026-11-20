#!/usr/bin/env python3
"""Joint gaps of a piece-built creature GLB: how far each pair of joined pieces opens in every clip.

    joint_gaps.py <glb> [--fit rig_state.npz] [--ref-clip Standing] [--fps 48] [--adj 0.01] [--clips A,B]
                  [--json out.json]

Pieces are the GLB's LOD0 connected components (welded by position). Two pieces are joined when they come within
--adj of each other in the reference pose: the bind pose, or with --fit the FitPose of a rig dump (dump_rig_state.py of
the blend the GLB was exported from; every GLB vertex takes the FitPose position of the dump vertex at its rest
position), i.e. Meshy's own assembly, where the pieces touch as they were made; with --ref-clip, pairs touching at
that clip's first frame count too (mirrored limbs have no FitPose of their own). Use --ref-clip without --fit for
the MM9 original (its crouched bind pose folds toes against thighs). In each clip, sampled at --fps with
linear-blend skinning (claude_shared/floor/glb_pose.py), a joined pair's opening is its minimum vertex distance minus
its reference distance. Prints per clip the worst opening and its pair, and the number of pairs open more than 1, 2
and 5 cm; --json writes them with every pair's worst. Pairs between the lower jaw and the skull (--mouth) open with
the bite and are reported apart as the mouth opening.
"""
import argparse
import json
from pathlib import Path
import sys

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'claude_shared' / 'floor'))
import glb_pose  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('glb')
    ap.add_argument('--fit', default=None)
    ap.add_argument('--fps', type=float, default=48.0)
    ap.add_argument('--adj', type=float, default=0.01)
    ap.add_argument('--ref-clip', default=None,
                    help='also (without --fit: instead of the bind pose) join pieces touching in this clip at 0 s')
    ap.add_argument('--clips', default=None)
    ap.add_argument('--json', default=None)
    ap.add_argument('--mouth', default='Xjawpiv,Xjawbase:Xheadpiv,Xnose',
                    help='pairs between these two joint groups open with the mouth: reported apart (MM9 bites)')
    a = ap.parse_args()
    glb = glb_pose.Glb(a.glb)
    model = glb_pose.Model(glb)
    nodes = glb.json['nodes']
    meshes = glb.json['meshes']
    model.primitives = [p for p in model.primitives
                        if 'shadow' not in ((nodes[p['node']].get('name') or '') +
                                            (meshes[nodes[p['node']]['mesh']].get('name') or '')).lower()]
    rest = np.concatenate([p['positions'] for p in model.primitives])
    tris, off = [], 0
    for p in model.primitives:
        tris.append(p['triangles'] + off); off += len(p['positions'])
    tris = np.concatenate(tris)
    world0 = model.world({})
    bind = np.concatenate([pts for pts, _ in model.skinned_positions(world0)])
    key = np.round(bind / 1e-5).astype(np.int64)
    _, weld = np.unique(key, axis=0, return_inverse=True)
    weld = weld.reshape(-1)
    wt = weld[tris]
    nw = int(weld.max()) + 1
    g = coo_matrix((np.ones(wt.size), (np.r_[wt[:, 0], wt[:, 1], wt[:, 2]], np.r_[wt[:, 1], wt[:, 2], wt[:, 0]])),
                   shape=(nw, nw))
    _, lab = connected_components(g, directed=False)
    comp = lab[weld]
    ids = np.unique(comp[np.unique(tris)])
    verts = {int(k): np.nonzero(comp == k)[0] for k in ids}
    ref = bind
    if a.fit:
        d = np.load(a.fit)
        # Blender Z-up rest -> glTF Y-up (x, z, -y); the GLB rest is the bind pose of the skinned mesh
        drest = d['rest'] @ np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]])
        dfit = d['fit'] @ np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]])
        dist, idx = cKDTree(drest).query(bind)
        assert dist.max() < 1e-3, f'rest positions do not match the dump (max {dist.max():.4f})'
        ref = dfit[idx]
    found = {}
    ks = sorted(verts)
    # joined in the FitPose and/or the --ref-clip pose (the mirrored left limbs have no FitPose of their own; the
    # crouched bind pose folds limbs against the ribs, so it is not used then); the reference distance is the smaller
    refs = [ref] if a.fit else []
    if a.ref_clip:
        refs.append(np.concatenate([pts for pts, _ in model.skinned_positions(model.world(model.sample(a.ref_clip, 0.0)))]))
    if not refs:
        refs = [bind]
    for rp in refs:
        trees = {k: cKDTree(rp[v]) for k, v in verts.items()}
        lo = {k: rp[v].min(0) for k, v in verts.items()}
        hi = {k: rp[v].max(0) for k, v in verts.items()}
        for i, p in enumerate(ks):
            for q in ks[i + 1:]:
                if np.any(lo[p] - a.adj > hi[q]) or np.any(lo[q] - a.adj > hi[p]):
                    continue
                dd = float(trees[q].query(rp[verts[p]])[0].min())
                if dd <= a.adj and dd < found.get((p, q), 1e9):
                    found[(p, q)] = dd
    pairs = [(p, q, d0) for (p, q), d0 in sorted(found.items())]
    # a readable label: dominant joint
    joint_names = [nodes[j].get('name', str(j)) for j in model.joints]
    jw = np.zeros((len(rest), max(1, len(joint_names))))
    off = 0
    for p in model.primitives:
        m = len(p['positions'])
        if p['skinned']:
            for c in range(p['joints'].shape[1]):
                np.add.at(jw, (np.arange(off, off + m), p['joints'][:, c]), p['weights'][:, c])
        else:
            par = model.parent[p['node']]
            if par in model.joints:
                jw[off:off + m, model.joints.index(par)] += 1
        off += m
    domj = {k: joint_names[int(np.argmax(jw[v].sum(0)))] for k, v in verts.items()}
    label = {k: f'{k}:{domj[k]}' for k, v in verts.items()}
    ga, gb = (set(x.split(',')) for x in a.mouth.split(':'))
    mouth = [((domj[p] in ga and domj[q] in gb) or (domj[p] in gb and domj[q] in ga)) for p, q, _ in pairs]
    clips = a.clips.split(',') if a.clips else list(model.clips)
    out = {'glb': a.glb, 'reference': 'fit' if a.fit else 'bind', 'pairs': len(pairs), 'clips': {}}
    worst_pair = {}
    for clip in clips:
        dur = model.clip_times(clip)[-1]
        best = (0.0, None, None)
        mouth_open = 0.0
        open_by_pair = np.zeros(len(pairs))
        for t in np.arange(0.0, dur + 1e-9, 1.0 / a.fps):
            pos = np.concatenate([pts for pts, _ in model.skinned_positions(model.world(model.sample(clip, t)))])
            for n_, (p, q, d0) in enumerate(pairs):
                dd = cKDTree(pos[verts[q]]).query(pos[verts[p]])[0].min() - d0
                if dd > open_by_pair[n_]:
                    open_by_pair[n_] = dd
                if mouth[n_]:
                    mouth_open = max(mouth_open, float(dd))
                    continue
                if dd > best[0]:
                    best = (float(dd), n_, float(t))
        joint = np.array([not m for m in mouth])
        rec = {'worst_m': round(best[0], 4), 'time': best[2], 'mouth_open_m': round(mouth_open, 4),
               'pair': None if best[1] is None else [label[pairs[best[1]][0]], label[pairs[best[1]][1]]],
               'pairs_over_1cm': int((open_by_pair[joint] > 0.01).sum()),
               'pairs_over_2cm': int((open_by_pair[joint] > 0.02).sum()),
               'pairs_over_5cm': int((open_by_pair[joint] > 0.05).sum())}
        out['clips'][clip] = rec
        for n_, v in enumerate(open_by_pair):
            key_ = f'{label[pairs[n_][0]]} - {label[pairs[n_][1]]}' + (' (mouth)' if mouth[n_] else '')
            if v > worst_pair.get(key_, (0, ''))[0]:
                worst_pair[key_] = (round(float(v), 4), clip)
        print(f"{clip:14s} worst {rec['worst_m']:.3f} m at {rec['time']:.3f} s {rec['pair']} mouth {mouth_open:.3f}  pairs >1cm "
              f"{rec['pairs_over_1cm']}, >2cm {rec['pairs_over_2cm']}, >5cm {rec['pairs_over_5cm']} (of {len(pairs)})")
    out['worst_pairs'] = dict(sorted(worst_pair.items(), key=lambda kv: -kv[1][0])[:40])
    if a.json:
        Path(a.json).write_text(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
