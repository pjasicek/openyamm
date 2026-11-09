"""Where the fists hold the mallet: finger and thumb bone heads/tails (both hands) over every frame of every clip,
moved into the rest pose through the mallet bone (Xhammer), projected on the mallet's axis (PCA of its rest
vertices). Only frames whose joint lies within NEAR of the axis count (holding, not passing). Writes
work/grip_band.json (t ranges per hand, axis, centre) for make_groups.py. Usage: blender -b -P grip_band.py"""
import os, json, bpy, numpy as np
from mathutils import Matrix
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NEAR = float(os.environ.get('NEAR', '0.07'))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'source.blend'))
src = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']; scene = bpy.context.scene
me = src.data
mi = [i for i, m in enumerate(me.materials) if 'Mallet' in m.name][0]
vids = sorted({v for p in me.polygons if p.material_index == mi for v in p.vertices})
P = np.array([(src.matrix_world @ me.vertices[i].co)[:] for i in vids])
c = P.mean(0); ax = np.linalg.svd(P - c, full_matrices=False)[2][0]
names = [b.name for b in rig.pose.bones if any(k in b.name for k in ('Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky')) and ' L ' in b.name or ' R ' in b.name and any(k in b.name for k in ('Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky'))]
rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
bpy.context.view_layer.update()
H = rig.pose.bones['Xhammer']; Mrest = rig.matrix_world @ H.matrix
out = {}
for act in bpy.data.actions:
    rig.animation_data.action = act; f0, f1 = (int(x) for x in act.frame_range)
    for f in range(f0, f1 + 1):
        scene.frame_set(f)
        Mpose = rig.matrix_world @ H.matrix; back = Mrest @ Mpose.inverted()
        for n in names:
            pb = rig.pose.bones[n]
            for q in (pb.head, pb.tail):
                p = np.array((back @ (rig.matrix_world @ q))[:]); t = float((p - c) @ ax); r = float(np.linalg.norm((p - c) - t * ax))
                if r < NEAR:
                    side = 'L' if ' L ' in n else 'R'
                    out.setdefault(side, {}).setdefault(act.name, []).append(t)
cl = np.array((src.matrix_world.inverted() @ __import__('mathutils').Vector(c))[:])  # mesh-local (dump_mesh.py space); the Body sits 1.28 m up
res = {'axis': ax.tolist(), 'centre': cl.tolist(), 'centre_world': c.tolist(), 'near': NEAR, 'bands': {}}
for side, d in out.items():
    allt = np.concatenate([np.array(v) for v in d.values()])
    res['bands'][side] = {'min': float(allt.min()), 'max': float(allt.max()), 'p01': float(np.percentile(allt, 1)), 'p99': float(np.percentile(allt, 99)),
                          'clips': {k: [round(min(v), 3), round(max(v), 3), len(v)] for k, v in d.items()}}
    print('BAND', side, round(allt.min(), 3), round(allt.max(), 3), {k: [round(min(v), 3), round(max(v), 3)] for k, v in d.items()})
json.dump(res, open(os.path.join(HERE, 'work', 'grip_band.json'), 'w'), indent=1)
