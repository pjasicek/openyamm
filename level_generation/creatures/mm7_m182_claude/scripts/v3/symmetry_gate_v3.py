"""v3 symmetry gate (Blender): per part (v3part 0 cdr1 body+wings, 1 grafted head, 2 neck loft, 3 spines) the
distance of every mirrored vertex (-x, y, z) to the surface (BVH) and to the nearest vertex; landmark pairs (eyes,
outer horn tips, wing tips, fore and hind claw tips); paired bones mirror error, centre bones on x = 0; skin weight
mirror error on the head (vertex-exact mirrored topology there). Writes review/symmetry_gate.json
(the v2 file is kept as review/symmetry_gate_v2.json)."""
import bpy, json
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
P = Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(P / 'work/v3/uv_master.blend'))
o = bpy.data.objects['Body']; me = o.data; rig = bpy.data.objects['Rig']
co = np.array([v.co[:] for v in me.vertices]); part = np.array([d.value for d in me.attributes['v3part'].data])
bvh = BVHTree.FromPolygons([Vector(c) for c in co], [list(p.vertices) for p in me.polygons])
kd = KDTree(len(co))
for i, c in enumerate(co): kd.insert(Vector(c), i)
kd.balance()
surf = np.array([bvh.find_nearest(Vector((-c[0], c[1], c[2])))[3] for c in co])
vert = np.array([kd.find(Vector((-c[0], c[1], c[2])))[2] for c in co]); partner = np.array([kd.find(Vector((-c[0], c[1], c[2])))[1] for c in co])
st = lambda d: {'median_mm': round(float(np.median(d)) * 1000, 3), 'p99_mm': round(float(np.percentile(d, 99)) * 1000, 3), 'max_mm': round(float(d.max()) * 1000, 3)}
doc = {'surface_mirror_distance': {name: st(surf[part == k]) for k, name in enumerate(['cdr1_body_wings', 'head', 'neck_loft', 'spines'])},
       'vertex_mirror_distance': {name: st(vert[part == k]) for k, name in enumerate(['cdr1_body_wings', 'head', 'neck_loft', 'spines'])}}
doc['surface_mirror_distance']['all'] = st(surf); doc['vertex_mirror_distance']['all'] = st(vert)
x, y, z = co.T; lm = {}
for s, sg in (('L', 1), ('R', -1)):
    side = x * sg > .003
    hd = side & (part == 1); lm[f'horn_tip_{s}'] = co[np.where(hd)[0][np.argmax(z[hd])]]
    w = side & (np.abs(x) > .5); lm[f'wing_tip_{s}'] = co[np.where(w)[0][np.argmax(np.abs(x[w]))]]
    fc = side & (y < -.9) & (z < .3) & (part == 0); lm[f'fore_claw_{s}'] = co[np.where(fc)[0][np.argmin(y[fc])]]
    hc = side & (y > -.3) & (y < 0) & (z < .1) & (part == 0) & (np.abs(x) > .1); lm[f'hind_claw_{s}'] = co[np.where(hc)[0][np.argmin(z[hc])]]
EYE = np.array([.0614, -1.4228, 1.0309])
for s, sg in (('L', 1), ('R', -1)):
    lm[f'eye_{s}'] = co[kd.find(Vector((sg * EYE[0], EYE[1], EYE[2])))[1]]
doc['landmarks'] = {k: {'L': np.round(lm[k + '_L'], 4).tolist(), 'R': np.round(lm[k + '_R'], 4).tolist(),
                        'mirror_error_mm': round(float(np.linalg.norm(lm[k + '_L'] - lm[k + '_R'] * [-1, 1, 1])) * 1000, 2)}
                    for k in ('eye', 'horn_tip', 'wing_tip', 'fore_claw', 'hind_claw')}
B = rig.data.bones; worst = 0.; centre = 0.
for b in B:
    if b.name.startswith('L') and 'R' + b.name[1:] in B:
        r = B['R' + b.name[1:]]; m = lambda v: Vector((-v.x, v.y, v.z))
        worst = max(worst, (m(b.head_local) - r.head_local).length, (m(b.tail_local) - r.tail_local).length)
    elif not b.name.startswith('R'):
        centre = max(centre, abs(b.head_local.x), abs(b.tail_local.x))
names = [g.name for g in o.vertex_groups]
W = np.zeros((len(co), len(names)))
for v in me.vertices:
    for g in v.groups: W[v.index, g.group] = g.weight
swap = [names.index(('R' + n[1:]) if n[:1] == 'L' and 'R' + n[1:] in names else ('L' + n[1:]) if n[:1] == 'R' and 'L' + n[1:] in names else n) for n in names]
hsel = (part == 1) & (vert < 1e-5)
doc['rig'] = {'bones': len(B), 'paired_bone_mirror_error_mm': round(worst * 1000, 4), 'centre_bone_max_abs_x_mm': round(centre * 1000, 4),
              'head_weight_mirror_max_error': round(float(np.abs(W[partner][:, swap][hsel] - W[hsel]).max()), 5), 'head_vertices_exactly_mirrored': f'{int(hsel.sum())}/{int((part == 1).sum())}'}
doc['method'] = ('cdr1 body and wings as installed (its own symmetry), grafted head exactly mirror-symmetric (v2 head, '
                 'uniform scale about x = 0), loft between two near-symmetric rings, spines on the midline')
(P / 'review/symmetry_gate.json').write_text(json.dumps(doc, indent=1) + '\n')
print('SYMMETRY', json.dumps({'surface': doc['surface_mirror_distance'], 'landmarks': {k: v['mirror_error_mm'] for k, v in doc['landmarks'].items()}, 'rig': doc['rig']}))
