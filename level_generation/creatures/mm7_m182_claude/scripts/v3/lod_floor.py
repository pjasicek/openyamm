"""Export check (Blender, isolated import of export/mm7_m182.glb): every clip present with its duration, and the
lowest posed vertex of every colour and shadow LOD mesh through every clip (half-frame steps at 24 fps).
Writes review/lod_motion_checks.json (v2: review/lod_motion_checks_v2.json)."""
import bpy, json
import numpy as np
from pathlib import Path
P = Path(__file__).resolve().parents[2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(P / 'export/mm7_m182.glb'))
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE'); sc = bpy.context.scene
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
for o in meshes: o.hide_viewport = False
res = {'meshes': {o.name: sum(len(p.vertices) - 2 for p in o.data.polygons) for o in meshes}, 'clips': {}}
for act in bpy.data.actions:
    rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    f0, f1 = act.frame_range; low = {}
    for k in range(int((f1 - f0) * 2) + 1):
        fr = f0 + k * .5; sc.frame_set(int(fr), subframe=fr % 1); dg = bpy.context.evaluated_depsgraph_get()
        for o in meshes:
            ev = o.evaluated_get(dg); m = ev.to_mesh(); c = np.empty(len(m.vertices) * 3); m.vertices.foreach_get('co', c)
            z = (np.array(o.matrix_world) @ np.c_[c.reshape(-1, 3), np.ones(len(m.vertices))].T)[2].min(); ev.to_mesh_clear()
            if o.name not in low or z < low[o.name]: low[o.name] = float(z)
    res['clips'][act.name] = {'duration_s': round((f1 - f0) / sc.render.fps, 4), 'lowest_m': {k: round(v, 4) for k, v in low.items()}, 'lowest_overall_m': round(min(low.values()), 4)}
(P / 'review/lod_motion_checks.json').write_text(json.dumps(res, indent=1) + '\n')
print('LOD_FLOOR', {k: v['lowest_overall_m'] for k, v in res['clips'].items()}, res['meshes'])
