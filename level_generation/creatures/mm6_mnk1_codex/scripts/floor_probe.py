import bpy,numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/anim_reduced.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];a=bpy.data.actions['Death'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];low=(1,None)
for f in np.arange(0,60.01,.5):
 bpy.context.scene.frame_set(int(f),subframe=float(f%1));ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();v=min(me.vertices,key=lambda v:v.co.z)
 if v.co.z<low[0]:low=(float(v.co.z),(float(f),v.index,b.data.attributes['piece'].data[v.index].value,list(v.co),list(b.data.vertices[v.index].co)))
 ev.to_mesh_clear()
print('FLOOR_WORST',low)
