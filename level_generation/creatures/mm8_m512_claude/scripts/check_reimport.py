"""Reimport the delivered portable GLB in an empty Blender scene and inspect its actual actions."""
import bpy,json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parents[1];source=P/'export/mm8_wolf.glb'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(source))
rigs=[o for o in bpy.data.objects if o.type=='ARMATURE'];assert len(rigs)==1
rig=rigs[0];assert len(rig.data.bones)==24
expected=['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']
report={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'bones':len(rig.data.bones),'actions':[]}
for name in expected:
 matches=[a for a in bpy.data.actions if a.name==name or a.name.startswith(name+'_')]
 assert len(matches)==1,(name,[a.name for a in bpy.data.actions])
 rig.animation_data.action=matches[0];bpy.context.scene.frame_set(1)
 report['actions'].append(matches[0].name)
assert bpy.data.objects.get('Wolf') is not None
(P/'work/reimport.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report),flush=True)
