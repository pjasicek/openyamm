import bpy,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/round2/body_l3_factor0.blend'));ob=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0);ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();v=[list(x.co)for x in m.vertices];ev.to_mesh_clear();names={g.index:g.name for g in ob.vertex_groups};trans=[]
for vert in ob.data.vertices:
 mat=sum((np.array(rig.pose.bones[names[g.group]].matrix@rig.data.bones[names[g.group]].matrix_local.inverted())*g.weight for g in vert.groups),np.zeros((4,4)));trans.append(mat[:3,:3].tolist())
ob.data.calc_loop_triangles();data={'world':v,'rest':[list(v.co)for v in ob.data.vertices],'transforms':trans,'triangles':[list(t.vertices)for t in ob.data.loop_triangles]};(P/'work/round2/fit_input.json').write_text(json.dumps(data));print('FIT INPUT',len(v),len(data['triangles']))
