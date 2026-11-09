import bpy
import hashlib
import json
from pathlib import Path

stage = Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_demon_meshy_reference_20261004/meshy_cleanup')
bpy.context.window.scene = bpy.data.scenes['MM6_Demon_Cleanup']
# Remove only this task's disposable reimport scene and its own datablocks.
for scene in list(bpy.data.scenes):
    if scene.name.startswith('MM6_Demon_Export_Verification'):
        for obj in list(scene.objects):
            data, kind = obj.data, obj.type
            bpy.data.objects.remove(obj, do_unlink=True)
            if data and data.users == 0:
                if kind == 'MESH':
                    bpy.data.meshes.remove(data)
                elif kind == 'CAMERA':
                    bpy.data.cameras.remove(data)
        bpy.data.scenes.remove(scene)
bpy.ops.wm.save_as_mainfile(filepath=str(stage / 'mm6_demon_cleaned.blend'), copy=True)
acceptance = {
    'status': 'geometry_cleanup_complete',
    'date': '2026-10-04',
    'reviewed_full_views': ['front', 'front_three_quarter', 'right', 'back_three_quarter', 'back', 'left'],
    'reviewed_details': ['head_chest_detail', 'harness_back_detail', 'feet_front_detail',
                        'repaired_foot_detail', 'repaired_foot_back_detail', 'hands_detail', 'knees_detail'],
    'marked_foot_spike_removed': True,
    'smaller_toe_base_and_inner_shin_pinches_faired': True,
    'original_shape_retained': 'Existing A pose, body, claws, spikes, harness, teeth, eyes and tail',
    'source_unchanged': True,
    'glb_reimport_passed': True,
    'uvs_authored': False, 'textures_authored': False, 'rig_authored': False,
    'animation_deformation_tested': False,
    'deliverables': {},
}
for name in ('mm6_demon_cleaned.glb', 'mm6_demon_cleaned.blend', 'preview.png'):
    path = stage / name
    acceptance['deliverables'][name] = {'bytes': path.stat().st_size,
                                       'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
(stage / 'acceptance.json').write_text(json.dumps(acceptance, indent=2) + '\n')
print('Saved reviewed cleanup; original review and unrelated scenes preserved')
