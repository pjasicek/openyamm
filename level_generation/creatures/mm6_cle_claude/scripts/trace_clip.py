"""Joint and staff traces of one clip as the viewer plays it (export/mm6_cle_lod0.glb imported, keys interpolated
linearly at 48 fps like the three.js viewer); adapted from mm6_thf_claude/scripts/trace_clip.py for hands that are
part of the sleeve mesh. Args: clip [fps]. Writes work/trace_<clip>.json: per half-frame and side the world
positions (Blender Z-up, m) of shoulder, elbow, wrist and hand centroid, and
  ring_drift_mm   the hand's wrist ring (hand vertices bordering the sleeve) in the forearm frame, change from rest
  wrist_swing / wrist_twist (deg, Hand vs ForeArm), forearm_twist (ForeArm vs Arm)
  hand_turn_deg   hand rotation since the previous half-frame
the staff grip (Staff joint) and ring centre (Socket_Staff_Head joint), staff_turn_deg per half-frame, and per frame
cloak_tear_cm: the largest length gain of any cloak edge stretched more than 2x."""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector, Quaternion
from mathutils.kdtree import KDTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
args = sys.argv[sys.argv.index('--') + 1:]
CLIP = args[0]; FPS = float(args[1]) if len(args) > 1 else 48.0
# classify on the master (rest pose)
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'rig_v2.blend'))
src = bpy.data.objects['Cleric']; sme = src.data
PARTS = json.loads(bpy.context.scene['cle_parts'])
part = np.zeros(len(sme.polygons), np.int32); sme.attributes['part'].data.foreach_get('value', part)
srest = np.array([tuple(src.matrix_world @ v.co) for v in sme.vertices])
gi = {g.name: g.index for g in src.vertex_groups}
hand = {'L': [], 'R': []}
for v in sme.vertices:
    for s, k in (('LeftHand', 'L'), ('RightHand', 'R')):
        if any(x.group == gi[s] and x.weight > 0.999 for x in v.groups):
            hand[k].append(v.index)
hset = {k: set(v) for k, v in hand.items()}
ring = {k: sorted({a for e in sme.edges for a, b in (e.vertices, e.vertices[::-1]) if a in hset[k] and b not in hset[k]})
        for k in 'LR'}
cloak = sorted({v for p in sme.polygons if PARTS[part[p.index]] == 'Cloak' for v in p.vertices})
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
bpy.ops.import_scene.gltf(filepath=os.path.join(common.PROJECT, 'export', 'mm6_cle_lod0.glb'))
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
mesh = next(o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('Cleric'))
act = bpy.data.actions[CLIP] if CLIP in bpy.data.actions else next(a for a in bpy.data.actions if a.name.startswith(CLIP))
arm.animation_data.action = act
if act.slots: arm.animation_data.action_slot = act.slots[0]
for fc in ([fc for l in act.layers for s in l.strips for cb in s.channelbags for fc in cb.fcurves]
           if hasattr(act, 'layers') else act.fcurves):
    for k in fc.keyframe_points:
        k.interpolation = 'LINEAR'                         # the viewer interpolates linearly
scene.render.fps = 24
me = mesh.data
grest = np.array([tuple(mesh.matrix_world @ v.co) for v in me.vertices])   # GLB import is in the bind pose
kd = KDTree(len(srest))
for i, p in enumerate(srest):
    kd.insert(p, i)
kd.balance()
src2glb = {}
for j, p in enumerate(grest):
    _, i, d = kd.find(p)
    if d < 1e-4:
        src2glb.setdefault(i, []).append(j)
g = lambda ids: sorted({j for i in ids for j in src2glb.get(i, [])})
RING = {k: g(v) for k, v in ring.items()}; HAND = {k: g(v) for k, v in hand.items()}; CL = g(cloak)
cl_set = set(CL)
cedges = np.array([tuple(e.vertices) for e in me.edges if e.vertices[0] in cl_set and e.vertices[1] in cl_set])
rlen = np.linalg.norm(grest[cedges[:, 0]] - grest[cedges[:, 1]], axis=1)
SIDE = {'L': 'Left', 'R': 'Right'}
pb = arm.pose.bones


def W(p):
    return np.array(arm.matrix_world @ p)


def rel(child, parent):
    a = (arm.matrix_world @ pb[parent].matrix).to_3x3().normalized(); b = (arm.matrix_world @ pb[child].matrix).to_3x3().normalized()
    ra = arm.data.bones[parent].matrix_local.to_3x3(); rb = arm.data.bones[child].matrix_local.to_3x3()
    q = ((ra.inverted() @ rb).to_quaternion().inverted() @ (a.inverted() @ b).to_quaternion())
    ax = Vector((0, 1, 0)); p_ = Vector((q.x, q.y, q.z)).project(ax)
    t = Quaternion((q.w, p_.x, p_.y, p_.z)); t.normalize(); sw = q @ t.inverted()
    tw = math.degrees(2 * math.atan2(p_.length, q.w)) * (1 if p_.dot(ax) >= 0 else -1)
    return math.degrees(sw.angle), (tw + 180) % 360 - 180


f0, f1 = act.frame_range
n = int(round((f1 - f0) * FPS / 24))
rows = []; prev = {}; rest = None
for step in [-1] + list(range(n + 1)):
    if step < 0:
        arm.animation_data.action = None
        for b in pb: b.matrix_basis.identity()
        bpy.context.view_layer.update()
    else:
        arm.animation_data.action = act
        t = f0 + step * 24 / FPS
        scene.frame_set(int(math.floor(t)), subframe=t - math.floor(t))
    ev = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    P = np.array([tuple(mesh.matrix_world @ v.co) for v in m.vertices]); ev.to_mesh_clear()
    row = {'step': step, 'time': None if step < 0 else round(step / FPS, 5)}
    for k in 'LR':
        s = SIDE[k]
        M = np.array((arm.matrix_world @ pb[s + 'ForeArm'].matrix).to_3x3().normalized())
        e = W(pb[s + 'ForeArm'].head)
        ringc = M.T @ (P[RING[k]].mean(0) - e)
        sw, tw = rel(s + 'Hand', s + 'ForeArm')
        Rh = (arm.matrix_world @ pb[s + 'Hand'].matrix).to_quaternion()
        turn = math.degrees(prev[k].rotation_difference(Rh).angle) if k in prev else 0.0
        if step >= 0:
            prev[k] = Rh
        row[k] = {'shoulder': W(pb[s + 'Arm'].head).round(4).tolist(), 'elbow': e.round(4).tolist(),
                  'wrist': W(pb[s + 'Hand'].head).round(4).tolist(), 'hand': P[HAND[k]].mean(0).round(4).tolist(),
                  'ringc': ringc.tolist(), 'wrist_swing': round(sw, 1), 'wrist_twist': round(tw, 1),
                  'forearm_twist': round(rel(s + 'ForeArm', s + 'Arm')[1], 1), 'hand_turn_deg': round(turn, 1)}
    grip, head = W(pb['Staff'].head), W(pb['Socket_Staff_Head'].head)
    ax = (head - grip) / np.linalg.norm(head - grip)
    row['staff'] = {'grip': grip.round(4).tolist(), 'head': head.round(4).tolist(), 'axis': ax.round(4).tolist()}
    row['staff_turn_deg'] = round(float(np.degrees(np.arccos(np.clip(ax @ prev['S'], -1, 1)))), 1) if 'S' in prev else 0.0
    if step >= 0:
        prev['S'] = ax
    dl = np.linalg.norm(P[cedges[:, 0]] - P[cedges[:, 1]], axis=1) / np.maximum(rlen, 1e-6)
    row['cloak_tear_cm'] = round(float(np.max(np.where(dl > 2, (dl - 1) * rlen, 0))) * 100, 2)
    if step < 0:
        rest = row
    else:
        for k in 'LR':
            row[k]['ring_drift_mm'] = round(float(np.linalg.norm(np.array(row[k]['ringc']) - np.array(rest[k]['ringc'])))
                                            * 1000, 1)
            del row[k]['ringc']
        rows.append(row)
json.dump({'clip': CLIP, 'fps': FPS, 'rows': rows}, open(os.path.join(common.WORK, f'trace_{CLIP}.json'), 'w'), indent=0)
print('TRACE', CLIP, len(rows), 'rows; ring verts', {k: len(v) for k, v in RING.items()})
