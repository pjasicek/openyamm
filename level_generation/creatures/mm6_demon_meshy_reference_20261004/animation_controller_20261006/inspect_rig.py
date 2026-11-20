"""Read the selected master without changing it; report casting controls and socket anchors."""
import json
from pathlib import Path
import bpy

stage = Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(stage.parent / 'texturing_fixed_20261005/mm6_demon_textured.blend'))
scene = bpy.data.scenes['MM6_Demon_Textured_Animations']
bpy.context.window.scene = scene
rig = next(o for o in scene.objects if o.get('material_role') == 'rig')
mesh = next(o for o in scene.objects if o.get('material_role') == 'body')
tracks = rig.animation_data.nla_tracks
for track in tracks:
    track.mute = track.name != 'Standing'
scene.frame_set(0)
report = {'scene': scene.name, 'rig': rig.name, 'mesh': mesh.name,
          'rig_matrix': [list(r) for r in rig.matrix_world],
          'clips': {t.name: [t.strips[0].frame_start, t.strips[0].frame_end] for t in tracks},
          'bones': {b.name: {'head': list(b.head), 'tail': list(b.tail),
                           'matrix': [list(r) for r in b.matrix],
                           'rest': [list(r) for r in b.bone.matrix_local],
                           'parent': b.parent.name if b.parent else None} for b in rig.pose.bones},
          'objects': [(o.name, o.type, o.get('material_role')) for o in scene.objects]}
(stage / 'rig.json').write_text(json.dumps(report, indent=2) + '\n')
print('Wrote rig.json; selected master unchanged.', flush=True)
