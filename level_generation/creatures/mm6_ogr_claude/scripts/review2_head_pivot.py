from pathlib import Path
import bpy,sys,math,json
from mathutils import Vector
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));from g6_head_clearance import Clearance
results=[]
for file in ['rig_v9h.blend','rig_v9u.blend']:
 for z,y in [(0,0),(.03,0),(.055,0),(.055,.025),(.03,.025),(.055,-.025)]:
  bpy.ops.wm.open_mainfile(filepath=str(p/'work'/file));rig=bpy.data.objects['Rig'];rig.animation_data.action=None
  for pb in rig.pose.bones:pb.matrix_basis.identity()
  bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT');h=rig.data.edit_bones['B_Head'];h.translate(Vector((0,y,z)));bpy.ops.object.mode_set(mode='OBJECT')
  c=Clearance(bpy.data.objects['Body']);a=bpy.data.actions['Death'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];worst=0;count=0
  for f in range(0,int(a.frame_range[1])+1,2):
   bpy.context.scene.frame_set(f);d=c.measure()[0];worst=max(worst,d);count+=d>.01
  row={'file':file,'offset':[0,y,z],'max_depth':worst,'frames_over_1cm':count};results.append(row);print('PIVOT_PROBE',row,flush=True)
(p/'revision_02/motion/head_pivot_probe.json').write_text(json.dumps(results,indent=2)+'\n')
