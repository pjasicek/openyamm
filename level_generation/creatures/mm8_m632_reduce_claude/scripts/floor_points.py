"""Floor-contact points for the LOD build (playbook MM8 batch lesson): LOD0 vertices within REA_FLOOR_MM (default
10 mm) of the lowest point in the last frame of Dead and in Death, reduced to at most REA_FLOOR_N (default 24) by
farthest-point sampling, as rest-pose positions -> work/floor_points.json. Reduced LOD3 otherwise lay 2 cm above the
floor in Dead. Usage: blender -b -P floor_points.py -- <lod0 glb>"""
import json, os, sys, bpy, bmesh
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
glb = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
bpy.ops.import_scene.gltf(filepath=glb)
o = bpy.data.objects[os.environ.get('REA_NODE', 'DarkDwarf')]
rig = next(m.object for m in o.modifiers if m.type == 'ARMATURE')
rest = np.array([(o.matrix_world @ v.co)[:] for v in o.data.vertices])
TOL = float(os.environ.get('REA_FLOOR_MM', '10')) / 1000; pick = set()
for name in ('Dead', 'Death'):
    act = bpy.data.actions[name]; rig.animation_data.action = act
    f0, f1 = (int(x) for x in act.frame_range)
    for f in ([f1] if name == 'Dead' else range(f0, f1 + 1)):
        sc.frame_set(f); b = bmesh.new(); b.from_object(o, bpy.context.evaluated_depsgraph_get()); b.transform(o.matrix_world)
        z = np.array([v.co.z for v in b.verts]); b.free()
        if name == 'Dead' or z.min() < 0.002:
            pick |= set(np.where(z < max(z.min(), 0) + TOL)[0].tolist())
idx = np.array(sorted(pick)); pts = rest[idx]
# one point per position (glTF splits vertices at seams; coincident copies are the same contact)
_, uniq = np.unique(np.round(pts, 6), axis=0, return_index=True); pts = pts[np.sort(uniq)]
N = int(os.environ.get('REA_FLOOR_N', '24')); chosen = [0]
dist = np.linalg.norm(pts - pts[0], axis=1)
while len(chosen) < min(N, len(pts)):
    k = int(np.argmax(dist)); chosen.append(k); dist = np.minimum(dist, np.linalg.norm(pts - pts[k], axis=1))
json.dump(pts[chosen].tolist(), open(os.path.join(HERE, 'work', 'floor_points.json'), 'w'), indent=1)
print('FLOOR POINTS', len(chosen), 'of', len(pts))
