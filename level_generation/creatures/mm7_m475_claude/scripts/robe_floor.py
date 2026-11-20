"""Keep the robe's skinned hem above the floor in the listed clips (Warlock Death: robe_sim.py holds the chain JOINTS
above its floor, but the cape flares out far from its chains, and once she lies down that offset points down: the
back-left hem went 11 cm under the floor; user review 2026-10-20). Per frame, for each robe chain bone (parents
first), the lowest vertex weighted at least MIN_W to it is found on the evaluated mesh; if it is under CLEAR, the bone
is turned about its head, in the vertical plane through that vertex, until the vertex clears the floor (ROUNDS per
frame, children follow; the turn is scaled by 1/weight, since hem vertices split between two chains); a turn that lowers the frame's lowest point is undone. Args: -- <in blend> <out blend> <Action> [...]"""
import bpy, sys, os, math
import numpy as np
from mathutils import Matrix, Vector
a = sys.argv[sys.argv.index('--') + 1:]
src, out, acts = a[0], a[1], a[2:]
CLEAR, MIN_W, ROUNDS = 0.004, 0.3, 4
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
scene = bpy.context.scene; rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; AW = rig.matrix_world
chain = sorted([b.name for b in rig.data.bones if b.name.startswith('Robe_')], key=lambda n: int(n.split('_')[-1]))   # parents first
gidx = {g.name: g.index for g in body.vertex_groups}
members = {}
for n in chain:
    if n in gidx:
        gi = gidx[n]
        ids = [v.index for v in body.data.vertices if any(e.group == gi and e.weight >= MIN_W for e in v.groups)]
        if ids:
            members[n] = (np.array(ids), np.array([next(e.weight for e in body.data.vertices[i].groups if e.group == gi) for i in ids]))


def mesh_co():
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    co = np.empty(len(m.vertices) * 3); m.vertices.foreach_get('co', co); ev.to_mesh_clear()
    return (np.array(body.matrix_world) @ np.c_[co.reshape(-1, 3), np.ones(len(co) // 3)].T).T[:, :3]


for name in acts:
    act = bpy.data.actions[name]; rig.animation_data_create(); rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(round(x)) for x in act.frame_range)
    before, after, turned = 0.0, 0.0, 0
    for f in range(f0, f1 + 1):
        scene.frame_set(f)
        co = mesh_co(); before = min(before, float(co[:, 2].min()))
        for _ in range(ROUNDS):
            for n, (ids, wts) in members.items():
                j = int(np.argmin(co[ids, 2])); k = ids[j]; p = Vector(co[k])
                if p.z >= CLEAR:
                    continue
                pb = rig.pose.bones[n]; M = AW @ pb.matrix; h = M.translation
                d = p - h; r = d.length
                ax = d.cross(Vector((0, 0, 1)))
                if r < 1e-4 or ax.length < 1e-6:
                    continue
                phi = math.asin(max(-1.0, min(1.0, d.z / r)))
                # the vertex moves by about its weight on this bone: aim the bone past the floor by 1/weight
                tz = p.z + (CLEAR - p.z) / max(wts[j], 0.3)
                th = math.asin(max(-1.0, min(1.0, (tz - h.z) / r))) - phi
                if th <= 0:
                    continue
                R = Matrix.Translation(h) @ Matrix.Rotation(th, 4, ax.normalized()) @ Matrix.Translation(-h)
                q0 = pb.rotation_quaternion.copy() if pb.rotation_mode == 'QUATERNION' else None
                low0 = float(co[:, 2].min())
                pb.matrix = AW.inverted() @ (R @ M); bpy.context.view_layer.update()
                co2 = mesh_co()
                if float(co2[:, 2].min()) < low0 - 1e-4 and q0 is not None:
                    pb.rotation_quaternion = q0; bpy.context.view_layer.update()
                    continue
                pb.rotation_mode = 'QUATERNION'; pb.keyframe_insert('rotation_quaternion', frame=f); turned += 1
                co = co2
        after = min(after, float(co[:, 2].min()))
    print('ROBEFLOOR', name, 'frames', f1 - f0 + 1, 'lowest cm before', round(before * 100, 1), 'after', round(after * 100, 1), 'turns', turned)
rig.animation_data.action = None
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
