"""Check evaluated joint and wing deformation before animation; retain reproducible probe renders."""
import bpy,sys,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path('level_generation/creatures/mm6_bar1_claude/scripts').resolve()))
import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v1.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene
co=np.array([v.co[:] for v in body.data.vertices]);ed=np.array([e.vertices[:] for e in body.data.edges]);length=np.linalg.norm(co[ed[:,1]]-co[ed[:,0]],axis=1)
hand=(np.linalg.norm(co-np.array(rig.data.bones['B_L_Hand'].head_local),axis=1)<.29)
probes={'neutral':[], 'shoulders':[('B_L_UpperArm',(1,0,0),-75),('B_R_UpperArm',(0,1,0),65)],
'elbows':[('B_L_Forearm',(1,0,0),-95),('B_R_Forearm',(1,0,0),-95)],
'wrists':[('B_L_Hand',(0,1,0),60),('B_R_Hand',(0,1,0),-60)],
'legs':[('B_L_Thigh',(1,0,0),-45),('B_L_Calf',(1,0,0),60),('B_R_Calf',(1,0,0),35)],
'wings_down':[('W_L_Root',(0,1,0),70),('W_R_Root',(0,1,0),-70)],
'wings_back':[('W_L_Root',(0,0,1),35),('W_R_Root',(0,0,1),-35)],
'head_turn':[('B_Head',(0,0,1),40)],'fingers':[]}
for sd in ['L','R']:
 axis=(rig.data.bones[f'B_{sd}_Finger1'].head_local-rig.data.bones[f'B_{sd}_Finger4'].head_local).normalized()
 for n in rig.data.bones.keys():
    if f'B_{sd}_Finger' in n:probes['fingers'].append((n,axis,-35 if sd=='L' else 35))
report={}
for title,moves in probes.items():
 for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
 for n,axis,angle in moves:
    pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';local=rig.data.bones[n].matrix_local.to_3x3().inverted()@Vector(axis)
    pb.rotation_quaternion=Quaternion(local,math.radians(angle))
 bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();ev=body.evaluated_get(deps);mesh=ev.to_mesh()
 posed=np.array([v.co[:] for v in mesh.vertices]);ev.to_mesh_clear();assert np.isfinite(posed).all()
 ratio=np.linalg.norm(posed[ed[:,1]]-posed[ed[:,0]],axis=1)/np.maximum(length,1e-6)
 mask=length>.002
 report[title]={'edge_p99':float(np.quantile(ratio[mask],.99)),'edge_max':float(ratio[mask].max()),'edges_above_3x':int((ratio[mask]>3).sum())}
 worst=np.argsort(np.where(mask,ratio,0))[-12:][::-1]
 report[title]['worst']=[{'ratio':float(ratio[k]),'vertices':ed[k].tolist(),'positions':co[ed[k]].tolist(),
    'weights':[{body.vertex_groups[g.group].name:round(g.weight,4) for g in body.data.vertices[int(v)].groups} for v in ed[k]]} for k in worst]
 common.render_views(str(P/f'review/probe_{title}'),1.5,3.6,views=('front','left'),resolution=(800,1000))
 if title in ['fingers','wrists']:
    c=rig.pose.bones['B_L_Hand'].head;common.render_views(str(P/f'review/probe_{title}_hand'),c.z-.1,.44,views=('front','three_quarter'),resolution=(800,800),target=(c.x,c.y))
for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
(P/'work/rig_probes.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
