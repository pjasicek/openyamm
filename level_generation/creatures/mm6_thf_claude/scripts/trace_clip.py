"""Joint and prop traces of one clip as the viewer plays it (export/mm6_thf_lod0.glb imported, keys interpolated
linearly at 48 fps like the three.js viewer), for the self-check loop. Args: clip [fps]. Writes
work/trace_<clip>.json: per half-frame and side the world positions (Blender Z-up, m) of shoulder (Arm head), elbow,
wrist (Hand head), hand-shell centroid, dagger pommel ('grip') and point ('tip', from the mesh), and the metrics
  wrist_gap_mm   mean distance of the hand shell's wrist ring to the nearest bracer/sleeve surface, minus rest
  ring_drift_mm  wrist ring centroid in the forearm frame (elbow -> wrist axis), change from rest
  bracer_drift_mm bracer centroid in the same forearm frame, change from rest
  wrist_swing / wrist_twist (deg, Hand vs ForeArm), forearm_twist (ForeArm vs Arm), elbow_deg
  hand_turn_deg  hand rotation since the previous half-frame
  tip_speed      dagger-tip travel since the previous half-frame (m)
and per frame the most stretched cloak edge (deformed / rest length) with its rest height, and cloak_tear_cm: the
largest length gain of any cloak edge stretched more than 2x."""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector, Quaternion
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
args = sys.argv[sys.argv.index('--') + 1:]
CLIP = args[0]; FPS = float(args[1]) if len(args) > 1 else 48.0
# classify on the master
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'rig_v2.blend'))
src = bpy.data.objects['Thief']; sme = src.data
PARTS = json.loads(bpy.context.scene['thf_parts'])
REG = json.loads(bpy.context.scene['thf_uv_regions'])
part = np.zeros(len(sme.polygons), np.int32); sme.attributes['part'].data.foreach_get('value', part)
ureg = np.zeros(len(sme.polygons), np.int32); sme.attributes['uv_region'].data.foreach_get('value', ureg)
srest = np.array([tuple(src.matrix_world @ v.co) for v in sme.vertices])
vpart = {}
for p in sme.polygons:
    for v in p.vertices:
        vpart.setdefault(v, set()).add(PARTS[part[p.index]])
import bmesh
bm = bmesh.new(); bm.from_mesh(sme)
ring = {'L': [], 'R': []}
for e in bm.edges:
    if e.is_boundary and all(vpart.get(v.index) == {'Hand'} for v in e.verts):
        for v in e.verts:
            ring['L' if srest[v.index][0] > 0 else 'R'].append(v.index)
bm.free()
ring = {k: sorted(set(v)) for k, v in ring.items()}
hand = {k: [i for i, ps in vpart.items() if ps == {'Hand'} and (srest[i][0] > 0) == (k == 'L')] for k in 'LR'}
bracer = {k: [i for i, ps in vpart.items() if ps == {'Bracer'} and (srest[i][0] > 0) == (k == 'L')] for k in 'LR'}
sleeve = {}
for k in 'LR':
    c = srest[ring[k]].mean(0)
    sleeve[k] = [i for i, ps in vpart.items() if ps == {'Torso'} and np.linalg.norm(srest[i] - c) < 0.07]
cloak = sorted(i for i, ps in vpart.items() if ps == {'Cloak'})
# dagger tip and pommel from the mesh (glTF stores no bone tails: the importer's guessed Dagger tails gave wrong blade
# directions): per side the dagger vertices farthest along / against the seat axis
seat = json.loads(bpy.context.scene['thf_daggers'])
dtip, dpom = {}, {}
for k in 'LR':
    ids = [i for i, ps in vpart.items() if ps == {'Dagger'} and (srest[i][0] > 0) == (k == 'L')]
    ax = np.array(seat[k]['axis'])
    proj = srest[ids] @ ax
    dtip[k] = [ids[int(np.argmax(proj))]]; dpom[k] = [ids[int(np.argmin(proj))]]
# load the runtime GLB
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
bpy.ops.import_scene.gltf(filepath=os.path.join(common.PROJECT, 'export', 'mm6_thf_lod0.glb'))
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
mesh = next(o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('Thief'))
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
RING = {k: g(v) for k, v in ring.items()}; HAND = {k: g(v) for k, v in hand.items()}
BR = {k: g(v) for k, v in bracer.items()}; SL = {k: g(v) for k, v in sleeve.items()}; CL = g(cloak)
TIP = {k: g(v) for k, v in dtip.items()}; POM = {k: g(v) for k, v in dpom.items()}
edges = np.array([tuple(e.vertices) for e in me.edges])
cl_set = set(CL); cedges = np.array([e for e in edges if e[0] in cl_set and e[1] in cl_set])
rlen = np.linalg.norm(grest[cedges[:, 0]] - grest[cedges[:, 1]], axis=1)
faces = [tuple(p.vertices) for p in me.polygons]
fset = {k: [f for f in faces if all(v in set(BR[k]) | set(SL[k]) for v in f)] for k in 'LR'}
SIDE = {'L': 'Left', 'R': 'Right'}
pb = arm.pose.bones


def W(p):
    return np.array(arm.matrix_world @ p)


def frame_of(side):
    e = W(pb[SIDE[side] + 'ForeArm'].head); w = W(pb[SIDE[side] + 'Hand'].head)
    x = (w - e) / np.linalg.norm(w - e)
    M = np.array((arm.matrix_world @ pb[SIDE[side] + 'ForeArm'].matrix).to_3x3().normalized())
    return e, M


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
rows = []; prev = {}
rest_metrics = None
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
        tree = BVHTree.FromPolygons([Vector(x) for x in P], fset[k]) if fset[k] else None
        gap = float(np.mean([tree.find_nearest(Vector(P[i]))[3] for i in RING[k]])) if tree else 0.0
        e, M = frame_of(k)
        ringc = M.T @ (P[RING[k]].mean(0) - e); brc = M.T @ (P[BR[k]].mean(0) - e)
        s = SIDE[k]
        sw, tw = rel(s + 'Hand', s + 'ForeArm')
        ftw = rel(s + 'ForeArm', s + 'Arm')[1]
        sh, el, wr = W(pb[s + 'Arm'].head), W(pb[s + 'ForeArm'].head), W(pb[s + 'Hand'].head)
        u, v = el - sh, wr - el
        elbow = math.degrees(math.acos(np.clip(u @ v / np.linalg.norm(u) / np.linalg.norm(v), -1, 1)))
        dg, dt = P[POM[k]].mean(0), P[TIP[k]].mean(0)     # pommel and blade point (mesh)
        Rh = (arm.matrix_world @ pb[s + 'Hand'].matrix).to_quaternion()
        turn = math.degrees(prev[k][1].rotation_difference(Rh).angle) if k in prev else 0.0
        speed = float(np.linalg.norm(dt - prev[k][0])) if k in prev else 0.0
        if step >= 0:
            prev[k] = (dt, Rh)
        row[k] = {'shoulder': sh.round(4).tolist(), 'elbow': el.round(4).tolist(), 'wrist': wr.round(4).tolist(),
                  'hand': P[HAND[k]].mean(0).round(4).tolist(), 'grip': dg.round(4).tolist(), 'tip': dt.round(4).tolist(),
                  'gap': gap, 'ringc': ringc.tolist(), 'brc': brc.tolist(), 'wrist_swing': round(sw, 1),
                  'wrist_twist': round(tw, 1), 'forearm_twist': round(ftw, 1), 'elbow_deg': round(elbow, 1),
                  'hand_turn_deg': round(turn, 1), 'tip_speed': round(speed, 4)}
    dl = np.linalg.norm(P[cedges[:, 0]] - P[cedges[:, 1]], axis=1) / np.maximum(rlen, 1e-6)
    i = int(np.argmax(dl))
    row['cloak_stretch'] = round(float(dl[i]), 2); row['cloak_stretch_z'] = round(float(grest[cedges[i, 0]][2]), 3)
    row['cloak_stretch_p95'] = round(float(np.percentile(dl, 99)), 2)
    gain = (dl - 1) * rlen                                   # absolute opening of each stretched edge (m)
    row['cloak_tear_cm'] = round(float(np.max(np.where(dl > 2, gain, 0))) * 100, 2)
    if step < 0:
        rest_metrics = row
    else:
        for k in 'LR':
            r = row[k]; r0 = rest_metrics[k]
            r['wrist_gap_mm'] = round((r['gap'] - r0['gap']) * 1000, 1)
            r['ring_drift_mm'] = round(float(np.linalg.norm(np.array(r['ringc']) - np.array(r0['ringc']))) * 1000, 1)
            r['bracer_drift_mm'] = round(float(np.linalg.norm(np.array(r['brc']) - np.array(r0['brc']))) * 1000, 1)
            for x in ('gap', 'ringc', 'brc'):
                del r[x]
        rows.append(row)
for k in 'LR':
    for x in ('gap', 'ringc', 'brc'):
        rest_metrics[k].pop(x, None)
json.dump({'clip': CLIP, 'fps': FPS, 'rest': rest_metrics, 'rows': rows,
           'counts': {'ring': {k: len(v) for k, v in RING.items()}, 'bracer': {k: len(v) for k, v in BR.items()},
                      'sleeve': {k: len(v) for k, v in SL.items()}}},
          open(os.path.join(common.WORK, f'trace_{CLIP}.json'), 'w'), indent=0)
print('TRACE', CLIP, len(rows), 'rows; counts', {k: len(v) for k, v in RING.items()}, {k: len(v) for k, v in BR.items()},
      {k: len(v) for k, v in SL.items()})
for r in rows:
    print('ROW %2d' % r['step'], ' '.join('%s gap %5.1f ring %5.1f br %5.1f sw %4.0f tw %4.0f ftw %4.0f turn %4.0f' % (
        k, r[k]['wrist_gap_mm'], r[k]['ring_drift_mm'], r[k]['bracer_drift_mm'], r[k]['wrist_swing'], r[k]['wrist_twist'],
        r[k]['forearm_twist'], r[k]['hand_turn_deg']) for k in 'RL'), 'cloak %.2f @%.2f' % (r['cloak_stretch'], r['cloak_stretch_z']))
