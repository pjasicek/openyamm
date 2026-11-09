"""Fit the skinned shell to all equipped poses by small rest-space displacements with outside constraints."""
import bpy,sys,os,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];path=P/'work/addons_v2/equipped.blend';bpy.ops.wm.open_mainfile(filepath=str(path));r=bpy.data.objects['Rig'];b=bpy.data.objects['Kept'];o=bpy.data.objects['hes_kept_plate'];sc=bpy.context.scene;pc=[v.value for v in b.data.attributes['piece'].data];fs=np.array([p.vertices[:]for p in b.data.polygons if pc[p.vertices[0]]==1]);ids=[[v.index]for v in o.data.vertices]+[list(e.vertices)for e in o.data.edges]+[list(p.vertices)for p in o.data.polygons];names=[g.name for g in o.vertex_groups];W=np.zeros((len(o.data.vertices),len(names)))
for v in o.data.vertices:
 for g in v.groups:W[v.index,g.group]=g.weight
restinv={n:r.data.bones[n].matrix_local.inverted()for n in names};constraints=[];inside_count=0;max_before=0

def points(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();p=[v.co.copy()for v in m.vertices];ev.to_mesh_clear();return p

def inside(tri,p):
 a,c,e=(tri-np.array(p)).transpose(1,0,2);la=np.linalg.norm(a,axis=1);lc=np.linalg.norm(c,axis=1);le=np.linalg.norm(e,axis=1);num=np.einsum('ij,ij->i',a,np.cross(c,e));den=la*lc*le+np.einsum('ij,ij->i',a,c)*le+np.einsum('ij,ij->i',c,e)*la+np.einsum('ij,ij->i',e,a)*lc;return abs(float(np.arctan2(num,den).sum()/(2*np.pi)))>.5
for a in bpy.data.actions:
 if not(a.name.startswith('Kept_Armed') or a.name=='Kept_ClubR1'):continue
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];count_before=inside_count
 for f in np.arange(0,a.frame_range[1]+.001,.5):
  sc.frame_set(int(f),subframe=float(f%1));bp=points(b);tri=np.array(bp,dtype=float)[fs];tree=BVHTree.FromPolygons(bp,fs.tolist(),all_triangles=True);ps=points(o);M=np.array([np.array((r.pose.bones[n].matrix@restinv[n]).to_3x3()).ravel()for n in names]);A=(W@M).reshape(-1,3,3)
  for ii in ids:
   p=sum((ps[i]for i in ii),Vector())/len(ii);h,n,j,d=tree.find_nearest(p,.012)
   if h is None or d<1e-6:continue
   inward=(p-h).dot(n)<-.5*d;penetrating=inward and inside(tri,p)
   if not penetrating and (len(ii)>1 or d>.008):continue
   direction=np.array((h-p if penetrating else p-h).normalized());rhs=(d+.0015) if penetrating else (.0003-d);coeff=np.array([A[i].T@direction/len(ii)for i in ii]);constraints.append((ii,coeff,rhs));inside_count+=int(penetrating)
   if penetrating:max_before=max(max_before,d)
 print('SHELL_CONSTRAINTS',a.name,inside_count-count_before,flush=True)
delta=np.zeros((len(o.data.vertices),3))
for iteration in range(100):
 worst=0.
 for ii,c,rhs in constraints:
  deficit=rhs-float((delta[ii]*c).sum());worst=max(worst,deficit)
  if deficit>0:delta[ii]+=c*(deficit/(c*c).sum())
 if worst<1e-6:break
assert worst<1e-5,(iteration,worst)
max_move=float(np.linalg.norm(delta,axis=1).max());assert max_move<.012,max_move
for v,d in zip(o.data.vertices,delta):v.co+=Vector(d)
report={'constraints':len(constraints),'penetrating_samples':inside_count,'max_before_m':max_before,'max_rest_shift_m':max_move,'solver_residual_m':worst,'iterations':iteration+1};record=P/'review/addons_v2/plate_clearance.json';old=json.loads(record.read_text()) if record.exists() else {};history=old.get('passes',[old] if old else []);history.append(report);record.write_text(json.dumps({'passes':history,'max_cumulative_shift_bound_m':sum(x['max_rest_shift_m'] for x in history)},indent=2)+'\n');bpy.ops.wm.save_as_mainfile(filepath=str(path));print('SHELL_FIT',report,flush=True);sys.stdout.flush();sys.stderr.flush();os._exit(0)
