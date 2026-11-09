"""Orient the double blade's cutting plane using its measured target-directed release."""
import bpy,json,math,sys
import numpy as np
from pathlib import Path
from mathutils import Matrix
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round1_clothed.blend'));r=bpy.data.objects['Rig'];a=bpy.data.objects['AxeMesh'];sc=bpy.context.scene;fps=sc.render.fps/sc.render.fps_base
vs=np.array([v.co[:] for v in a.data.vertices]);ids=np.where((abs(vs[:,0])>.21)&(vs[:,2]>.8))[0];points=vs[ids]
def matrices(role):
 act=bpy.data.actions[role];r.animation_data.action=act;r.animation_data.action_slot=act.slots[0];dur=act.frame_range[1]/fps;ts=np.arange(0,dur+1e-5,1/120);ms=[]
 for t in ts:
  f=t*fps;sc.frame_set(int(f),subframe=f%1);ms.append(np.array(r.pose.bones['Axe'].matrix@r.data.bones['Axe'].matrix_local.inverted()))
 return ts,np.array(ms),dur
poses={role:matrices(role) for role in ['Attack','Cast']}
def check(deg,role):
 ts,m,dur=poses[role];rot=np.array(Matrix.Rotation(math.radians(deg),3,'Z'));p=points@rot.T;pts=np.einsum('tij,vj->tvi',m[:,:3,:3],p)+m[:,:3,3,None].transpose(0,2,1);vel=np.gradient(pts,1/120,axis=0);speed=np.linalg.norm(vel,axis=2);face=-m[:,1,2];speed[(face<.5)|(ts<.08)|(ts>dur-.08)]=0;i,j=np.unravel_index(speed.argmax(),speed.shape);v=vel[i,j];edge=m[i,:3,:3]@rot[:,0]*np.sign(points[j,0]);flat=m[i,:3,:3]@rot[:,1];lead=float(v@edge/np.linalg.norm(v));flatshare=float(abs(v@flat)/np.linalg.norm(v))
 return {'impact_seconds':float(ts[i]),'speed_m_s':float(speed[i,j]),'edge_leading_share':lead,'flat_normal_share':flatshare,'target_alignment':float(face[i]),'actual_edge_vertex':int(ids[j]),'pass':lead>.65 and flatshare<.4}
curve=[{'roll_deg':float(d),'Attack':check(d,'Attack'),'Cast':check(d,'Cast')} for d in range(-180,181,5)]
valid=[x for x in curve if x['Attack']['pass'] and x['Cast']['pass']];assert valid,'No blade orientation passes the actual fastest target-directed motion'
chosen=min(valid,key=lambda x:abs(x['roll_deg']))
rot=Matrix.Rotation(math.radians(chosen['roll_deg']),3,'Z')
for v in a.data.vertices:v.co=rot@v.co
sc['round1_blade_roll_deg']=chosen['roll_deg'];(P/'review/round1/blade_roll_curve.json').write_text(json.dumps(curve,indent=2))
(P/'review/final_blade_gate.json').write_text(json.dumps({k:chosen[k] for k in ['Attack','Cast']},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round1_high.blend'));print('BLADE',chosen,flush=True)
