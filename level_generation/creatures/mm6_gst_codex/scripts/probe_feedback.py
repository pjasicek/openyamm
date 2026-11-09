import bpy,json,numpy as np,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_v1.blend'));r=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];sc=bpy.context.scene
r.animation_data.action=bpy.data.actions['Attack'];sc.frame_set(51)
c=np.array([v.co[:] for v in o.data.vertices]);e=np.array([x.vertices[:] for x in o.data.edges]);part=np.array([x.value for x in o.data.attributes['part'].data]);length=np.linalg.norm(c[e[:,1]]-c[e[:,0]],axis=1)
ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();new=np.array([v.co[:] for v in m.vertices]);ev.to_mesh_clear();ratio=np.linalg.norm(new[e[:,1]]-new[e[:,0]],axis=1)/np.maximum(length,1e-10);ids=np.where((part[e[:,0]]==0)&(length>.002))[0]
for idx in ids[np.argsort(ratio[ids])[-6:]]:
 print('EDGE',int(idx),'ratio',ratio[idx],'rest',c[e[idx]].tolist(),'posed',new[e[idx]].tolist(),'weights',[[(o.vertex_groups[g.group].name,round(g.weight,3)) for g in o.data.vertices[v].groups if g.weight>.03] for v in e[idx]])
d=json.loads((P/'work/rig.json').read_text());out={}
for sd in ['L','R']:
 angles=[];wrists=[]
 for frame in np.arange(1,70,.5):
  sc.frame_set(int(frame),subframe=frame%1);f=r.pose.bones['B_'+sd+'_Forearm'].matrix.translation;h=r.pose.bones['B_'+sd+'_Hand'].matrix.translation;rest=Vector(d['digits'][sd+'2']['pts'][0]);hand=r.pose.bones['B_'+sd+'_Hand'].matrix@r.data.bones['B_'+sd+'_Hand'].matrix_local.inverted()@rest
  angles.append(math.degrees((h-f).angle(hand-h)));wrists.append(list(h))
 out[sd]={'max_bend_deg':max(angles),'worst_frame':int(np.argmax(angles))/2,'positions':wrists}
(P/'review/feedback_v2/wrist_probe.json').write_text(json.dumps(out,indent=2));print('WRIST',[(k,v['max_bend_deg'],v['worst_frame']) for k,v in out.items()])
