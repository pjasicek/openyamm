from pathlib import Path
import bpy,sys,json,numpy as np
from mathutils import Vector
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
from g6_head_clearance import Clearance
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v9.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];c=Clearance(body);common.workbench_clay(bpy.context.scene)
for name,frame in [('Hit',12),('Fidget',21),('Death',7),('Death',32)]:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(frame)
 print('CONTACT',name,frame,c.measure(),c.last_hit,'rest',list(body.data.vertices[c.last_hit[2]].co) if c.last_hit else None)
 head=rig.pose.bones['B_Head'].head
 common.render_views(str(p/'revision_02'/f'contact_{name}{frame}'),head.z+.07,.70,views=('front','left','three_quarter'),resolution=(500,500),target=head[:2])
for name,frames in [('Standing',[0,30,60]),('Running',[0,4,12,20,24]),('Death',[0,7,16,24,32])]:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
 for f in frames:
  bpy.context.scene.frame_set(f);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();co=np.array([tuple(v.co) for v in me.vertices]);ev.to_mesh_clear();print('FLOOR',name,f,co[:,2].min(),co[:,2].max())
