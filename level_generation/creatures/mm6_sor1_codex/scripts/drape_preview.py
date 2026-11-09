import bpy,sys,numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_arm_clear.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];a=bpy.data.actions['Death'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];scene=bpy.context.scene;common.workbench_clay(scene)
for f in [15,56.5,100,156]:
 scene.frame_set(int(f),subframe=f-int(f));common.render_views(str(p/'review'/('drape_'+str(f))),.7,2.5,views=('front','left','three_quarter'),resolution=(600,600))
 ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();low=min(me.vertices,key=lambda v:v.co.z);print('FLOOR',f,low.index,list(low.co),'piece',body.data.attributes['piece'].data[low.index].value);ev.to_mesh_clear()
