"""Wing-root gate (Blender, 48 Hz): edges of the wing material within 0.25 m of the wing/body junction (vertices shared
by the body and wing materials) and body edges within 0.08 m of it: edge stretch p99 / max per clip; the root lag
(mean displacement of root-band wing vertices relative to the rest pose, as a fraction of the Wing0 tail
displacement: 1 = moves with the wing, 0 = static); interpenetration proxy: wing root vertices that end up inside
the body (closest body triangle normal points away from them by more than 5 mm). Usage: blender -b <blend> -P
wing_root_gate.py -- <out.json>"""
import bpy, json, sys
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
out = sys.argv[sys.argv.index('--') + 1]
o = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']; me = o.data; sc = bpy.context.scene
wslot = [i for i, m in enumerate(me.materials) if m and 'Wing' in m.name] or [2]
fv = [(p.material_index in wslot, list(p.vertices)) for p in me.polygons]
vw = np.zeros(len(me.vertices), bool); vb = np.zeros(len(me.vertices), bool)
for w, vs in fv:
    (vw if w else vb)[vs] = True
rest = np.array([v.co[:] for v in me.vertices]); junc = vw & vb
from mathutils.kdtree import KDTree
kd = KDTree(int(junc.sum()))
for i, x in enumerate(rest[junc]): kd.insert(Vector(x), i)
kd.balance(); dj = np.array([kd.find(Vector(x))[2] for x in rest])
E = np.array([e.vertices[:] for e in me.edges]); L0 = np.linalg.norm(rest[E[:, 0]] - rest[E[:, 1]], axis=1)
we = vw[E].all(1) & (dj[E].max(1) < .25) & (L0 > 1e-5); be = vb[E].all(1) & ~vw[E].any(1) & (dj[E].max(1) < .08) & (L0 > 1e-5)
band = vw & (dj > .03) & (dj < .15)
bodyf = [vs for w, vs in fv if not w]
res = {}
for act in bpy.data.actions:
    if act.name in ('Cast',): continue
    rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    f0, f1 = act.frame_range; sw, sb, lag, pen = [], [], [], 0
    for k in range(int((f1 - f0) * 2) + 1):
        fr = f0 + k * .5; sc.frame_set(int(fr), subframe=fr % 1)
        ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
        c = np.empty(len(m.vertices) * 3); m.vertices.foreach_get('co', c); c = c.reshape(-1, 3); ev.to_mesh_clear()
        r = np.linalg.norm(c[E[:, 0]] - c[E[:, 1]], axis=1) / np.maximum(L0, 1e-9); r = np.maximum(r, 1 / np.maximum(r, 1e-9))
        sw.append(r[we]); sb.append(r[be])
        for s in 'LR':
            pb = rig.pose.bones[f'{s}Wing0']; t_now = np.array(rig.matrix_world @ pb.tail); t_rest = np.array(rig.matrix_world @ pb.bone.tail_local)
            dw = np.linalg.norm(t_now - t_rest)
            sel = band & ((rest[:, 0] > 0) == (s == 'L'))
            if dw > .02: lag.append(float(np.linalg.norm(c[sel] - rest[sel], axis=1).mean() / dw))
        if k % 4 == 0:
            bvh = BVHTree.FromPolygons([Vector(x) for x in c], bodyf)
            for i in np.where(band)[0][::3]:
                hit = bvh.find_nearest(Vector(c[i]))
                if hit[0] is not None and (Vector(c[i]) - hit[0]).dot(hit[1]) < -.005: pen += 1
    sw = np.concatenate(sw); sb = np.concatenate(sb)
    res[act.name] = {'wing_root_stretch_p99': round(float(np.percentile(sw, 99)), 3), 'wing_root_stretch_max': round(float(sw.max()), 3),
                     'body_near_root_stretch_p99': round(float(np.percentile(sb, 99)), 3), 'root_follow_ratio_mean': round(float(np.mean(lag)), 3) if lag else None,
                     'root_vertices_inside_body_samples': pen}
json.dump(res, open(out, 'w'), indent=1); print('WINGROOT', json.dumps(res))
