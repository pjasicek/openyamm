"""Symmetry gate (system Python): mirrored-vertex distance, landmark pairs, rig and weights, for the v2 final mesh
(work/v2/final.npz, dumped from work/v2/anim_v2.blend) against v1 (work/v2/v1_textured.npz, the reduced v1 rest mesh).
Landmarks per side: eye (iris texel centre of the v1 paint moved into the v2 frame, nearest surface vertex), the
outermost crest-horn tip, fore and hind claw tips (lowest / foremost vertices of each foot), wing tip. Writes
review/symmetry_gate.json."""
import json, sys
import numpy as np
from pathlib import Path
from scipy.spatial import cKDTree
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P / 'scripts'))
from straighten import straighten


def mirror_stats(co):
    d, _ = cKDTree(co).query(co * [-1, 1, 1]); return {'median_mm': round(float(np.median(d)) * 1000, 3), 'p99_mm': round(float(np.percentile(d, 99)) * 1000, 3),
                                                    'max_mm': round(float(d.max()) * 1000, 3)}


def landmarks(co, part):
    x, y, z = co.T; out = {}
    for s, sg in (('L', 1), ('R', -1)):
        side = x * sg > 0.002
        horn = side & (part > 0) & (z > .43); out[f'horn_tip_{s}'] = co[np.where(horn)[0][np.argmax(z[horn])]] if horn.any() else None
        fore = side & (y < -.33) & (z < .2) & (part == 0); out[f'fore_claw_{s}'] = co[np.where(fore)[0][np.argmin(y[fore])]]
        hind = side & (y > -.12) & (y < .02) & (z < .05); out[f'hind_claw_{s}'] = co[np.where(hind)[0][np.argmin(z[hind] + .3 * y[hind])]]
        wing = side & (np.abs(x) > .2); out[f'wing_tip_{s}'] = co[np.where(wing)[0][np.argmax(np.abs(x[wing]))]]
        eye = np.array([sg * abs(EYE[0]), EYE[1], EYE[2]]); out[f'eye_{s}'] = co[cKDTree(co).query(eye)[1]]
    pairs = {}
    for k in ('horn_tip', 'fore_claw', 'hind_claw', 'wing_tip', 'eye'):
        a, b = out[f'{k}_L'], out[f'{k}_R']
        if a is None or b is None: continue
        pairs[k] = {'L': np.round(a, 4).tolist(), 'R': np.round(b, 4).tolist(), 'mirror_error_mm': round(float(np.linalg.norm(a - b * [-1, 1, 1])) * 1000, 2)}
    return pairs


EYE = straighten(np.array([[.0022, -.3525, .4283]]))[0]
new = np.load(P / 'work/v2/final.npz'); old = np.load(P / 'work/v2/v1_textured.npz')
doc = {'v2_final_mesh': {'vertices': len(new['co']), 'triangles': len(new['tris']), 'mirror_vertex_distance': mirror_stats(new['co']),
                         'landmarks': landmarks(new['co'], new['part'])},
       'v1_reduced_mesh': {'vertices': len(old['co']), 'mirror_vertex_distance': mirror_stats(old['co']), 'landmarks': landmarks(old['co'], old['part'])}}
# rig: every L bone mirrors its R partner, centre bones on x = 0
names = [str(b) for b in new['bone_names']]; H, T = new['bone_head'], new['bone_tail']; worst = 0.; centre = 0.
for i, n in enumerate(names):
    if n.startswith('L') and 'R' + n[1:] in names:
        j = names.index('R' + n[1:]); worst = max(worst, np.abs(H[i] * [-1, 1, 1] - H[j]).max(), np.abs(T[i] * [-1, 1, 1] - T[j]).max())
    elif not n.startswith('R'):
        centre = max(centre, abs(H[i, 0]), abs(T[i, 0]))
# weights: w(v, bone) == w(mirror(v), mirror(bone))
co = new['co']; _, partner = cKDTree(co).query(co * [-1, 1, 1]); G = [str(g) for g in new['group_names']]; W = new['weights']
swap = [G.index(('R' + g[1:]) if g[:1] == 'L' and 'R' + g[1:] in G else ('L' + g[1:]) if g[:1] == 'R' and 'L' + g[1:] in G else g) for g in G]
werr = float(np.abs(W[partner][:, swap] - W).max())
doc['rig'] = {'bones': len(names), 'paired_bone_mirror_error_m': float(worst), 'centre_bone_max_abs_x_m': float(centre), 'weight_mirror_max_error': werr}
gate = doc['v2_final_mesh']['mirror_vertex_distance']['p99_mm'] < .01 and max(p['mirror_error_mm'] for p in doc['v2_final_mesh']['landmarks'].values()) < .01 \
    and worst < 1e-6 and centre < 1e-6 and werr < 1e-4
doc['passed'] = bool(gate)
doc['method'] = ('v2 straightening (head yaw 9.8 deg / roll 4.4 deg turned onto x = 0, midline field from body x-intervals), '
                 '+X half kept (left wing, flank, legs), bmesh symmetrize with 0.4 mm weld, procedural wings mirrored, '
                 'symmetric decimation + re-symmetrize, weights computed on +X and mirrored')
(P / 'review/symmetry_gate.json').write_text(json.dumps(doc, indent=1) + '\n'); print('SYMMETRY', json.dumps({k: doc[k] for k in ('passed', 'rig')}),
      doc['v2_final_mesh']['mirror_vertex_distance'], doc['v1_reduced_mesh']['mirror_vertex_distance'])
