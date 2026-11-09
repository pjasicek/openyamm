"""Trace one clip of a runtime GLB as the viewer plays it (linear keys, 48 fps) and gate it with the thief's limits
(../mm6_thf_claude/scripts/trace_gate.py): per side the wrist seam gap (hand-shell wrist ring to the nearest
forearm/bracer surface, change from rest, mm), wrist swing / twist (Hand vs Forearm), forearm twist (Forearm vs
UpperArm), elbow angle, hand turn per half-frame, plus the right hand's path (for the impact check).
Args: -- <glb> <clip> -> work/trace_<clip>.json, prints TRACE lines and GATE pass/fail."""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import bmesh
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
glb, clip = sys.argv[sys.argv.index('--') + 1:][:2]
LIMITS = {'wrist_gap_mm': 3.0, 'wrist_swing': 45.0, 'wrist_twist': 45.0, 'forearm_twist': 90.0, 'hand_turn_deg': 45.0}
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
body = max((o for o in bpy.data.objects if o.type == 'MESH' and o.parent == rig and o.visible_get()),
           key=lambda o: len(o.data.polygons))
for o in bpy.data.objects:
    if o.type == 'MESH' and o is not body:
        o.hide_viewport = True
sc = bpy.context.scene
act = bpy.data.actions[next(a.name for a in bpy.data.actions if a.name.split('_')[0] == clip or a.name == clip)]
rig.animation_data.action = act
if getattr(act, 'slots', None) is not None and len(act.slots):
    rig.animation_data.action_slot = act.slots[0]


def fcurves(action):
    fcs = list(getattr(action, 'fcurves', []) or [])
    if not fcs and hasattr(action, 'layers'):
        fcs = [fc for l in action.layers for s in l.strips for cb in s.channelbags for fc in cb.fcurves]
    return fcs


for fc in fcurves(act):
    for k in fc.keyframe_points:
        k.interpolation = 'LINEAR'
f0, f1 = act.frame_range; fps = sc.render.fps / sc.render.fps_base
pb = rig.pose.bones
# pieces of the (welded) mesh: hand shells are separate pieces dominated by hand/finger bones
bm = bmesh.new(); bm.from_mesh(body.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
names = {g.index: g.name for g in body.vertex_groups}
me = body.data
dom = {}
for v in me.vertices:
    gs = sorted(v.groups, key=lambda g: -g.weight)
    dom[v.index] = names[gs[0].group] if gs else ''
co_rest = np.array([v.co[:] for v in me.vertices])


def deformed():
    dg = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(dg)
    m = ev.to_mesh(); out = np.array([body.matrix_world @ v.co for v in m.vertices]); ev.to_mesh_clear(); return out


def ring_ids(side):
    s = 'L' if side == 'L' else 'R'
    hand = [i for i, n in dom.items() if n.startswith(f'B_{s}_Hand') or n.startswith(f'B_{s}_Finger')]
    w = np.array(rig.matrix_world @ rig.data.bones[f'B_{s}_Hand'].head_local)
    d = np.linalg.norm(co_rest[hand] - w, axis=1)
    return [hand[i] for i in np.argsort(d)[:12]]


arm_ids = {s: [i for i, n in dom.items() if n in (f'B_{s}_Forearm', f'B_{s}_ForearmTwist')] for s in 'LR'}
rings = {s: ring_ids(s) for s in 'LR'}
tris = [tuple(p.vertices) for p in me.polygons]


def gap(P, s):
    ids = set(arm_ids[s]); ft = [t for t in tris if all(i in ids for i in t)]
    tree = BVHTree.FromPolygons([tuple(p) for p in P], ft)
    return float(np.mean([tree.find_nearest(Vector(P[i]))[3] for i in rings[s]]) * 1000)


def ang(m):
    return math.degrees(m.to_quaternion().angle)


def swing_twist(child, parent):
    rel = (parent.matrix.to_3x3().inverted() @ child.matrix.to_3x3()).to_quaternion()
    tw = 2 * math.degrees(math.atan2(rel.y, rel.w)); tw = (tw + 180) % 360 - 180
    sw = math.degrees(math.acos(max(-1, min(1, (rel.to_matrix() @ Vector((0, 1, 0))).y))))
    return sw, tw


sc.frame_set(int(f0)); rest_gap = {s: gap(deformed(), s) for s in 'LR'}
rows, prevq = [], {}
n = int(round((f1 - f0) / fps * 48))
for i in range(n + 1):
    f = f0 + i / 48 * fps; sc.frame_set(int(f), subframe=f - int(f))
    P = deformed(); r = {'step': i, 't': round(i / 48, 4)}
    for s in 'LR':
        h, fa, ua = pb[f'B_{s}_Hand'], pb[f'B_{s}_Forearm'], pb[f'B_{s}_UpperArm']
        ws, wt = swing_twist(h, fa); _, ft = swing_twist(fa, ua)
        q = (rig.matrix_world @ h.matrix).to_quaternion()
        turn = math.degrees(q.rotation_difference(prevq[s]).angle) if s in prevq else 0.0; prevq[s] = q
        turn = min(turn, 360 - turn)
        r[s] = {'wrist_gap_mm': round(gap(P, s) - rest_gap[s], 2), 'wrist_swing': round(ws, 1), 'wrist_twist': round(wt, 1),
                'forearm_twist': round(ft, 1), 'hand_turn_deg': round(turn, 1),
                'elbow_deg': round(math.degrees((ua.matrix.to_3x3() @ Vector((0, 1, 0))).angle(fa.matrix.to_3x3() @ Vector((0, 1, 0)))), 1),
                'wrist': [round(x, 4) for x in (rig.matrix_world @ h.head)]}
    rows.append(r)
json.dump({'clip': clip, 'rows': rows}, open(os.path.join(HERE, 'work', f'trace_{clip}.json'), 'w'))
bad = []
for s in 'LR':
    for m, lim in LIMITS.items():
        v, st = max((abs(r[s][m]), r['step']) for r in rows)
        print(f'TRACE {clip} {s} {m} max {v:.1f} (limit {lim}) at half-frame {st}')
        if v > lim:
            bad.append(f'{s} {m} {v:.1f}')
yw = [r['R']['wrist'][1] for r in rows]; k = int(np.argmin(yw))
print(f'TRACE {clip} R wrist furthest forward at {rows[k]["t"]:.3f} s (y {yw[k]:.3f}, rest {yw[0]:.3f})')
print('GATE', 'PASS' if not bad else 'FAIL ' + ', '.join(bad))
