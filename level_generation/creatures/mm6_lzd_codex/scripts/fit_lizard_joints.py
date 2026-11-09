"""Compare independent skin cross-sections with auto-rig wrist/elbow estimates."""
import bpy,bmesh,json,sys,math
import numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/step1.blend'));ob=bpy.data.objects['Body'];me=ob.data
M={k:np.array(v)for k,v in json.loads((P/'work/meshy_joints.json').read_text())['joints'].items()};J={k:v.copy()for k,v in M.items()}
pv=np.array([x.value for x in me.attributes['piece'].data]);report={}
def shell(piece):
 b=bmesh.new();b.from_mesh(me);b.verts.ensure_lookup_table();bmesh.ops.delete(b,geom=[v for v in b.verts if pv[v.index]!=piece],context='VERTS');return b
def ring(base,point,axis,radius):
 b=base.copy();r=bmesh.ops.bisect_plane(b,geom=list(b.verts)+list(b.edges)+list(b.faces),plane_co=Vector(point),plane_no=Vector(axis));edges=[e for e in r['geom_cut']if isinstance(e,bmesh.types.BMEdge)];vs={v for e in edges for v in e.verts if (v.co-Vector(point)).length<radius};points=np.array([tuple(v.co)for v in vs]);per=sum(e.calc_length()for e in edges if all(v in vs for v in e.verts));b.free();return (points.mean(0),per)if len(points)>=5 else None
# The quiver biases the left shoulder and lower spine in the auto-rig.
for name,z in [('Pelvis',M['Pelvis'][2]),('Spine',1.075),('Spine1',1.20),('Spine2',1.315)]:
 J[name]=np.array([0,.02,z])
for side,piece in [('L',3),('R',4)]:
 b=shell(piece);S=np.array([.21 if side=='L' else -.21,.02,1.335]);J[side+'_UpperArm']=S;E=M[side+'_Forearm'];W=M[side+'_Hand'];d=(W-E)/np.linalg.norm(W-E);rings=[]
 for t in np.arange(-.045,.046,.003):
  r=ring(b,W+d*t,d,.085)
  if r:rings.append((t,*r))
 assert rings,side
 rr=min(rings,key=lambda r:r[2]);wr=rr[1];J[side+'_Hand']=wr
 upper=[];lower=[];armd=wr-S;L=np.linalg.norm(armd);armd/=L
 for t in np.linspace(.2,.88,36):
  r=ring(b,S+armd*L*t,armd,.10)
  if r:
   if t<.42:upper.append(r[0])
   if t>.61:lower.append(r[0])
 def fit(points):
  a=np.array(points);assert len(a)>3;c=a.mean(0);u=np.linalg.svd(a-c)[2][0];return c,u
 a,u=fit(upper);c,v=fit(lower);q=np.linalg.lstsq(np.column_stack([u,-v]),c-a,rcond=None)[0];el=(a+q[0]*u+c+q[1]*v)/2;et=float((el-S)@armd/L);bend=math.degrees(math.acos(np.clip(abs(u@v),-1,1)))
 use=.35<et<.67 and bend>3
 if use:J[side+'_Forearm']=el
 report[side]={'meshy_shoulder':M[side+'_UpperArm'].tolist(),'anatomical_shoulder':S.tolist(),'meshy_wrist':W.tolist(),'ring_wrist':wr.tolist(),'wrist_difference_mm':float(np.linalg.norm(W-wr)*1000),'meshy_elbow':E.tolist(),'ring_elbow':el.tolist(),'ring_elbow_fraction':et,'ring_line_angle_deg':bend,'used_ring_elbow':use}
 b.free()
 # Source feet are broad reptile feet; ankle stays inside the shin above the claw fan.
 b=shell(1);A=M[side+'_Foot'];rr=[]
 for z in np.arange(.08,.201,.005):
  r=ring(b,[A[0],A[1],z],[0,0,1],.095)
  if r:rr.append(r)
 if rr:
  r=min(rr,key=lambda a:a[1]);report[side]['ankle_ring']=r[0].tolist()
 # The skin ankle shell is interrupted by greaves; use the visible hinge above the claw fan.
 J[side+'_Foot']=np.array([.231 if side=='L' else -.231,.005,.105])
 b.free()
# Meshy head placement is a guide; this neck articulates below the rigid snout.
(P/'work/joints_final.json').write_text(json.dumps({'height_m':1.7,'joints':{k:v.tolist()for k,v in J.items()},'report':report},indent=2));print('JOINTS',report)
