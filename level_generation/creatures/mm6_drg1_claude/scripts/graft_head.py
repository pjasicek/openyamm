"""Replace the failed full-body head with the jaw-separated HD head, preserving body/wing UVs."""
import bpy,bmesh,math,json
import numpy as np
from pathlib import Path
from mathutils import Vector,kdtree
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_master.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];rig.animation_data_clear()
for pb in rig.pose.bones:pb.matrix_basis.identity()
with bpy.data.libraries.load(str(P/'work/head_static_v2.blend'),link=False) as (src,dst):dst.objects=['Body']
head=dst.objects[0];head.name='ReplacementHead';bpy.context.collection.objects.link(head);me=head.data;co=np.array([v.co[:] for v in me.vertices]);pa=np.array([v.value for v in me.attributes['part'].data]);weights=[]
# The open-mouth gap supplies a separator between the upper muzzle and mandible.
for x,y,z in co:
 cut=.51+.20*(y+.10);jaw=(y<-.07 and z<cut)
 if jaw:weights.append({'Jaw':1.})
 else:
  h=float(np.clip((z-.07)/.35,0,1));weights.append({'Neck3':1-h,'Head':h})
main=np.where(pa==0)[0];tree=kdtree.KDTree(len(main))
for i in main:tree.insert(Vector(co[i]),int(i))
tree.balance()
for part in sorted(set(pa)):
 if part==0:continue
 ids=np.where(pa==part)[0];anchor=min((tree.find(Vector(co[i])) for i in ids),key=lambda q:q[2])[1];w=weights[anchor]
 if part==1:w={'Jaw':1.}
 for i in ids:weights[i]=w
for n in ['Head','Jaw','Neck3']:head.vertex_groups.new(name=n)
for i,w in enumerate(weights):
 for n,value in w.items():
  if value>.001:head.vertex_groups[n].add([i],value,'REPLACE')
for v in me.vertices:v.co=Vector(v.co)*.35+Vector((0,-.35,.52))
# Preserve jaw frames while relocating their actual hinges.
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT');b=rig.data.edit_bones['Head'];b.head=(0,-.355,.710);b.tail=(0,-.510,.695);b=rig.data.edit_bones['Jaw'];b.head=(0,-.385,.701);b.tail=(0,-.495,.643);b=rig.data.edit_bones['Socket_Mouth'];b.head=(0,-.512,.677);b.tail=(0,-.55,.677);bpy.ops.object.mode_set(mode='OBJECT')
# Eliminate old skull and neck surface concealed inside the replacement neck stub.
bm=bmesh.new();bm.from_mesh(body.data);doomed=[f for f in bm.faces if f.material_index==1 or (f.material_index==0 and abs(f.calc_center_median().x)<.12 and f.calc_center_median().y<-.20 and f.calc_center_median().z>.553)]
bmesh.ops.delete(bm,geom=doomed,context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
# Only small accidental neck holes are filled; membranes and mouth stay open.
bound=[e for e in bm.edges if e.is_boundary];seen=set();fixed=0
for edge in bound:
 if edge in seen:continue
 stack=[edge];es=[];vs=set()
 while stack:
  e=stack.pop()
  if e in seen:continue
  seen.add(e);es.append(e);vs.update(e.verts)
  for v in e.verts:stack.extend(q for q in v.link_edges if q.is_boundary and q not in seen)
 c=sum((v.co for v in vs),Vector())/len(vs);radius=max((v.co-c).length for v in vs)
 if 3<=len(vs)<=14 and radius<.035 and abs(c.x)<.13 and c.y<-.18 and c.z<.54:
  made=bmesh.ops.holes_fill(bm,edges=es,sides=0)['faces'];bmesh.ops.triangulate(bm,faces=made);fixed+=len(made)
bm.to_mesh(body.data);bm.free()
# Bury the old cut ring slightly inside the new neck; blend both surfaces on the same neck bone.
hbm=bmesh.new();hbm.from_mesh(me);htree=BVHTree.FromBMesh(hbm);bbm=bmesh.new();bbm.from_mesh(body.data)
for v in {v for e in bbm.edges if e.is_boundary for v in e.verts}:
 if abs(v.co.x)<.12 and v.co.y<-.2 and .51<v.co.z<.59:
  loc,n,_,dist=htree.find_nearest(v.co)
  if dist<.06:v.co=loc-n*.001
bbm.to_mesh(body.data);bbm.free();hbm.free()
# Reduction here affects the dedicated high-resolution head only; protect teeth and horn tips by geometry.
bpy.ops.object.select_all(action='DESELECT');head.select_set(True);bpy.context.view_layer.objects.active=head;mod=head.modifiers.new('HeadBaseReduction','DECIMATE');mod.ratio=.48;mod.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.ops.object.vertex_group_limit_total(limit=4);bpy.ops.object.vertex_group_normalize_all(lock_active=False)
me=head.data;me.materials.clear();mat=bpy.data.materials.new('DrakeHeadNew');mat.use_nodes=True;me.materials.append(mat)
for f in me.polygons:f.material_index=0;f.use_smooth=True
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.004);bpy.ops.uv.pack_islands(rotate=True,margin=.004,margin_method='FRACTION');bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.export_scene.gltf(filepath=str(P/'work/head_upload_v2.glb'),use_selection=True,export_format='GLB',export_animations=False,export_skins=False,export_attributes=False,export_morph=False)
# Preserve part ids for anatomy-driven texture classes without colliding with old parts.
if me.attributes.get('part'):
 for a in me.attributes['part'].data:a.value+=100
head.select_set(True);body.select_set(True);bpy.context.view_layer.objects.active=body;bpy.ops.object.join()
newslot=next(i for i,m in enumerate(body.data.materials) if m.name=='DrakeHeadNew')
for f in body.data.polygons:
 if f.material_index==newslot:f.material_index=1
while len(body.data.materials)>4:body.data.materials.pop(index=len(body.data.materials)-1)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/graft_uv.blend'));print('GRAFT',len(body.data.polygons),'faces, neck holes repaired',fixed)
