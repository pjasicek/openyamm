"""Stage 1 (Blender): the sleeping titan. Poses the titan (sleeper.json), bakes each of its four LOD meshes into a
static mesh, lays it on its back (head toward -X, face up, front of the couch toward -Y), scales it to the game size
(work/ttn_lods.glb from scripts/expose_lods.py; sleeper.json game_scale: the creature's own 524-unit height) and lays it on the couch's deck. Model units: metres =
game units / 100; origin at the couch's bottom centre. Writes work/body.blend (Body_LOD0..3), work/body.json (bounds,
the head's underside for the headrest) and work/eyes_lod<n>.npz (UV triangles of the eye polygons, glTF v-down).
Usage: blender -b --python build_body.py"""
import json
import os
import sys

import bpy
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import pose_sleeper  # noqa: E402

cfg = json.load(open(os.path.join(HERE, 'sleeper.json')))
work = os.path.join(PROJECT, 'work')
arm, _ = pose_sleeper.pose(cfg, keep_all_meshes=True)
scene = bpy.context.scene
LODS = {'Titan': 0, 'Titan_LOD1': 1, 'Titan_LOD2': 2, 'Titan_LOD3': 3}
dg = bpy.context.evaluated_depsgraph_get()
bodies = {}
for o in list(scene.objects):
    if o.type != 'MESH' or o.name not in LODS:
        continue
    lod = LODS[o.name]
    # eye polygons, picked in the rest pose (posed positions differ only by the head's turn): the white of the eyes
    # sits on the front of the face between the brow and the cheekbones
    me_rest = o.data
    uv = me_rest.uv_layers.active.data
    eye_tris = []
    eye_ids = []
    for p in me_rest.polygons:
        c = o.matrix_world @ p.center
        if abs(c.x + 0.008) < 0.085 and 1.342 < c.z < 1.40 and c.y < -0.09:
            eye_tris.append([[uv[li].uv[0], 1.0 - uv[li].uv[1]] for li in p.loop_indices][:3])
            eye_ids.append(p.index)
    if lod == 0:
        eye_ids0 = eye_ids
    np.savez(os.path.join(work, f'eyes_lod{lod}.npz'), uv=np.array(eye_tris, np.float32))
    ev = o.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=True, depsgraph=dg)
    me.transform(o.matrix_world)
    ob = bpy.data.objects.new(f'Body_LOD{lod}', me)
    bodies[lod] = ob
    print('BODY LOD', lod, 'triangles', sum(len(p.vertices) - 2 for p in me.polygons), 'eye polys', len(eye_tris))
for o in list(scene.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for lod, ob in sorted(bodies.items()):
    scene.collection.objects.link(ob)
    ob.vertex_groups.clear()

# Lay down and scale (LOD0 sets the placement for all).
s = cfg['game_scale']
xf = Matrix.Scale(s, 4) @ pose_sleeper.LAY
for ob in bodies.values():
    ob.data.transform(xf)
co = np.array([v.co[:] for v in bodies[0].data.vertices])
lo, hi = co.min(0), co.max(0)
length = hi[0] - lo[0]
# the back's lowest points (torso and legs, beyond the head and neck zone) rest on the deck, sunk 2 cm
head_zone = lo[0] + 0.30 * length
torso = co[co[:, 0] > head_zone]
deck = cfg['couch']['deck']
dz = deck - 0.02 - torso[:, 2].min()
dx = -(lo[0] + hi[0]) / 2 + cfg.get('body_shift_x', 0.0)
dy = -(lo[1] + hi[1]) / 2
move = Matrix.Translation((dx, dy, dz))
for ob in bodies.values():
    ob.data.transform(move)
co = np.array([v.co[:] for v in bodies[0].data.vertices])
lo, hi = co.min(0), co.max(0)
# head profile along x (for the headrest): the lowest point of the body in 5 cm slices of the head end
slices = []
x = lo[0]
while x < lo[0] + 0.32 * length:
    sel = co[(co[:, 0] >= x) & (co[:, 0] < x + 0.05) & (np.abs(co[:, 1]) < 0.6)]
    if len(sel):
        slices.append([round(float(x), 3), round(float(sel[:, 2].min()), 3), round(float(sel[:, 2].max()), 3)])
    x += 0.05
eye_c = np.mean([bodies[0].data.polygons[i].center[:] for i in eye_ids0], 0)
eye_n = np.mean([bodies[0].data.polygons[i].normal[:] for i in eye_ids0], 0)
info = {'eye_centre': eye_c.round(4).tolist(), 'eye_normal': (eye_n / np.linalg.norm(eye_n)).round(3).tolist(),
        'bounds': [lo.round(4).tolist(), hi.round(4).tolist()], 'head_slices': slices, 'deck': deck}
json.dump(info, open(os.path.join(work, 'body.json'), 'w'), indent=1)
print('BODY bounds', info['bounds'])
for sl in slices:
    print('SLICE', sl)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(work, 'body.blend'))
print('BODY_DONE')
