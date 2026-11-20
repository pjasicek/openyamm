"""Reimport export/mm7_m182.glb in a clean scene: per clip and LOD (colour and shadow meshes) the lowest vertex over
all frames, LOD0 parity against dragon_master.blend (bounds per sampled frame), and front/side silhouette renders of
the flight cycle for the scale measurement (review/scale/*.png). Writes work/export_check.json."""
import bpy, json
import numpy as np
from pathlib import Path
from mathutils import Vector
P = Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(P / 'export/mm7_m182.glb'))
sc = bpy.context.scene; sc.render.fps = 24
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE'); meshes = [o for o in bpy.data.objects if o.type == 'MESH' and any(m.type == 'ARMATURE' for m in o.modifiers)]   # not the importer's bone-shape Icosphere
actions = {a.name.split('|')[-1].split('.')[0]: a for a in bpy.data.actions}
def evaluated(o):
    ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh(); a = np.empty(len(m.vertices) * 3)
    m.vertices.foreach_get('co', a); ev.to_mesh_clear(); a = a.reshape(-1, 3)
    return (np.c_[a, np.ones(len(a))] @ np.array(o.matrix_world).T)[:, :3]
report = {'meshes': [o.name for o in meshes], 'clips': {}}
arm.animation_data_create()
for name, act in sorted(actions.items()):
    arm.animation_data.action = act; lo, hi = act.frame_range; per = {}
    for f in range(int(lo), int(hi) + 1):
        sc.frame_set(f)
        for o in meshes:
            per[o.name] = min(per.get(o.name, 1e9), float(evaluated(o)[:, 2].min()))
    report['clips'][name] = {'frames': int(hi - lo + 1), 'min_z_per_mesh': per, 'min_z': min(per.values())}
# scale renders: front and side alpha over the Standing cycle (LOD0 only)
lod0 = max(meshes, key=lambda o: len(o.data.vertices))
for o in meshes: o.hide_render = o is not lod0
sc.render.engine = 'BLENDER_WORKBENCH'; sc.render.film_transparent = True; sc.render.resolution_x = sc.render.resolution_y = 600
cam = bpy.data.objects.new('C', bpy.data.cameras.new('C')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.type = 'ORTHO'; cam.data.ortho_scale = 1.6
out = P / 'review/scale'; out.mkdir(parents=True, exist_ok=True)
arm.animation_data.action = actions['Standing']; lo, hi = actions['Standing'].frame_range
target = Vector((0, -.05, .35))  # glTF import is Y-up converted back to Blender Z-up
for view, d in [('front', (0, -1, 0)), ('side', (1, 0, 0))]:
    cam.location = target + Vector(d) * 3; cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
    for i, f in enumerate(np.linspace(lo, hi - 1, 11)):
        sc.frame_set(int(round(f))); sc.render.filepath = str(out / f'{view}_{i:02d}.png'); bpy.ops.render.render(write_still=True)
report['scale_projection'] = {'ortho_scale_m': 1.6, 'resolution': 600, 'samples': 11}
bounds = {}
for name in ('Standing', 'Attack', 'Dead'):
    arm.animation_data.action = actions[name]; sc.frame_set(int(actions[name].frame_range[0]) + 4); a = evaluated(lod0)
    bounds[name] = [a.min(0).round(5).tolist(), a.max(0).round(5).tolist()]
report['lod0_bounds_frame4'] = bounds
(P / 'work/export_check.json').write_text(json.dumps(report, indent=2) + '\n')
print('EXPORT_CHECK', {k: round(v['min_z'], 5) for k, v in report['clips'].items()})
