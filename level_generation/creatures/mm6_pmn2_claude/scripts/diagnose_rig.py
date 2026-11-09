"""Hands and feet on the Meshy rig: which bones weight the fist shells, which clips key finger/face bones, and the
boot sole (lowest 15 % of each boot) height/tilt per frame of every clip."""
import bpy, sys, os, json, collections, math
import numpy as np
from mathutils import Vector
src = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(src))
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
m = bpy.data.objects['Mage']; me = m.data
co = np.array([tuple(m.matrix_world @ v.co) for v in me.vertices])
print('MESHBOUNDS', co.min(0).round(3), co.max(0).round(3))
gname = {g.index: g.name for g in m.vertex_groups}
# fist shells: loose parts beyond the wrist
import bmesh
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
comp = [-1] * len(bm.verts); n = 0
for v in bm.verts:
    if comp[v.index] >= 0: continue
    st = [v]; comp[v.index] = n
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if comp[y.index] < 0: comp[y.index] = n; st.append(y)
    n += 1
comp = np.array(comp)
for c in range(n):
    idx = np.where(comp == c)[0]; cc = co[idx].mean(0)
    if abs(cc[0]) > 0.38 and len(idx) > 200:
        tot = collections.Counter()
        for i in idx:
            for g in me.vertices[i].groups:
                tot[gname[g.group]] += g.weight
        s = sum(tot.values())
        print('FIST', 'x', round(cc[0], 3), 'verts', len(idx), {k: round(v / s, 3) for k, v in tot.most_common(12)})
# which bones are keyed / actually move in each action
for act in bpy.data.actions:
    moved = set()
    for fc in getattr(act, 'fcurves', []):
        pts = [k.co[1] for k in fc.keyframe_points]
        if pts and max(pts) - min(pts) > 1e-3:
            moved.add(fc.data_path.split('"')[1])
    if not moved and hasattr(act, 'layers'):
        for layer in act.layers:
            for strip in layer.strips:
                for cb in strip.channelbags:
                    for fc in cb.fcurves:
                        pts = [k.co[1] for k in fc.keyframe_points]
                        if pts and max(pts) - min(pts) > 1e-3:
                            moved.add(fc.data_path.split('"')[1])
    extra = sorted(b for b in moved if not b.startswith('mixamorig:') or 'Hand' in b and 'Hand' != b[-4:])
    print('ACT', act.name, 'moving bones', len(moved), 'finger/face bones moving', extra[:20])
# boots: verts with z < 0.45 and |x| > 0.05
boot = {s: np.where((co[:, 2] < 0.45) & (co[:, 0] * s > 0.05))[0] for s in (1, -1)}
sole = {s: boot[s][co[boot[s], 2] < 0.035] for s in (1, -1)}
print('SOLE verts', {s: len(v) for s, v in sole.items()})
deps = bpy.context.evaluated_depsgraph_get()
arm.animation_data_create()
for act in bpy.data.actions:
    arm.animation_data.action = act
    if hasattr(arm.animation_data, 'action_slot') and act.slots:
        arm.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(round(x)) for x in act.frame_range)
    rows = []
    for f in range(f0, f1 + 1, max(1, (f1 - f0) // 12)):
        bpy.context.scene.frame_set(f)
        ev = m.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
        P = np.array([tuple(m.matrix_world @ v.co) for v in ev.vertices]); m.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh_clear()
        r = [f]
        for s in (1, -1):
            sp = P[sole[s]]
            # sole plane normal via SVD
            c = sp.mean(0); u, sv, vt = np.linalg.svd(sp - c); nrm = vt[2] * np.sign(vt[2][2])
            tilt = math.degrees(math.acos(min(1, abs(nrm[2]))))
            pitch = math.degrees(math.atan2(nrm[1], nrm[2])); roll = math.degrees(math.atan2(nrm[0], nrm[2]))
            r += ['LR'[s < 0], round(float(sp[:, 2].min()), 3), round(float(sp[:, 2].max()), 3), round(pitch, 1), round(roll, 1)]
        rows.append(r)
    print('SOLES', act.name, 'frame, side, zmin, zmax, pitch, roll ->')
    for r in rows: print('   ', r)
