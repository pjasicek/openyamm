import bpy,numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/round3_motion.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];a=bpy.data.actions['Attack'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(102,subframe=.5);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();names=[g.name for g in body.vertex_groups];edges=[]
for e in body.data.edges:
 a,b=e.vertices;wa=sum(g.weight for g in body.data.vertices[a].groups if names[g.group].startswith('B_L_') and any(k in names[g.group] for k in ['UpperArm','Forearm','Hand']));wb=sum(g.weight for g in body.data.vertices[b].groups if names[g.group].startswith('B_L_') and any(k in names[g.group] for k in ['UpperArm','Forearm','Hand']))
 if wa>.3 and wb>.3:edges.append(((me.vertices[a].co-me.vertices[b].co).length/max(1e-6,(body.data.vertices[a].co-body.data.vertices[b].co).length),a,b))
for ratio,a,b in sorted(edges,reverse=True)[:22]:print('STRETCH',round(ratio,3),a,b,[round(x,3) for x in body.data.vertices[a].co],[(names[g.group],round(g.weight,3)) for g in body.data.vertices[a].groups])
ev.to_mesh_clear()
