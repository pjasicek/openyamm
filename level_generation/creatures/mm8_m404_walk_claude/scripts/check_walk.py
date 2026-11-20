"""Walking checks on a GLB (Blender): foot slip of planted sole vertices against the clip's ground speed, the
closest approach of tail to legs, and of the sword to the body below the hands, per frame at 240 Hz.
Usage: blender -b -P check_walk.py -- <body.glb> <sword.glb> <stride_m> <out.json>"""
import bpy, sys, os, json, numpy as np
from mathutils import kdtree
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from glb_io import Glb
from gltf_pose import GltfPose
a = sys.argv[sys.argv.index('--') + 1:]
glb, sword_glb, stride, out = a[0], a[1], float(a[2]), a[3]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
body = next(o for o in bpy.data.objects if o.type == 'MESH' and o.name == 'M404') if 'M404' in bpy.data.objects else \
    max((o for o in bpy.data.objects if o.type == 'MESH'), key=lambda o: len(o.data.polygons))
gp = GltfPose(Glb(glb).json, rig)
before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=sword_glb)
sword = [o for o in set(bpy.data.objects) - before if o.type == 'MESH']
roots = {o: o.matrix_world.copy() for o in sword}
names = [g.name for g in body.vertex_groups]
def group_ids(pred, wmin=.5):
    return np.array([v.index for v in body.data.vertices if sum(g.weight for g in v.groups if pred(names[g.group])) > wmin])
legs = group_ids(lambda n: any(k in n for k in ('Thigh', 'Calf', 'Foot', 'Toe')))
tail = group_ids(lambda n: n.startswith('Tail'), .5)
torso = group_ids(lambda n: n in ('B_Pelvis', 'B_Spine', 'B_Spine1', 'B_Spine2', 'B_Loincloth') or 'Thigh' in n or 'Calf' in n)
soles = {s: group_ids(lambda n, s=s: n in (f'B_{s}_Foot', f'B_{s}_Toe0')) for s in 'LR'}
act = next(x for x in bpy.data.actions if x.name.split('|')[-1] == 'Walking')
rig.animation_data.action = act; rig.animation_data.action_slot = act.slots[0]
scene = bpy.context.scene; fps = scene.render.fps / scene.render.fps_base
dur = (act.frame_range[1] - act.frame_range[0]) / fps
v = stride / dur; n = int(round(dur * 240))
prev = None; slip = {s: [] for s in 'LR'}; contact_slip = {s: [] for s in 'LR'}; acc = {s: 0.0 for s in 'LR'}
tail_leg, sword_body, spikes = [], [], []
floor = None
for i in range(n + 1):
    t = dur * i / n; f = act.frame_range[0] + t * fps
    scene.frame_set(int(f), subframe=f % 1); bpy.context.view_layer.update()
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    co = np.array([(body.matrix_world @ x.co)[:] for x in m.vertices]); ev.to_mesh_clear()
    if floor is None:
        floor = min(co[soles['L'], 2].min(), co[soles['R'], 2].min())
    if prev is not None:
        for s in 'LR':
            ids = soles[s]; both = ids[(co[ids, 2] < floor + .004) & (prev[ids, 2] < floor + .004)]
            if len(both):
                d = co[both] - prev[both]; d[:, 1] -= v * dur / n
                sp = np.linalg.norm(d[:, :2], axis=1).min() / (dur / n)    # the best-anchored contact point
                slip[s].append(sp); acc[s] += sp * dur / n; spikes.append((round(sp, 3), s, round(t * 48, 2)))
            elif acc[s] > 0:
                contact_slip[s].append(acc[s]); acc[s] = 0.0
    prev = co
    kd = kdtree.KDTree(len(legs))
    for j, idx in enumerate(legs):
        kd.insert(co[idx], j)
    kd.balance()
    tail_leg.append(min(kd.find(co[k])[2] for k in tail[::3]))
    G = rig.matrix_world @ rig.pose.bones['Socket_Sword'].matrix @ gp.C['Socket_Sword'].inverted()
    pts = []
    for o in sword:
        M = G @ roots[o]; pts += [(M @ x.co) for x in o.data.vertices]
    kd2 = kdtree.KDTree(len(torso))
    for j, idx in enumerate(torso):
        kd2.insert(co[idx], j)
    kd2.balance()
    sword_body.append(min(kd2.find(p)[2] for p in pts[::4]))
for s in 'LR':
    if acc[s] > 0:
        contact_slip[s].append(acc[s])
rep = {'ground_speed_m_s': v, 'max_contact_slip_speed_m_s': {s: float(max(slip[s])) for s in 'LR'},
       'median_contact_slip_speed_m_s': {s: float(np.median(slip[s])) for s in 'LR'},
       'slip_per_contact_mm': {s: [round(x * 1000, 1) for x in contact_slip[s]] for s in 'LR'},
       'worst_slip_frames_48hz': sorted(spikes, reverse=True)[:6],
       'tail_to_leg_min_mm': float(min(tail_leg) * 1000), 'sword_to_torso_legs_min_mm': float(min(sword_body) * 1000)}
json.dump(rep, open(out, 'w'), indent=1); print('CHECK', json.dumps(rep), flush=True)
