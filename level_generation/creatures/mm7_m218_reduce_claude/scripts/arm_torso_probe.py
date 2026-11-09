"""Arm-into-torso probe (user review 2026-10-20: the spearman's arm sank into the chest; the G6 gate samples only the
forearms and hands). Per action and frame, the deepest upper-arm / forearm vertex inside the torso: torso = faces whose
vertices are all weighted > 0.6 to the spine, pelvis, neck and head bones; a vertex is inside if it lies behind the
closest torso face within a 45 deg cone of its normal (the G6 test), up to 12 cm. Upper-arm vertices within 8 cm of
the shoulder joint are skipped (the shoulder blend). Prints per action and arm the worst depth and the frames above
1.5 cm. Args: -- <blend> <action> [...]
Copied from ../mm7_m218_claude/scripts/ for the reduction, with a tie rule (ARM_TIE, default on: a nearest point on a
shared vertex/edge uses the mean normal of all faces at that distance). A .glb argument is imported instead (mesh node REA_NODE,
default Elf, renamed Body; the armature renamed Rig), so the source and reduced exports are probed the same way."""
import bpy, sys, os
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
if a[0].endswith('.glb'):
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=os.path.abspath(a[0]))
    bpy.data.objects[os.environ.get('REA_NODE', 'Elf')].name = 'Body'
    next(o for o in bpy.data.objects if o.type == 'ARMATURE').name = 'Rig'
else:
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
acts = a[1:]
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data; sc = bpy.context.scene
names = [g.name for g in body.vertex_groups]
AXIAL = ('B_Pelvis', 'B_Spine', 'B_Spine1', 'B_Spine2', 'B_Neck', 'B_Head')
nv = len(me.vertices)
ax = np.zeros(nv); part = {}
for s in 'LR':
    part[s] = {'upper': np.zeros(nv), 'fore': np.zeros(nv)}
for v in me.vertices:
    for e in v.groups:
        n = names[e.group]
        if n in AXIAL:
            ax[v.index] += e.weight
        for s in 'LR':
            if n.startswith(f'B_{s}_UpperArm'):
                part[s]['upper'][v.index] += e.weight
            if n.startswith(f'B_{s}_Forearm'):
                part[s]['fore'][v.index] += e.weight
tris = [tuple(p.vertices) for p in me.polygons if all(ax[i] > 0.6 for i in p.vertices)]
for an in acts:
    act = bpy.data.actions[an]; rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    res = {(s, k): [] for s in 'LR' for k in ('upper', 'fore')}
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
        co = np.empty(len(m.vertices) * 3); m.vertices.foreach_get('co', co); ev.to_mesh_clear()
        co = co.reshape(-1, 3)
        bvh = BVHTree.FromPolygons([Vector(c) for c in co], tris)
        for s in 'LR':
            sh = rig.matrix_world.inverted() @ (rig.matrix_world @ rig.pose.bones[f'B_{s}_UpperArm'].head)
            for k in ('upper', 'fore'):
                idx = np.where(part[s][k] > 0.5)[0]
                if k == 'upper':
                    idx = idx[np.linalg.norm(co[idx] - np.array(sh), axis=1) > 0.08]
                worst = 0.0
                for i in idx:
                    p = Vector(co[i]); hit = bvh.find_nearest(p, 0.12)
                    if hit[0] is None:
                        continue
                    d = p - hit[0]; L = d.length
                    if os.environ.get('ARM_DEBUG_POINT') and (me.vertices[i].co - Vector([float(x) for x in os.environ['ARM_DEBUG_POINT'].split(',')])).length < 0.002 and f == int(os.environ.get('ARM_DEBUG_FRAME', '-1')):
                        t = tris[hit[2]]
                        print('ARMPOINT', an, f, f'dist {L * 100:.1f} cm dot {d.dot(hit[1]) / max(L, 1e-9):.2f}', 'torso face rest',
                              [tuple(round(x, 3) for x in me.vertices[j].co) for j in t],
                              'bones', sorted({names[e.group] for j in t for e in me.vertices[j].groups if e.weight > 0.3}))
                    nrm = hit[1]
                    if os.environ.get('ARM_TIE', '1') == '1' and L > 1e-6:
                        # nearest point on a shared vertex or edge: every torso face at that distance counts (their
                        # mean normal), so the result does not depend on which tied face the BVH reports (the reduced
                        # mesh's BVH reported another face of the same unchanged corner: 9.1 cm false depth)
                        ties = [h[1] for h in bvh.find_nearest_range(p, L + 1e-5)]
                        nrm = sum(ties, Vector()).normalized() if ties else hit[1]
                    if L > 1e-6 and d.dot(nrm) < -0.7 * L:
                        if os.environ.get('ARM_DEBUG') and L > 0.015:
                            t = tris[hit[2]]
                            print('ARMDEBUG', an, f, s, k, f'{L * 100:.1f} cm vertex', i, 'rest', tuple(round(x, 3) for x in me.vertices[i].co),
                                  'torso face rest', [tuple(round(x, 3) for x in me.vertices[j].co) for j in t],
                                  'bones', sorted({names[e.group] for j in t for e in me.vertices[j].groups if e.weight > 0.3}))
                        worst = max(worst, L)
                res[(s, k)].append((f, worst))
    for (s, k), r in res.items():
        r = np.array(r)
        bad = [int(x) for x in r[r[:, 1] > 0.015, 0]]
        print(f'ARMTORSO {an} {s} {k}: worst {r[:, 1].max() * 100:.1f} cm at frame {int(r[np.argmax(r[:, 1]), 0])}; '
              f'> 1.5 cm: {bad[:20]}{" ..." if len(bad) > 20 else ""}')
