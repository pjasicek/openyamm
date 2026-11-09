"""Arm and hand gate for the lizardman peasant rig (Arm and hand gate, CLAUDE_HUMANOID_NPC_PLAYBOOK.md):
per sampled frame, arm skin vertices inside the torso/tunic surface (closed-skin inside test via nearest-face normal),
minimum arm-to-torso clearance, elbow angle, wrist swing and forearm twist.
Usage: blender -b -P arm_gate.py -- <blend> <action>[,<action>...] [step]"""
import bpy, sys, math, json, os
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
actions = argv[1].split(','); step = float(argv[2]) if len(argv) > 2 else 2
rig = bpy.data.objects['Lizardman_Rig']; body = bpy.data.objects['Lizardman_Body']; sc = bpy.context.scene
rig.animation_data.action = None
for t in rig.animation_data.nla_tracks: t.mute = True
names = [g.name for g in body.vertex_groups]
nv = len(body.data.vertices)
W = np.zeros((nv, len(names)))
for v in body.data.vertices:
    for g in v.groups: W[v.index, g.group] = g.weight
def share(keys):
    cols = [i for i, n in enumerate(names) if any(k in n for k in keys)]
    return W[:, cols].sum(1)
arm = {s: share([s + 'Arm', s + 'ForeArm', s + 'Hand', s + 'Thumb', s + 'Digit']) for s in ['Left', 'Right']}
torso = share(['Hips', 'Spine', 'UpLeg'])
armv = {s: np.flatnonzero(arm[s] > .6) for s in arm}
faces = np.array([p.vertices[:] for p in body.data.polygons if len(p.vertices) == 3])
tri_torso = faces[(torso[faces] > .6).all(1)]
def frame_eval():
    dg = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(dg); me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    ev.to_mesh_clear(); M = np.array(body.matrix_world)
    return co @ M[:3, :3].T + M[:3, 3]
def angles(s):
    pb = rig.pose.bones
    sh = pb[s + 'Arm'].head; el = pb[s + 'ForeArm'].head; wr = pb[s + 'Hand'].head
    elbow = math.degrees((sh - el).angle(wr - el))
    fa = pb[s + 'ForeArm'].matrix.to_3x3(); hd = pb[s + 'Hand'].matrix.to_3x3()
    swing = math.degrees((fa @ Vector((0, 1, 0))).angle(hd @ Vector((0, 1, 0))))
    q = pb[s + 'ForeArm'].matrix_basis.to_quaternion(); tw = math.degrees(q.to_swing_twist('Y')[1])
    return elbow, swing, tw
report = {}
for name in actions:
    a = bpy.data.actions[name]; rig.animation_data.action = a; rig.animation_data.action_slot = a.slots[0]
    end = a.frame_range[1]; rows = []
    for f in np.arange(0, end + 1e-6, step):
        sc.frame_set(int(f), subframe=float(f % 1)); co = frame_eval()
        bvh = BVHTree.FromPolygons([Vector(c) for c in co], tri_torso.tolist())
        row = {'frame': float(f)}
        for s in ['Left', 'Right']:
            inside = 0; clear = 9
            for i in armv[s]:
                p = Vector(co[i]); hit = bvh.find_nearest(p)
                if hit[0] is None: continue
                d = (p - hit[0]).dot(hit[1]); clear = min(clear, hit[3])
                if d < 0 and hit[3] < .05:
                    inside += 1
                    if os.environ.get("GATE_WHERE"): print("INSIDE", s, f, i, [round(x, 3) for x in co[i]], round(hit[3] * 1000, 1), [round(w, 2) for w in W[i][W[i] > .05]], [names[k] for k in np.flatnonzero(W[i] > .05)])
            e, sw, tw = angles(s)
            row[s] = dict(inside=inside, clear_mm=round(clear * 1000, 1), elbow=round(e, 1), wrist_swing=round(sw, 1), forearm_twist=round(tw, 1))
        lows = co[:, 2].min(); row['lowest_mm'] = round(lows * 1000, 2)
        rows.append(row)
    report[name] = rows
    worst = {s: dict(inside=max(r[s]['inside'] for r in rows), clear_mm=min(r[s]['clear_mm'] for r in rows),
                     elbow=[min(r[s]['elbow'] for r in rows), max(r[s]['elbow'] for r in rows)],
                     wrist_swing=max(r[s]['wrist_swing'] for r in rows),
                     twist=[min(r[s]['forearm_twist'] for r in rows), max(r[s]['forearm_twist'] for r in rows)]) for s in ['Left', 'Right']}
    print('GATE', name, json.dumps(worst), 'lowest_mm', min(r['lowest_mm'] for r in rows), 'arm verts', {s: len(armv[s]) for s in armv})
out = argv[3] if len(argv) > 3 else None
if out: open(out, 'w').write(json.dumps(report, indent=1))
