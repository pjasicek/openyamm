"""Dress chains (adapted from mm8_m460_claude/scripts/robe_rig.py): 16 chains of 4 bones around the skirt, roots
at the waist parented to B_Pelvis, joints on the OUTERMOST skirt surface (a ray from the body axis at each angle
and height; the grey underskirt and the inner folds take the same weights by angle and height, so the layers move
together). Skirt = piece 0 below the waist (1.04 m), excluding the sleeve cuffs. Weights: linear blend between the
two neighbouring chains by angle and the two neighbouring joints by height; the top 7.5 cm blend into B_Pelvis.
Writes scene['cloak_chains'] for dress_sim.py. In/out: work/rig_owned.blend -> work/rig_dress.blend (env)."""
import bpy, math, json, os
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
p = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p / os.environ.get('DRESS_INPUT', 'work/rig_owned.blend')))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
if rig.animation_data:
    rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis = Matrix()
bpy.context.view_layer.update()
pv = np.array([a.value for a in me.attributes['piece'].data]); co = np.array([v.co[:] for v in me.vertices])
WAIST, BLEND = 1.04, 0.075
skirt = (pv == 0) & (co[:, 2] < WAIST) & ~((co[:, 2] > 0.95) & (np.abs(co[:, 0]) > 0.19))
ids = np.flatnonzero(skirt)
faces = [tuple(f.vertices) for f in me.polygons if all(skirt[i] for i in f.vertices)]
tree = BVHTree.FromPolygons(co.tolist(), faces)
axis = Vector((0, float(co[ids][co[ids, 2] > 0.9][:, 1].mean()), 0))
zs = [1.00, 0.76, 0.52, 0.28, float(co[ids, 2].min()) + 0.005]
NCH = 16; STEP = 360 / NCH
chains = []
for c in range(NCH):
    deg = -180 + c * STEP; a = math.radians(deg); d = Vector((math.sin(a), math.cos(a), 0)); pts = []
    for z in zs:
        start = Vector((axis.x, axis.y, z)); hits = []; dist = 0
        while dist < 0.8:
            loc, n, idx, dl = tree.ray_cast(start + d * (dist + 1e-5), d, 0.8 - dist)
            if loc is None:
                break
            hits.append(loc); dist += dl + 1e-5
        if hits:
            pt = hits[-1]
        else:
            aa = np.arctan2(co[ids, 0] - axis.x, co[ids, 1] - axis.y); da = np.abs((aa - a + math.pi) % (2 * math.pi) - math.pi)
            cand = ids[(da < 0.25) & (np.abs(co[ids, 2] - z) < 0.07)]
            assert len(cand), (deg, z)
            pt = Vector(co[cand].mean(0)); pt.z = z
        pts.append(list(pt))
    chains.append({'deg': deg, 'pts': pts, 'bones': [f'Dress_{c:02}_{k}' for k in range(4)]})
bpy.context.view_layer.objects.active = rig; bpy.ops.object.mode_set(mode='EDIT')
for c in chains:
    parent = rig.data.edit_bones['B_Pelvis']
    for k, n in enumerate(c['bones']):
        b = rig.data.edit_bones.get(n) or rig.data.edit_bones.new(n)
        b.head = c['pts'][k]; b.tail = c['pts'][k + 1]; b.parent = parent; b.use_connect = k > 0; parent = b
bpy.ops.object.mode_set(mode='OBJECT')
for c in chains:
    for n in c['bones']:
        if n not in body.vertex_groups:
            body.vertex_groups.new(name=n)
groups = {g.name: g for g in body.vertex_groups}
for i in ids:
    x, y, z = co[i]; a = (math.degrees(math.atan2(x - axis.x, y - axis.y)) + 180) / STEP
    lo = int(a) % NCH; hi = (lo + 1) % NCH; t = a - math.floor(a); w = {}
    for ci, mix in ((lo, 1 - t), (hi, t)):
        u = np.interp(z, list(reversed(zs[:-1])), list(reversed(range(4))))
        k = min(3, int(u)); j = min(3, k + 1); v = u - k
        for n, amt in ((chains[ci]['bones'][k], 1 - v), (chains[ci]['bones'][j], v)):
            w[n] = w.get(n, 0) + mix * amt
    waist = float(np.clip((z - (WAIST - BLEND)) / BLEND, 0, 1)); w = {n: v * (1 - waist) for n, v in w.items()}
    w['B_Pelvis'] = waist
    for g in body.vertex_groups:
        g.remove([int(i)])
    best = sorted(w.items(), key=lambda nv: -nv[1])[:4]; total = sum(v for n, v in best)
    for n, v in best:
        if v > 1e-6:
            groups[n].add([int(i)], v / total, 'REPLACE')
bpy.context.scene['cloak_chains'] = json.dumps(chains)
assert len(rig.data.bones) <= 128
print('DRESS chains', len(chains), 'joints', len(rig.data.bones), 'skirt verts', len(ids), 'axis y', round(axis.y, 3),
      'hem z', round(zs[-1], 3), 'excluded cuff verts', int(((pv == 0) & (co[:, 2] < WAIST) & ~skirt).sum()))
bpy.ops.wm.save_as_mainfile(filepath=str(p / os.environ.get('DRESS_OUTPUT', 'work/rig_dress.blend')))
