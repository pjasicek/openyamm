"""Level the retargeted feet and establish skin contact before the robe simulation."""
from pathlib import Path
import bpy,sys,runpy,numpy as np
from mathutils import Vector
p=Path(__file__).resolve().parents[1]
s=p/'scripts/foot_level.py';sys.argv=[str(s),'--',str(p/'work/motion_authored.blend'),str(p/'work/motion_feet.blend'),'Standing','Walking:const','Attack','Cast','Hit','Fidget','Death:until=12'];runpy.run_path(str(s),run_name='__main__')
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene;pv=np.array([v.value for v in body.data.attributes['piece'].data]);rest=np.array([v.co[:] for v in body.data.vertices]);feet=(pv==0)&(rest[:,2]<.18)
for role in ['Standing','Walking','Attack','Cast','Hit','Death','Fidget']:
    a=bpy.data.actions[role];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];changes=[]
    for f in range(int(a.frame_range[1])+1):
        scene.frame_set(f);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();co=np.array([v.co[:] for v in me.vertices]);ev.to_mesh_clear()
        mask=(pv==0)|np.isin(pv,[3,4,7,8,11]) if role=='Death' and f>10 else feet
        dz=.003-float(co[mask,2].min());pb=rig.pose.bones['B_Pelvis'];m=pb.matrix.copy();m.translation.z+=dz;pb.matrix=m;bpy.context.view_layer.update();pb.keyframe_insert('location',frame=f);changes.append(dz)
    print('FLOOR',role,min(changes),max(changes),flush=True)
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/motion_grounded.blend'))
