"""Lower colour and shadow LODs through every clip at 24 fps (from mm8_m492_claude check_motion_lods_v3.py): each LOD is
swapped into the Body node of a review copy, reimported and sampled. Writes review/lod_motion_checks.json."""
import bpy, json, sys, copy
import numpy as np
from pathlib import Path
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import read_glb, write_glb
D, B = read_glb(P / 'export/mm7_m182.glb'); node = next(n for n in D['nodes'] if n.get('name') == 'Body'); extras = D['meshes'][node['mesh']]['extras']
levels = [('lod%d' % k, i) for k, i in enumerate(extras['openyamm_lods'], 1)] + [('shadow%d' % k, i) for k, i in enumerate(extras['openyamm_shadow_lods'])]
report = {}
for label, index in levels:
    d = copy.deepcopy(D); next(n for n in d['nodes'] if n.get('name') == 'Body')['mesh'] = index
    path = P / 'work' / f'{label}_review.glb'; write_glb(path, d, B)
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene; sc.render.fps = 24; bpy.ops.import_scene.gltf(filepath=str(path))
    o = bpy.data.objects['Body']; rig = next(m.object for m in o.modifiers if m.type == 'ARMATURE'); item = {}
    for act in bpy.data.actions:
        rig.animation_data.action = act
        if act.slots: rig.animation_data.action_slot = act.slots[0]
        start, end = act.frame_range; minimum = 10
        for f in range(int(start), int(end) + 1):
            sc.frame_set(f); ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh()
            co = np.array([tuple(ev.matrix_world @ v.co) for v in me.vertices]); ev.to_mesh_clear(); minimum = min(minimum, float(co[:, 2].min()))
        item[act.name.rsplit('|', 1)[-1]] = round(minimum, 5)
    report[label] = item; print('LOD_FLOORS', label, item, flush=True)
    path.unlink()
(P / 'review/lod_motion_checks.json').write_text(json.dumps(report, indent=2) + '\n')
print('LOD_MIN', min(v for r in report.values() for v in r.values()))
