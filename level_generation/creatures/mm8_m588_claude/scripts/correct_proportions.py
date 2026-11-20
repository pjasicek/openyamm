"""Native standing is 210x163 px: widen the inferred body, preserving its frozen UVs."""
import bpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];factor=1.125
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig.blend'))
assert 'native_width_correction' not in json.loads((P/'work/rig_spec.json').read_text()), 'Correction already applied'
body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig']
for v in body.data.vertices:v.co.x*=factor
for o in bpy.data.objects:o.select_set(o==rig)
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for bone in rig.data.edit_bones:bone.head.x*=factor;bone.tail.x*=factor
bpy.ops.object.mode_set(mode='OBJECT')
spec=json.loads((P/'work/rig_spec.json').read_text())
for g in spec['groups'].values():g['center'][0]*=factor
spec['native_standing_bbox']=[210,163];spec['native_width_correction']=factor
(P/'work/rig_spec.json').write_text(json.dumps(spec,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig.blend'))
