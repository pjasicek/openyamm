import bpy,json,runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for file in ['animated_master','production_body','runtime_master']:
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/{file}.blend'));rig=bpy.data.objects['Rig'];scene=bpy.context.scene
 for clip in ['Standing','Fidget','Death']:
  act=bpy.data.actions[clip];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
  for f in [0,int(act.frame_range[1])]:
   scene.frame_set(f);print('ROOT',file,clip,f,list(rig.pose.bones['B_Pelvis'].head),flush=True)
   print('UNKEYED',[(b.name,list(b.location),list(b.scale)) for b in rig.pose.bones if b.name!='B_Pelvis' and (b.location.length>.001 or max(abs(v-1) for v in b.scale)>.001)],flush=True)
runpy.run_path(str(P/'scripts/round2_deform_probe.py'),run_name='__main__')
