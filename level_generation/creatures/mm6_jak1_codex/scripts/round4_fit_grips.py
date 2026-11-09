"""Fit fixed-count prop surfaces to frozen hand samples; never change contact tolerances or body data."""
import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils import Vector
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as G
config=json.loads((P/'gates.json').read_text());body=G.Glb(P/'export/mm6_jak1.glb');staff=G.Glb(P/'export/mm6_jak1_staff.glb');report=G.Report(config)
body_meshes=[m for m in G.load_meshes(body)if '/colour'in m.label];staff_meshes=G.load_meshes(staff)
clips=[(name,G.sample_grid(lo,hi,48),body.pose(animation,G.sample_grid(lo,hi,48)))for name,animation,lo,hi in body.clips()]
records=[];fitted={}
for level,side in [(0,'L'),(2,'L'),(3,'L'),(2,'R'),(3,'R')]:
 mesh=body_meshes[level];G.configure_mesh(mesh,config,report);tri,bary,groups,_=G.grip_points(mesh,side,config)
 hand=next(h for h in config['props'][0]['hands']if h['side']==side)
 all_points=[];groups_global=[];offset=0
 for name,times,poses in clips:
  for t,pose in zip(times,poses):
   if not G.held_samples(config['props'][0],hand,name,t):continue
   points=mesh.posed(pose);world=np.einsum('sk,tkj->tsj',bary,points[tri]).reshape(-1,3)
   local=G.transform(G.C@np.linalg.inv(pose[body.names['Staff']]),world)
   all_points.append(local)
   for group in groups:groups_global.append(np.flatnonzero(group)+offset)
   offset+=len(local)
 # Quantization is only for fitting speed; final shared gate uses the original unrounded surface samples.
 points,inverse=np.unique(np.round(np.concatenate(all_points),4),axis=0,return_inverse=True)
 groups_global=[np.unique(inverse[i])for i in groups_global];sizes=np.array([len(i)for i in groups_global]);starts=np.r_[0,np.cumsum(sizes)[:-1]];sample_ids=np.concatenate(groups_global)
 prop=staff_meshes[level];original=fitted.get(level,prop.rest.copy()).copy();surface=G.Surface(prop,np.ones(len(prop.rest),bool))
 z=-original[:,1];mask=((z>.20)&(z<.36))if side=='L'else((z>-.13)&(z<.16))
 assert mask.any();vectors=[Vector(p)for p in points]
 def coords(params):
  a,b,c,dx,dy,slope=params;matrix=np.array([[1+a,b],[b,1+c]]);out=original.copy()
  out[np.ix_(mask,[0,2])]=(original[np.ix_(mask,[0,2])]@matrix.T)*(1+slope*((z[mask]-(.29 if side=='L'else 0))/.07))[:,None]+[dx,dy]
  return out
 def cost(params):
  verts=coords(params);surface.build(verts)
  hit=[surface.tree.find_nearest(p)for p in vectors]
  d=np.array([h[3]for h in hit]);norm=np.array([tuple(h[1])for h in hit]);near=np.array([tuple(h[0])for h in hit]);signed=np.where(np.sum((points-near)*norm,axis=1)<0,-d,d)
  gaps=np.minimum.reduceat(d[sample_ids],starts)*1000;depth=np.maximum(-signed*1000,0)
  vg=np.maximum(gaps-2.82,0);vp=np.maximum(depth-2.82,0)
  score=vg.max()**2+vp.max()**2+.1*(np.mean(vg**2)+np.mean(vp**2))
  return float(score),float(gaps.max()),float(depth.max())
 params=np.zeros(6);best=cost(params);initial=best;steps=np.array([.08,.08,.08,.001,.001,.08])
 for iteration in range(100):
  if best[0]<1e-7:break
  options=[]
  for i in range(6):
   for sign in [-1,1]:
    q=params.copy();q[i]+=sign*steps[i]
    if max(abs(q[:3]))>.65 or max(abs(q[3:5]))>.007 or abs(q[5])>.6:continue
    options.append((cost(q),q))
  value,q=min(options,key=lambda v:v[0][0])
  if value[0]<best[0]-1e-8:params=q;best=value
  else:steps*=.5
  if steps[0]<.0005:break
  print('FIT',level,side,iteration,best,params.tolist(),flush=True)
 fitted[level]=coords(params)
 records.append({'lod':level,'hand':side,'initial_score_gap_depth':initial,'fitted_score_gap_depth':best,'affine_parameters':params.tolist(),'sample_quantization_m':.0001,'fixed_triangles':len(prop.faces)})
bpy.ops.wm.open_mainfile(filepath=str(P/'source/mm6_jak1_staff.blend'))
for level,points in fitted.items():
 obj=bpy.data.objects['Staff'if level==0 else f'Staff_LOD{level}'];prop=staff_meshes[level]
 # Export vertices are split at UV/normal seams; map the identical source positions, then apply the same fit.
 raw=(prop.rest@G.C[:3,:3]);target=(points@G.C[:3,:3]);lookup={tuple(np.rint(v*1e6).astype(int)):q for v,q in zip(raw,target)}
 for v in obj.data.vertices:
  distance=np.linalg.norm(raw-np.array(v.co),axis=1);i=int(np.argmin(distance));assert distance[i]<2e-6,float(distance[i]);v.co=target[i]
 obj.data.update()
 for other in bpy.context.scene.objects:other.select_set(other==obj)
 bpy.context.view_layer.objects.active=obj
 bpy.ops.export_scene.gltf(filepath=str(P/f'work/round4/staff_lod{level}.glb'),use_selection=True,export_format='GLB',export_yup=False,export_animations=False,export_skins=False,export_morph=False,export_attributes=False)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'source/mm6_jak1_staff.blend'))
(P/'review/round4/grip_fit.json').write_text(json.dumps(records,indent=2));print('GRIP FIT FINISHED',flush=True)
