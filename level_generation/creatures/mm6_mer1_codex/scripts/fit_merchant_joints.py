import bpy,bmesh,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/step1.blend'));ob=bpy.data.objects['Body'];me=ob.data
M={k:np.array(v)for k,v in json.loads((P/'work/meshy_joints.json').read_text())['joints'].items()};J={k:v.copy()for k,v in M.items()};pv=np.array([a.value for a in me.attributes['piece'].data]);co=np.array([tuple(v.co)for v in me.vertices])
def rings(p,n,pieces):
 bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[v for v in bm.verts if pv[v.index] not in pieces],context='VERTS')
 r=bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=Vector(p),plane_no=Vector(n));edges=[e for e in r['geom_cut']if isinstance(e,bmesh.types.BMEdge)];vs={v for e in edges for v in e.verts};pts=np.array([tuple(v.co)for v in vs]);per=sum(e.calc_length()for e in edges);bm.free()
 return (pts.mean(0),per) if len(pts)>=5 else None
rep={}
for side,parts,boot in [('R',{4,8},7),('L',{3,9},6)]:
 S=M[side+'_UpperArm'];W=M[side+'_Hand'];d=(W-S)/np.linalg.norm(W-S)
 rr=[]
 for t in np.linspace(-.05,.085,55):
  q=W+d*t;r=rings(q,d,parts)
  if r is not None:rr.append((t,*r))
 # The narrow wrist is between the flared cuff and the broad palm.
 wr=min((r for r in rr if .005<r[0]<.070),key=lambda r:r[2]);J[side+'_Hand']=wr[1]
 line=[]
 for t in np.linspace(.18,.9,40):
  r=rings(S+(wr[1]-S)*t,d,parts)
  if r is not None:line.append((t,r[0]))
 ts=np.array([t for t,p in line]);cs=np.array([p for t,p in line])
 def fit(a,b):
  x=cs[(ts>a)&(ts<b)];assert len(x)>=4;c=x.mean(0);u=np.linalg.svd(x-c)[2][0];return c,u if u@d>0 else -u
 c1,u1=fit(.34,.53);c2,u2=fit(.68,.87);q=np.linalg.lstsq(np.column_stack([u1,-u2]),c2-c1,rcond=None)[0];E=(c1+q[0]*u1+c2+q[1]*u2)/2;J[side+'_Forearm']=E
 ar=[];A=M[side+'_Foot']
 for z in np.linspace(A[2]-.025,A[2]+.025,21):
  r=rings([A[0],A[1],z],[0,0,1],{boot})
  if r is not None:ar.append((z,*r))
 an=min(ar,key=lambda r:r[2]);J[side+'_Foot']=an[1]
 rep[side]={'meshy_wrist':W.tolist(),'ring_wrist':wr[1].tolist(),'wrist_move_cm':float(np.linalg.norm(wr[1]-W)*100),'ring_elbow':E.tolist(),'elbow_t':float((E-S)@d/np.linalg.norm(wr[1]-S)),'line_angle_deg':float(np.degrees(np.arccos(np.clip(u1@u2,-1,1)))),'line_gap_mm':float(np.linalg.norm(c1+u1*q[0]-c2-u2*q[1])*1000),'ankle':an[1].tolist(),'arm_centres':cs.tolist()}
 print('JOINT',side,json.dumps(rep[side]))
# The generated body is effectively symmetric; averaged landmarks avoid asymmetric limp from estimator noise.
for key in ['Clavicle','UpperArm','Forearm','Hand','Thigh','Calf','Foot','Toe0']:
 l,r=J['L_'+key],J['R_'+key];q=(l+r*np.array([-1,1,1]))/2;J['L_'+key]=q;J['R_'+key]=q*np.array([-1,1,1])
for key in ['Pelvis','Spine','Spine1','Spine2','Neck','Head']:J[key][0]=0
(P/'work/joints_final.json').write_text(json.dumps({'height_m':1.7,'joints':{k:v.tolist()for k,v in J.items()},'report':rep},indent=2))
