"""Lowest body point (skinned LOD0 of the body GLB, imported as is) at every key time of a clip in [0, T] ->
work/floor_<label>.json. Usage: blender -b -P floor_measure.py -- <glb> <label> <T> [clip]"""
import json, os, sys, bpy
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]; glb, label, T = a[0], a[1], float(a[2]); clip = a[3] if len(a) > 3 else 'Attack'
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
sc = bpy.context.scene; rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
body = next(o for o in bpy.data.objects if o.type == 'MESH' and o.name == 'EtherKnight')
act = next(x for x in bpy.data.actions if x.name.split('|')[-1] == clip or x.name == clip)
rig.animation_data.action = act
if act.slots:
    rig.animation_data.action_slot = act.slots[0]
rows = []
for k in range(int(round(T * 120)) + 1):
    t = k / 120; fr = act.frame_range[0] + t * 24; sc.frame_set(int(fr), subframe=fr - int(fr))
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    z = min((body.matrix_world @ v.co).z for v in m.vertices); ev.to_mesh_clear(); rows.append((round(t, 5), z))
json.dump(rows, open(os.path.join(HERE, 'work', f'floor_{label}.json'), 'w')); print('FLOOR', label, min(r[1] for r in rows))
