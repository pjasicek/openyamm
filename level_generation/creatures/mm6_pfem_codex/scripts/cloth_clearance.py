"""Move skirt controls locally where the retained calf surface crosses the closed dress."""
import bpy,numpy as np,math,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/reduced.blend'))
r=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];sc=bpy.context.scene;m=o.data
pv=np.array([v.value for v in m.attributes['piece'].data]);rest=np.array([v.co[:] for v in m.vertices])
cloth=np.flatnonzero(pv==100);lookup={int(i):j for j,i in enumerate(cloth)}
polys=[tuple(f.vertices) for f in m.polygons if all(pv[i]==100 for i in f.vertices)]
names=[b.name for b in r.data.bones if b.name.startswith('Skirt_')];ni={n:i for i,n in enumerate(names)}
W=np.zeros((len(rest),len(names)))
for v in m.vertices:
 for g in v.groups:
  n=o.vertex_groups[g.group].name
  if n in ni:W[v.index,ni[n]]=g.weight
skin=np.flatnonzero(np.isin(pv,[8,10])&(rest[:,2]>.29))
report={}
for name in ('Death',):
 a=bpy.data.actions[name];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];N=int(a.frame_range[1])
 snapshots=[];adjust=[]
 for frame in range(N+1):
  sc.frame_set(frame);ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mm=ev.to_mesh();P=np.array([v.co[:] for v in mm.vertices]);ev.to_mesh_clear()
  poses={n:r.pose.bones[n].matrix.copy() for n in names};snapshots.append(poses)
  centres=[]
  for i in skin:
   u=float(np.clip((rest[i,2]-.09)/(.515-.09),0,1))
   centres.append(sum((r.pose.bones[f'B_{s}_Foot'].head.lerp(r.pose.bones[f'B_{s}_Calf'].head,u) for s in 'LR'),Vector())*.5)
  shift=np.zeros((len(names),3))
  for it in range(8):
   V=P+W@shift;tree=BVHTree.FromPolygons(V.tolist(),polys);rows=[];moves=[]
   for i,centre in zip(skin,centres):
    d=Vector(V[i])-centre;length=d.length
    if length<1e-6:continue
    direction=d/length;distance=0.;outer=None;face=None
    for h in range(20):
     loc,no,fi,dist=tree.ray_cast(centre+direction*(distance+.00001),direction,.8-distance)
     if loc is None:break
     distance=(loc-centre).length;outer=distance;face=fi;point=loc
    if outer is None or length-outer<-.032:continue
    ids=list(polys[face]);tri=V[ids];matrix=np.vstack([tri.T,np.ones(3)])
    bary=np.linalg.lstsq(matrix,np.r_[point,1],rcond=None)[0];bary=np.clip(bary,0,1);bary/=bary.sum()
    row=bary@W[ids]
    rows.append(row);moves.append(np.array(direction)*(length+.036-outer))
   if not rows:break
   A=np.array(rows);D=np.array(moves)
   ds=np.linalg.solve(A.T@A+np.eye(len(names))*.015,A.T@D)
   shift+=ds
  adjust.append(shift)
 B=np.array(adjust)
 # Local contact corrections must enter and leave smoothly.
 radius=2;kernel=np.exp(-.5*(np.arange(-radius,radius+1)/.8)**2);kernel/=kernel.sum()
 idx=np.arange(N+1)[:,None]+np.arange(-radius,radius+1)[None,:]
 idx=idx%N if name=='Walking' else np.clip(idx,0,N)
 B=(B[idx]*kernel[None,:,None,None]).sum(1)
 if name=='Walking':B[-1]=B[0]
 prev={}
 for frame,poses in enumerate(snapshots):
  sc.frame_set(frame);desired={n:M.copy() for n,M in poses.items()}
  for i,n in enumerate(names):desired[n].translation+=Vector(B[frame,i])
  for n in names:
   pb=r.pose.bones[n];b=pb.bone;par=b.parent
   parent=desired[par.name] if par.name in desired else r.pose.bones[par.name].matrix
   basis=parent@par.matrix_local.inverted()@b.matrix_local
   local=basis.inverted()@desired[n]
   pb.location=local.translation;pb.keyframe_insert('location',frame=frame)
 for l in a.layers:
  for st in l.strips:
   for bag in st.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
 report[name]={'maximum_control_offset_m':float(np.linalg.norm(B,axis=-1).max())}
 print('CLOTH CLEARANCE',name,report[name])
(p/'work/cloth_clearance.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/reduced.blend'))
