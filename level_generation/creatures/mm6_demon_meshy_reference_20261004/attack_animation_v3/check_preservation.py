"""Verify the final editable file preserves geometry, weights and other curves."""
import bpy
import json
import numpy as np
from pathlib import Path

stage = Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(stage / 'mm6_demon_attack.blend'))
scene = bpy.context.scene
rig = scene.objects['Demon_Attack_Rig']
mesh = scene.objects['Demon_Attack_Mesh']
with bpy.data.libraries.load(str(stage.parent / 'attack_animation_v2/mm6_demon_attack.blend'), link=False) as (available, loaded):
    loaded.scenes = ['MM6_Demon_Attack']
old_scene = loaded.scenes[0]
old_rig = next(o for o in old_scene.objects if o.type == 'ARMATURE')
old_mesh = next(o for o in old_scene.objects if o.type == 'MESH')
assert np.array_equal(np.array([tuple(v.co) for v in mesh.data.vertices]),
                      np.array([tuple(v.co) for v in old_mesh.data.vertices]))
assert [list(f.vertices) for f in mesh.data.polygons] == [list(f.vertices) for f in old_mesh.data.polygons]
assert [g.name for g in mesh.vertex_groups] == [g.name for g in old_mesh.vertex_groups]
assert [[(g.group, g.weight) for g in v.groups] for v in mesh.data.vertices] == [[(g.group, g.weight) for g in v.groups] for v in old_mesh.data.vertices]
assert len(rig.data.bones) == len(old_rig.data.bones) == 85
for bone in rig.data.bones:
    old = old_rig.data.bones[bone.name]
    assert np.array_equal(np.array(bone.matrix_local), np.array(old.matrix_local)), bone.name


def curves(action):
    return {(c.data_path, c.array_index): [(tuple(k.co), k.interpolation) for k in c.keyframe_points]
            for c in action.layers[0].strips[0].channelbag(action.slots[0]).fcurves}


changed = set(json.loads((stage / 'foot_controls.json').read_text())['changed_bones'])
results = {}
for clip in ['Attack', 'Walking', 'Running']:
    new = next(t.strips[0].action for t in rig.animation_data.nla_tracks if t.name == clip)
    old = next(t.strips[0].action for t in old_rig.animation_data.nla_tracks if t.name == clip)
    new_curves, old_curves = curves(new), curves(old)
    assert set(new_curves) == set(old_curves)
    differences = [key for key in new_curves if new_curves[key] != old_curves[key]]
    if clip == 'Attack':
        assert differences and all(any('"' + name + '"' in key[0] for name in changed) for key in differences)
    else:
        assert not differences, clip
    results[clip] = {'curves': len(new_curves), 'changed_curves': len(differences),
                     'changed_data_paths': sorted(set(path for path, _ in differences))}
report = {'final_blend_checked': True, 'rest_mesh_coordinates_identical': True,
          'triangle_connectivity_identical': True, 'vertex_groups_and_weights_identical': True,
          'all_85_bind_matrices_identical': True, 'source_and_final_uv_layers': [len(old_mesh.data.uv_layers), len(mesh.data.uv_layers)],
          'clips': results}
(stage / 'preservation_review.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
