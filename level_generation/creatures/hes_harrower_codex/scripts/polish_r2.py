"""Keep the blade's fist guard as the gauntlet ring; clear the wrist hinge at the distal plate."""
from pathlib import Path
import bpy,sys,runpy,os,json
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/final_r2.blend'));rig=bpy.data.objects['Rig']
for side in 'LR':
 bpy.data.objects.remove(bpy.data.objects['Cuff_'+side],do_unlink=True)
 ob=bpy.data.objects['Arm_forearm_'+side];assert not ob.get('review_r2_wrist_fit');a=rig.data.bones[f'B_{side}_Forearm'].head_local;b=rig.data.bones[f'B_{side}_Hand'].head_local;axis=(b-a).normalized()
 for v in ob.data.vertices:
  if v.index<60:continue
  row=((v.index-60)%15)//5;v.co-=(b-a)*(.06*row/2)
  q=v.co-a;rad=(q-axis*q.dot(axis)).normalized();v.co+=rad*.002
 ob['review_r2_wrist_fit']=True
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/final_r2.blend'))
clips=[a.name for a in bpy.data.actions if a.name.startswith('Harrower_')];os.environ['ONLY']='forearm_L,forearm_R';sys.argv=['armour_gate.py','--',str(P/'work/final_r2.blend'),'wrists_r2',str(P/'scripts/armour_harrower.json'),*clips];runpy.run_path(str(P/'scripts/armour_gate.py'),run_name='__main__')
sys.argv=['shell_leak.py','--',str(P/'work/final_r2.blend'),str(P/'scripts/armour_harrower.json'),'r2',*clips];runpy.run_path(str(P/'scripts/shell_leak.py'),run_name='__main__')
