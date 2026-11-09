import bpy,json
import numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_v1.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene;src=np.load(P/'work/weights.npz');co=src['co'];edges=src['edges'];weights=src['weights'];names=src['names'];length=np.linalg.norm(co[edges[:,0]]-co[edges[:,1]],axis=1);report={}
for role,t in [('Walk',.56),('Attack',.50),('Cast',.50)]:
 a=bpy.data.actions[role];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];f=t*24+1;sc.frame_set(int(f),subframe=f-int(f));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();c=np.array([v.co[:] for v in me.vertices]);ev.to_mesh_clear();ratio=np.linalg.norm(c[edges[:,0]]-c[edges[:,1]],axis=1)/length
 ids=np.argsort(ratio)[-10:][::-1];report[role]=[{'edge':edges[i].tolist(),'ratio':float(ratio[i]),'rest':co[edges[i]].tolist(),'weights':[{str(names[j]):float(weights[v,j]) for j in np.where(weights[v]>.001)[0]} for v in edges[i]]} for i in ids]
(P/'work/pilot_edge_diagnostic.json').write_text(json.dumps(report,indent=2))
sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.color_type='MATERIAL';sc.display.shading.show_cavity=True;sc.display.shading.show_shadows=False;sc.render.resolution_x=sc.render.resolution_y=900
cam=bpy.data.objects.new('DetailCamera',bpy.data.cameras.new('DetailCamera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=1.5
for role,t in [('Attack',.5),('Cast',.5)]:
 a=bpy.data.actions[role];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];sc.frame_set(int(t*24+1));cam.location=(0,-6,1.35);cam.rotation_euler=(Vector((0,-.2,1.35))-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(P/'review'/f'{role}_hands_close.png');bpy.ops.render.render(write_still=True)
