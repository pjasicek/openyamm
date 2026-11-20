import bpy,bmesh,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/step1.blend'));o=bpy.data.objects['Body'];me=o.data
co=np.array([tuple(v.co) for v in me.vertices]);pv=np.zeros(len(co),np.int32);me.attributes['piece'].data.foreach_get('value',pv)
M={k:np.array(v) for k,v in json.loads((p/'work/meshy_joints.json').read_text())['joints'].items()};J={k:v.copy() for k,v in M.items()};report={}
def rings(part,at,axis):
 bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[v for v in bm.verts if pv[v.index] not in part],context='VERTS')
 res=bmesh.ops.bisect_plane(bm,geom=bm.verts[:]+bm.edges[:]+bm.faces[:],plane_co=Vector(at),plane_no=Vector(axis));edges=set(e for e in res['geom_cut'] if isinstance(e,bmesh.types.BMEdge));out=[]
 while edges:
  e=edges.pop();todo=list(e.verts);vs=set();es={e}
  while todo:
   v=todo.pop()
   if v in vs:continue
   vs.add(v)
   for ee in v.link_edges:
    if ee in edges:edges.remove(ee);es.add(ee);todo.extend(ee.verts)
  if len(vs)>=4:
   pts=np.array([tuple(v.co) for v in vs]);out.append((pts.mean(0),sum(e.calc_length() for e in es),pts))
 bm.free();return out
for n in ['Pelvis','Spine','Spine1','Spine2','Neck','Head']:J[n][0]=-.003
for n in ['Clavicle','UpperArm','Forearm','Hand','Thigh','Calf','Foot','Toe0']:
 l,r=M['L_'+n],M['R_'+n];c=(l+r)/2;c[0]=-.003;w=(l[0]-r[0])/2
 for s,sign in [('L',1),('R',-1)]:J[s+'_'+n]=c+np.array([sign*w,0,0])
for s,part,sign in [('L',2,1),('R',3,-1)]:
 wr=J[s+'_Hand'];el=J[s+'_Forearm'];axis=(wr-el)/np.linalg.norm(wr-el);profile=[]
 for t in np.arange(-.045,.041,.003):
  at=wr+axis*t;rs=rings([part],at,axis)
  if len(rs)==1:profile.append((t,*rs[0][:2]))
 assert profile
 chosen=min(profile,key=lambda x:x[2]);J[s+'_Hand']=chosen[1]
 # Sleeve hides the elbow: line intersection between sleeve and exposed forearm centrelines.
 sh=J[s+'_UpperArm'];wr=J[s+'_Hand'];ax=(wr-sh)/np.linalg.norm(wr-sh);cs=[]
 for t in np.linspace(.17,.87,20):
  at=sh+(wr-sh)*t;rs=rings([0,part],at,ax)
  if rs:cs.append((t,min(rs,key=lambda x:np.linalg.norm(x[0]-at))[0]))
 a=np.array([v for t,v in cs if t<.4]);b=np.array([v for t,v in cs if t>.60]);ca,cb=a.mean(0),b.mean(0);da=np.linalg.svd(a-ca)[2][0];db=np.linalg.svd(b-cb)[2][0]
 ts=np.linalg.lstsq(np.column_stack([da,-db]),cb-ca,rcond=None)[0];hit=(ca+da*ts[0]+cb+db*ts[1])/2
 if np.linalg.norm(hit-el)<.07:J[s+'_Forearm']=hit
 foot=co[pv==(6 if s=='L' else 5)];ankle=foot[(foot[:,2]>.085)&(foot[:,2]<.16)];J[s+'_Foot']=np.array([np.median(ankle[:,0]),np.median(ankle[:,1]),.12]);J[s+'_Toe0']=np.array([sign*.194-.003,-.135,.025])
 report[s]={'wrist_shift_mm':float(np.linalg.norm(J[s+'_Hand']-M[s+'_Hand'])*1000),'wrist_ring_perimeter_mm':float(chosen[2]*1000),'elbow_line_intersection_m':hit.tolist(),'elbow_shift_mm':float(np.linalg.norm(J[s+'_Forearm']-M[s+'_Forearm'])*1000),'profile':[(float(t),float(per)) for t,c,per in profile]}
assert all(np.isfinite(v).all() for v in J.values());assert all(.17<np.linalg.norm(J[s+'_Hand']-J[s+'_Forearm'])<.30 for s in ['L','R'])
(p/'work/joints_final.json').write_text(json.dumps({'height_m':1.7,'joints':{k:v.tolist() for k,v in J.items()},'report':report},indent=2)+'\n');print('FITTED',json.dumps(report))
