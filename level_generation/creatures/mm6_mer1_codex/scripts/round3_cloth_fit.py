"""Fit the new skirt to the complete legs using the shared signed surface queries, then smooth corrections."""
import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as G
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round3/master.blend'));body=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];s=bpy.context.scene
m=G.load_meshes(G.Glb(P/'work/round3/pilot.glb'))[0];kd=KDTree(len(body.data.vertices))
for v in body.data.vertices:kd.insert(v.co,v.index)
kd.balance();mapping=np.array([kd.find(c)[1]for c in m.rest]);part=np.array([v.value for v in body.data.attributes['piece'].data]);pp=part[mapping];surface=G.Surface(m,pp==2,cap=True,opening={'axis':[0,0,-1]});samples=np.where(np.isin(pp,[6,7])&(m.rest[:,2]<.84))[0]
gn={g.index:g.name for g in body.vertex_groups};roots=[r.pose.bones[f'Cloak_{i}_0']for i in range(16)]
def coords():
 ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();co=np.array([v.co[:]for v in me.vertices]);ev.to_mesh_clear();return co[mapping]
def frame(f):s.frame_set(int(f),subframe=f%1)
records={}
for role in ['Standing','Walking','Running','Hit','Fidget','Attack','Death']:
 a=bpy.data.actions[role];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];fs=np.arange(0,float(a.frame_range[1])+.01,1.);end=float(a.frame_range[1]);fs=np.unique(np.r_[fs,end]);base=[];offset=[];depths=[]
 for f in fs:
  frame(f);orig=np.array([b.location[:]for b in roots]);largest=0
  for it in range(14):
   co=coords();surface.build(co);depth,idx=G.penetration(surface,co[samples],True);largest=max(largest,depth)
   if depth<.8:break
   pt=Vector(co[samples[idx]]);loc,n,fi,d=surface.tree.find_nearest(pt)
   if fi>=len(surface.faces):
    tree=BVHTree.FromPolygons(surface.points.tolist(),surface.faces.tolist(),all_triangles=True);loc,n,fi,d=tree.find_nearest(pt)
   ids=mapping[m.weld_first[surface.faces[fi]]];weights=np.zeros(16)
   for vi in ids:
    for g in body.data.vertices[vi].groups:
     name=gn[g.group]
     if name.startswith('Cloak_'):weights[int(name.split('_')[1])]+=g.weight
   if weights.sum()<.01:break
   c=int(weights.argmax());delta=(pt-loc).normalized()*min(.025,d+.004)
   for j,share in [(c,1.),((c-1)%16,.7),((c+1)%16,.7),((c-2)%16,.2),((c+2)%16,.2)]:
    b=roots[j];M=b.matrix.copy();M.translation+=delta*share;b.matrix=M;bpy.context.view_layer.update()
  base.append(orig);offset.append(np.array([b.location[:]for b in roots])-orig);depths.append(largest)
 # Positive broad envelope limits frame-specific corrections before smoothing; rotations are already smoothed.
 arr=np.array(offset);sm=[]
 for f in fs:
  dt=fs-f
  if role in ['Standing','Walking','Running','Fidget']:dt=(dt+end/2)%end-end/2
  w=np.exp(-.5*(dt/(6. if role=='Death'else 3.))**2);w[abs(dt)>18]=0
  sm.append(np.einsum('f,fij->ij',w,arr)/w.sum())
 for layer in a.layers:
  for strip in layer.strips:
   for cb in strip.channelbags:
    for fc in list(cb.fcurves):
     if 'Cloak_' in fc.data_path and '_0"].location' in fc.data_path:cb.fcurves.remove(fc)
 for f,original,delta in zip(fs,base,sm):
  frame(f)
  for b,location in zip(roots,original+np.array(delta)*1.25):b.location=location;b.keyframe_insert('location',frame=float(f))
 records[role]={'largest_input_mm':max(depths),'max_root_translation_m':float(np.max(np.linalg.norm(arr,axis=2))),'solver_samples':len(fs),'smoothing_sigma_s':.12 if role=='Death'else .08}
 print('CLOTH FIT',role,records[role],flush=True)
# Hold precisely the final death pose.
a=bpy.data.actions['Death'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];frame(float(a.frame_range[1]));terminal={b.name:b.matrix_basis.copy()for b in r.pose.bones};r.animation_data.action=None;bpy.data.actions.remove(bpy.data.actions['Dead']);a=bpy.data.actions.new('Dead');a.use_fake_user=True;r.animation_data.action=a
for f in [0,30]:
 for b in r.pose.bones:
  b.matrix_basis=terminal[b.name]
  for field in ['location','rotation_quaternion','scale']:b.keyframe_insert(field,frame=f)
for a in bpy.data.actions:
 for l in a.layers:
  for st in l.strips:
   for cb in st.channelbags:
    for fc in cb.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round3/cloth_fit.blend'));(P/'review/round3/cloth_fit.json').write_text(json.dumps(records,indent=2))
