import bpy
import json
from pathlib import Path

stage = Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_demon_meshy_reference_20261004/attack_animation_v3')
scene = bpy.context.scene
record = {
    'blender': bpy.app.version_string,
    'gui': not bpy.app.background,
    'filepath': bpy.data.filepath,
    'active_scene': scene.name,
    'scenes': [s.name for s in bpy.data.scenes],
    'objects': [{'name': o.name, 'type': o.type} for o in scene.objects],
}
for obj in scene.objects:
    if obj.type != 'ARMATURE':
        continue
    record[obj.name] = {
        'action': obj.animation_data.action.name if obj.animation_data and obj.animation_data.action else None,
        'feet': [{'name': b.name, 'parent': b.parent.name if b.parent else None,
                  'rest_head': list(b.head_local), 'rest_tail': list(b.tail_local),
                  'use_connect': b.use_connect, 'pose_head': list(obj.pose.bones[b.name].head)}
                 for b in obj.data.bones if any(p in b.name for p in ['UpLeg', 'Leg', 'Foot', 'Toe'])],
    }
(stage / 'live_scene_audit.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record, indent=2))
