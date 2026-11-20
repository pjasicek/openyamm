"""Revision 2: keep the right pad seated beneath its chest-mounted steel collar."""
from pathlib import Path
import bpy,sys,json,numpy as np
from mathutils import Vector,Matrix
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
from common import setup_render,workbench_clay,render_views,ortho_camera
from shoulder_intersections import intersections
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_revision1.blend'))
body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];me=body.data;me.calc_loop_triangles()
pv=np.zeros(len(me.vertices),int);me.attributes['piece'].data.foreach_get('value',pv)
ids=np.where(pv==11)[0];si=np.where(pv==7)[0];skin=np.where(pv==0)[0]
old=np.array([v.co[:] for v in me.vertices]);uv={l.name:np.array([v.uv[:] for v in l.data]) for l in me.uv_layers}
# Transfer the underlying shoulder/chest skin continuously across both armour layers.
# Fitting in Standing preserves the accepted silhouette despite the new attachment.
from mathutils.bvhtree import BVHTree
rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0]
bpy.context.scene.frame_set(0)
ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();posed=[v.co.copy() for v in m.vertices];ev.to_mesh_clear()
transforms={g.name:rig.pose.bones[g.name].matrix@rig.data.bones[g.name].matrix_local.inverted() for g in body.vertex_groups}
body_faces=[t.vertices[:] for t in me.loop_triangles if all(pv[i]==0 for i in t.vertices)]
tree=BVHTree.FromPolygons(posed,body_faces,all_triangles=True)
weights={}
for i in np.r_[si,ids]:
 if pv[i]==7 and old[i,2]<1.18:continue
 loc,n,fi,d=tree.find_nearest(posed[i])
 if d>.08:continue
 tri=body_faces[fi];pts=np.array([posed[v] for v in tri]);q=np.array(loc)
 uvw=np.linalg.lstsq(np.vstack([pts.T,np.ones(3)]),np.r_[q,1.],rcond=None)[0]
 uvw=np.clip(uvw,0,1);uvw/=uvw.sum();w={}
 for v,a in zip(tri,uvw):
  for g in me.vertices[v].groups:
   name=body.vertex_groups[g.group].name;w[name]=w.get(name,0)+float(a)*g.weight
 if pv[i]==7:
  t=float(np.clip((old[i,2]-1.18)/.10,0,1));t=t*t*(3-2*t);w={n:a*t for n,a in w.items()}
  for g in me.vertices[i].groups:
   name=body.vertex_groups[g.group].name;w[name]=w.get(name,0)+g.weight*(1-t)
 w=dict(sorted(w.items(),key=lambda x:-x[1])[:4]);total=sum(w.values());w={n:a/total for n,a in w.items()}
 mat=Matrix([[sum(a*transforms[n][r][c] for n,a in w.items()) for c in range(4)] for r in range(4)])
 dest=posed[i].copy()
 if pv[i]==7:
  rim=float(np.clip((-old[i,0]-.14)/.07,0,1));rim=rim*rim*(3-2*rim)
  front=float(np.clip((.08-old[i,1])/.10,0,1));front=front*front*(3-2*front)
  back=float(np.clip((old[i,1]-.06)/.05,0,1));back=back*back*(3-2*back)
  dest+=Vector((0,-.008*front+.004*back,0))*rim
 me.vertices[i].co=mat.inverted()@dest
 for g in body.vertex_groups:g.remove([int(i)])
 for name,a in w.items():
  if a>1e-7:body.vertex_groups[name].add([int(i)],a,'REPLACE')
 weights[int(i)]=w
# Small clearance for the coarse nested shells.
down=(rig.data.bones['B_R_Forearm'].head_local-rig.data.bones['B_R_UpperArm'].head_local).normalized()
for i in ids:me.vertices[i].co+=down*.010
for l in me.uv_layers:assert np.array_equal(uv[l.name],np.array([v.uv[:] for v in l.data]))
assert np.array_equal(old[~np.isin(pv,[7,11])],np.array([v.co[:] for v in me.vertices])[~np.isin(pv,[7,11])])
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_revision2.blend'))
def faces(ids):
 d={int(v):i for i,v in enumerate(ids)}
 return np.array([[d[v] for v in t.vertices] for t in me.loop_triangles if all(v in d for v in t.vertices)])
pf=faces(ids);sf=faces(si);kf=faces(skin);rows={}
from g6_head_clearance import Clearance
head=Clearance(body)
for role in ['Standing','Walking','Running','Attack','Hit','Fidget','Death','Dead']:
 act=bpy.data.actions[role];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
 row={'samples':0,'steel_crossing_frames':[],'max_skin_crossings':0,'max_skin_crossings_time':0,'head_depth_m':0,'head_time':0}
 for f in np.arange(0,float(act.frame_range[1])+.0001,30/192):
  bpy.context.scene.frame_set(int(f),subframe=float(f%1));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=np.array([v.co[:] for v in m.vertices]);ev.to_mesh_clear()
  hits=intersections(co[si],sf,co[ids],pf);bodyhits=intersections(co[skin],kf,co[ids],pf)
  row['samples']+=1
  dep=head.measure()[0]
  if dep>row['head_depth_m']:row['head_depth_m']=dep;row['head_time']=float(f)/30
  if hits:
   row['steel_crossing_frames'].append([float(f)/30,len(hits)])
   hp=ids[np.unique(pf[[b for a,b in hits]])];hs=si[np.unique(sf[[a for a,b in hits]])]
   if 'crossing_rest_bounds' not in row:row['crossing_rest_bounds']={'cap':[old[hp].min(0).tolist(),old[hp].max(0).tolist()],'plate':[old[hs].min(0).tolist(),old[hs].max(0).tolist()]}
  if len(bodyhits)>row['max_skin_crossings']:row['max_skin_crossings']=len(bodyhits);row['max_skin_crossings_time']=float(f)/30
 rows[role]=row;print('SHOULDER',role,row,flush=True)
(p/'review/revision2/shoulder_gate.json').write_text(json.dumps({'sample_hz':192,'weights':weights,'rest_fit_m':.010,'clips':rows},indent=2))
assert all(not row['steel_crossing_frames'] for row in rows.values()),'Copper crosses steel'
assert max(row['head_depth_m'] for row in rows.values())<.01,'Head contact exceeds playbook limit'
me.materials.clear()
for i,c in enumerate([(.3,.3,.3,1),(.2,.5,.95,1),(.85,.3,.05,1)]):
 m=bpy.data.materials.new('part'+str(i));m.diffuse_color=c;me.materials.append(m)
for face in me.polygons:face.material_index=1 if pv[face.vertices[0]] in (7,13) else 2 if pv[face.vertices[0]] in (11,12) else 0
scene=setup_render();workbench_clay(scene)
for act,f in [('Standing',25),('Walking',19),('Running',6),('Attack',16),('Attack',23),('Hit',3),('Death',30)]:
 rig.animation_data.action=bpy.data.actions[act];rig.animation_data.action_slot=rig.animation_data.action.slots[0]
 scene.frame_set(f);bpy.context.view_layer.update()
 if act!='Death':render_views(str(p/'review/revision2'/f'{act}_{f}'),1.33,.7,views=('front','right'),resolution=(800,800))
 target=Vector((-.15,-.03,1.3)) if act!='Death' else Vector((0,.35,.4))
 cam=ortho_camera('above',target+Vector((-1.2,-2.2,2.3)),(0,0,0),.85)
 cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();scene.camera=cam
 scene.render.filepath=str(p/'review/revision2'/f'{act}_{f}_above.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
