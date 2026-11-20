"""Choose symmetric skin-ring elbows and exact hand-boundary wrists; boots keep the anatomical ankle estimate."""
import bpy,bmesh,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/step1.blend'));me=bpy.data.objects['Body'].data
M=json.loads((P/'work/meshy_joints.json').read_text())['joints'];R=json.loads((P/'work/joints_final.json').read_text());J=R['joints'];pv=np.array([a.value for a in me.attributes['piece'].data]);co=np.array([tuple(v.co)for v in me.vertices]);bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table()
x0=(M['L_UpperArm'][0]+M['R_UpperArm'][0])/2
# The two independent line fits bracket the elbow; average mirrored measurements for the symmetric limb geometry.
elbows=np.array([J['L_Forearm'],J['R_Forearm']]);ez=elbows[:,2].mean();ey=elbows[:,1].mean();ex=np.abs(elbows[:,0]-x0).mean()
for sd,part,sign in [('L',2,1),('R',3,-1)]:
 ids={v.index for e in bm.edges if e.is_boundary for v in e.verts if pv[v.index]==part};assert len(ids)==12
 wr=co[list(ids)].mean(0);J[sd+'_Hand']=wr.tolist();J[sd+'_Forearm']=[float(x0+sign*ex),float(ey),float(ez)];J[sd+'_Foot']=M[sd+'_Foot']
 print('SELECTED JOINT',sd,'wrist',wr,'elbow',J[sd+'_Forearm'],'ankle',J[sd+'_Foot'])
R['joints']=J;R['selection']='Exact 12-vertex hand boundary wrists; mirrored ring-line elbow average; Meshy ankles retained because global narrowest boot ring is 5cm too high.'
(P/'work/joints_final.json').write_text(json.dumps(R,indent=2))
