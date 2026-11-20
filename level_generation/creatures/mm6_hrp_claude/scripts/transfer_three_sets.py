"""Verify and transfer independent body/wing UVs; head UVs, skin and all nine clips remain intact."""
import bpy,json
import numpy as np
from pathlib import Path
from mathutils import Vector,kdtree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/three_sets.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];me=body.data
rig.animation_data_clear()
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
with bpy.data.libraries.load(str(P/'work/anim_v1.blend'),link=False) as (src,dst):dst.actions=src.actions
for a in bpy.data.actions:a.use_fake_user=True
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update();T=np.array([tuple(body.matrix_world@v.co) for v in me.vertices]);report={}
head_before=np.array([me.uv_layers.active.data[i].uv[:] for f in me.polygons if f.material_index==1 for i in f.loop_indices])
for label,slot in [('torso',0),('wings',2)]:
 before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(P/'meshy'/f'{label}_retexture_v1/model_urls_glb.glb'));src=max((o for o in bpy.data.objects if o not in before and o.type=='MESH'),key=lambda o:len(o.data.polygons));sm=src.data
 S=np.array([tuple(src.matrix_world@v.co) for v in sm.vertices]);ids=sorted({i for f in me.polygons if (f.material_index==2)==(slot==2) for i in f.vertices});sub=T[ids];scale=np.ptp(sub,axis=0).max()/np.ptp(S,axis=0).max();S=S*scale+(sub.max(0)+sub.min(0))/2-(S.max(0)+S.min(0))/2*scale
 tree=kdtree.KDTree(len(sm.polygons))
 for f in sm.polygons:tree.insert(Vector(S[list(f.vertices)].mean(0)),f.index)
 tree.balance();worst=0;corner_error=0;count=0;uv=me.uv_layers.active.data;su=sm.uv_layers.active.data
 for f in me.polygons:
  if f.material_index!=slot:continue
  _,si,dist=tree.find(Vector(T[list(f.vertices)].mean(0)));worst=max(worst,dist);sf=sm.polygons[si];assert len(sf.vertices)==len(f.vertices)==3
  for li,vi in zip(f.loop_indices,f.vertices):
   ds=np.linalg.norm(S[list(sf.vertices)]-T[vi],axis=1);k=int(ds.argmin());corner_error=max(corner_error,float(ds[k]));uv[li].uv=su[sf.loop_indices[k]].uv
  count+=1
 assert worst<.00001 and corner_error<.00001,(label,worst,corner_error)
 report[label]={'faces':count,'max_centroid_error_m':worst,'max_corner_error_m':corner_error,'source_faces':len(sm.polygons)}
 for o in list(bpy.data.objects):
  if o not in before:bpy.data.objects.remove(o,do_unlink=True)
head_after=np.array([me.uv_layers.active.data[i].uv[:] for f in me.polygons if f.material_index==1 for i in f.loop_indices]);assert np.array_equal(head_before,head_after)
for a in bpy.data.actions:a.use_fake_user=True
assert {a.name for a in bpy.data.actions}=={'Standing','Walking','Running','Fidget','Attack','Cast','Hit','Death','Dead'}
# Native flight proportions: the model's spread wings were 25% too long relative to the head-to-foot height.
pa=[v.value for v in me.attributes['part'].data]
for sd,sg,part in [('L',1,1),('R',-1,10)]:
 anchor=Vector((-.01+sg*.10,.09,1.43))
 ids=[v.index for v in me.vertices if pa[v.index]==part]
 for vg in body.vertex_groups:vg.remove(ids)
 for i in ids:
  x=abs(me.vertices[i].co.x)
  for k in range(3):
   w=float(np.interp(x,[.29,.75,1.25],np.eye(3)[k]))
   if w>0:body.vertex_groups[sd+'Wing'+str(k)].add([i],w,'REPLACE')
 for v in me.vertices:
  if pa[v.index]==part:v.co=anchor+(v.co-anchor)*.80
 bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
 for k in range(3):
  b=rig.data.edit_bones[sd+'Wing'+str(k)];b.head=anchor+(b.head-anchor)*.80;b.tail=anchor+(b.tail-anchor)*.80
 bpy.ops.object.mode_set(mode='OBJECT')
report['wing_span_scale']=.80
(P/'work/three_set_uv_transfer.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_master.blend'));print('THREE_SET_UV',report,flush=True)
