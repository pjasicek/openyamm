from pathlib import Path
import sys,bpy
from mathutils import Vector
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
import common
from g6_head_clearance import Clearance
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v7.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene
print('HEAD REST',[(i,list(body.data.vertices[i].co)) for i in (128,134,153)])
C=Clearance(body);common.workbench_clay(scene)
for name,f in [('Running',15),('Hit',3),('Attack',32),('Walking',16),('Standing',0)]:
 act=bpy.data.actions[name];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];scene.frame_set(f)
 if name in ('Walking','Standing'):
  target=rig.pose.bones['B_Pelvis'].head;scale=.70
 else:
  target=rig.pose.bones['B_Head'].head;scale=.55
 print('CONTACTCASE',name,f,C.measure(),C.last_hit)
 common.render_views(str(p/f'review/contact_{name}'),target.z,scale,views=('front','left','three_quarter'),target=(target.x,target.y),resolution=(650,650))
