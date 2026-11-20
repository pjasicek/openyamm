from pathlib import Path
import bpy, json
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/imported.blend'))
for role,source in {'Standing':'Carbine_Standing','Walking':'Demon_Walking','Hit':'Carbine_Hit','Death':'Carbine_Death','Dead':'Carbine_Dead','Fidget':'Carbine_Fidget'}.items():
 a=bpy.data.actions[source].copy();a.name=role;a.use_fake_user=True
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body']
r={'bones':{b.name:{'head':list(b.head_local),'tail':list(b.tail_local),'matrix':[list(r) for r in b.matrix_local]} for b in rig.data.bones},'bounds':[[min(v.co[i] for v in body.data.vertices),max(v.co[i] for v in body.data.vertices)] for i in range(3)]}
(P/'review/rest.json').write_text(json.dumps(r,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/motion_start.blend'))
