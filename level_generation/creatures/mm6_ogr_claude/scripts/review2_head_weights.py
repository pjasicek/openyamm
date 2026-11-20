from pathlib import Path
import bpy,sys,json
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
from g6_head_clearance import Clearance
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v9.blend'));b=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];c=Clearance(b)
for i in [5308,5848]:print('HEADWEIGHT_OLD',i,[(b.vertex_groups[e.group].name,round(e.weight,3)) for e in b.data.vertices[i].groups if e.weight>.005])
headverts={i for f in b.data.polygons if b.data.attributes['head'].data[f.index].value for i in f.vertices}
for i in headverts:
 v=b.data.vertices[i];q=v.co.z-.4*v.co.y;w=min(max((q-1.49)/.04,0),1)
 if w<=0:continue
 old={e.group:e.weight for e in v.groups};gi=b.vertex_groups['B_Head'].index
 for g in b.vertex_groups:g.remove([i])
 for index,value in old.items():b.vertex_groups[index].add([i],value*(1-w),'REPLACE')
 b.vertex_groups['B_Head'].add([i],old.get(gi,0)*(1-w)+w,'REPLACE')
for i in headverts:
 v=b.data.vertices[i];q=v.co.z-.4*v.co.y;w=min(max((q-1.48)/.055,0),1);w=w*w*(3-2*w);v.co.y-=.035*w
b.data.update();c=Clearance(b)
for name in ['Standing','Running','Fidget','Death','Hit']:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];worst=(0,None,None)
 for f in range(int(a.frame_range[1])+1):
  bpy.context.scene.frame_set(f);d=c.measure()[0]
  if d>worst[0]:worst=(d,f,c.last_hit)
 print('HEAD_RIGID_GATE',name,worst)
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_v9h.blend'))
