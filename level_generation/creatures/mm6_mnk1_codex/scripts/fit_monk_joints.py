"""Fit exposed wrist rings and garment centrelines; covered anatomy is recorded inference."""
import bpy,bmesh,json,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/step1.blend'));body=bpy.data.objects['Body'];me=body.data
pv=np.zeros(len(me.vertices),np.int32);me.attributes['piece'].data.foreach_get('value',pv)
co=np.array([tuple(v.co) for v in me.vertices]);H=float(co[:,2].max())
M={k:np.array(v) for k,v in json.loads((p/'work/meshy_joints.json').read_text())['joints'].items()}
J={k:v.copy() for k,v in M.items()};report={}
bases={}
def shell(ids):
 bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table()
 bmesh.ops.delete(bm,geom=[v for v in bm.verts if pv[v.index] not in ids],context='VERTS');return bm
bases['body']=shell([0]);bases['skirt']=shell([1])
def rings(base,point,normal):
 bm=base.copy();res=bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=Vector(point),plane_no=Vector(normal))
 edges=set(e for e in res['geom_cut'] if isinstance(e,bmesh.types.BMEdge));result=[]
 while edges:
  e=edges.pop();todo=list(e.verts);vs=set()
  while todo:
   v=todo.pop()
   if v in vs:continue
   vs.add(v)
   for ed in v.link_edges:
    if ed in edges:edges.remove(ed);todo.extend(ed.verts)
  if len(vs)>=4:
   pts=np.array([tuple(v.co) for v in vs]);result.append(pts)
 bm.free();return result
# Meshy inferred a zigzag spine in the robe. Each axis joint belongs at the torso/skirt cross-section centre.
for name in ['Pelvis','Spine','Spine1','Spine2']:
 z=J[name][2];base=bases['skirt'] if z<1.075 else bases['body'];rs=rings(base,(0,0,z),(0,0,1))
 rs=[r for r in rs if r[:,0].min()<0<r[:,0].max()]
 assert rs,name
 r=min(rs,key=lambda r:np.linalg.norm(r.mean(0)[:2]));centre=(r.min(0)+r.max(0))/2
 J[name]=np.array([centre[0],centre[1],z])
J['Neck']=np.array([-.006,-.025,1.405]);J['Head']=np.array([-.006,-.018,1.475])
for name in ['UpperArm','Clavicle','Thigh','Calf','Foot','Toe0']:
 left,right=M['L_'+name],M['R_'+name];v=(left+right)/2;width=(left[0]-right[0])/2
 for sd,sign in [('L',1),('R',-1)]:J[sd+'_'+name]=np.array([sign*width-.006,v[1],v[2]])
J['L_Clavicle']=np.array([.035,-.020,1.389]);J['R_Clavicle']=np.array([-.047,-.020,1.389])
for sd,part in [('L',2),('R',3)]:
 bm=shell([part]);bound=set(e for e in bm.edges if e.is_boundary);loops=[]
 while bound:
  e=bound.pop();todo=list(e.verts);vs=set()
  while todo:
   v=todo.pop()
   if v in vs:continue
   vs.add(v)
   for ed in v.link_edges:
    if ed in bound:bound.remove(ed);todo.extend(ed.verts)
  loops.append(np.array([tuple(v.co) for v in vs]))
 ring=max(loops,key=len);base=ring.mean(0);axis=M[sd+'_Hand']-base;axis/=np.linalg.norm(axis)
 profile=[]
 for t in np.arange(.01,.13,.005):
  at=base+axis*t;rs=rings(bm,at,axis)
  if rs:
   r=min(rs,key=lambda r:np.linalg.norm(r.mean(0)-at));c=r.mean(0)
   radius=float(np.linalg.norm(r-c,axis=1).mean());profile.append((float(t),radius,c.tolist(),len(rs)))
 print('WRIST_PROFILE',sd,json.dumps(profile))
 # The shell continues up the forearm under the sleeve; its open boundary is not the wrist.
 eligible=[r for r in profile if .035<=r[0]<=.080 and r[3]==1]
 assert eligible
 chosen=min(eligible,key=lambda r:r[1]);wr=np.array(chosen[2]);bm.free();J[sd+'_Hand']=wr
 sh=J[sd+'_UpperArm'];axis=(wr-sh)/np.linalg.norm(wr-sh);centres=[]
 for t in np.linspace(.12,.86,20):
  at=sh+(wr-sh)*t;rs=rings(bases['body'],at,axis)
  if rs:centres.append((t,min(rs,key=lambda r:np.linalg.norm(r.mean(0)-at)).mean(0)))
 # The widening sleeve has no skin elbow landmark. The mid-arm ring and source 1:1 segment ratio constrain it.
 near=min(centres,key=lambda tc:abs(tc[0]-.5))[1];el=sh+(wr-sh)*.50
 el+=np.clip(near-el,-.025,.025)
 J[sd+'_Forearm']=el
 foot=co[pv==(8 if sd=='L' else 7)];J[sd+'_Foot']=np.array([np.median(foot[:,0]),.015,.11]);J[sd+'_Toe0']=np.array([np.median(foot[:,0]),-.13,.032])
 report[sd]={'wrist_ring_vertices':len(ring),'wrist_shift_cm':float(np.linalg.norm(wr-M[sd+'_Hand'])*100),'elbow_shift_cm':float(np.linalg.norm(el-M[sd+'_Forearm'])*100),'elbow_basis':'sleeve ring plus source equal upper/forearm ratio; hidden anatomy inferred','arm_centres':[(float(t),c.tolist()) for t,c in centres]}
for bm in bases.values():bm.free()
assert all(np.isfinite(v).all() for v in J.values())
assert abs(np.linalg.norm(J['L_Hand']-J['L_UpperArm'])-np.linalg.norm(J['R_Hand']-J['R_UpperArm']))<.035
(p/'work/joints_final.json').write_text(json.dumps({'height_m':H,'joints':{k:v.tolist() for k,v in J.items()},'report':report},indent=2)+'\n')
# Discard imported custom normals; the sleeve's bright shards are shading artifacts on otherwise connected faces.
bpy.context.view_layer.objects.active=body
if me.has_custom_normals:bpy.ops.mesh.customdata_custom_splitnormals_clear()
for f in me.polygons:f.use_smooth=True
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/step1.blend'))
print('FITTED',json.dumps(report))
