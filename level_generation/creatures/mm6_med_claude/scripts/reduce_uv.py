"""Reduce in a bent pose, carrying rest coordinates and fitted weights; unwrap body/head independently."""
import bpy,bmesh,json,math
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_v1.blend'))
body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];sc=bpy.context.scene
rig.animation_data.action=bpy.data.actions['Death'];sc.frame_set(33)
rest=np.array([v.co[:] for v in body.data.vertices]);pa=np.array([v.value for v in body.data.attributes['part'].data]);att=body.data.attributes.new('rest_co','FLOAT_VECTOR','POINT');att.data.foreach_set('vector',rest.ravel())
body.data.materials.clear()
for n in ['MedusaBody','MedusaHead']:
 m=bpy.data.materials.new(n);m.diffuse_color=(.48,.53,.48,1);body.data.materials.append(m)
for f in body.data.polygons:f.material_index=int(pa[f.vertices[0]]>=100)
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body;bpy.ops.object.modifier_apply(modifier='MedusaSkin')
protect=body.vertex_groups.new(name='KeepDetail');ids=np.where(np.isin(pa,[1,4,101,104,106,100,110,114,119,127,129,130,131,132]))[0];protect.add(ids.tolist(),1.,'REPLACE')
mod=body.modifiers.new('BentReduction','DECIMATE');mod.ratio=.63;mod.vertex_group=protect.name;mod.invert_vertex_group=True;mod.vertex_group_factor=1000.;mod.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=mod.name)
me=body.data;rc=np.empty(len(me.vertices)*3);me.attributes['rest_co'].data.foreach_get('vector',rc);me.vertices.foreach_set('co',rc);me.attributes.remove(me.attributes['rest_co']);body.vertex_groups.remove(body.vertex_groups['KeepDetail']);me.update()
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
mod=body.modifiers.new('MedusaSkin','ARMATURE');mod.object=rig
bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();me.update()
# Smart islands suit the disconnected scales/jewellery and do not collapse narrow finger strips.
for slot in [0,1]:
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='DESELECT');bpy.ops.object.mode_set(mode='OBJECT')
 for f in me.polygons:f.select=f.material_index==slot
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.uv.smart_project(angle_limit=math.radians(35),island_margin=.002,area_weight=0,correct_aspect=True,scale_to_bounds=True);bpy.ops.object.mode_set(mode='OBJECT')
 if slot==1:
  parts=np.array([v.value for v in me.attributes['part'].data]);uv=me.uv_layers.active
  for f in me.polygons:
   if parts[f.vertices[0]] in [101,104,106]:
    for loop in f.loop_indices:uv.data[loop].uv*=2.5
  bpy.ops.object.mode_set(mode='EDIT');bpy.ops.uv.pack_islands(rotate=True,margin=.003,margin_method='FRACTION',shape_method='CONCAVE');bpy.ops.object.mode_set(mode='OBJECT')
me.calc_loop_triangles();uv=me.uv_layers.active;stats={};areas=[]
for t in me.loop_triangles:
 a=np.array([me.vertices[i].co[:] for i in t.vertices]);u=np.array([uv.data[i].uv[:] for i in t.loops]);world=np.linalg.norm(np.cross(a[1]-a[0],a[2]-a[0]))*.5;ua=abs(np.linalg.det(np.column_stack([u[1]-u[0],u[2]-u[0]])))*.5;areas.append((t.material_index,world,ua))
for slot in [0,1]:
 ar=np.array([(w,u) for s,w,u in areas if s==slot]);good=ar[:,0]>1e-10;assert np.all(ar[good,1]>1e-12),'Collapsed UV triangle';stats[str(slot)]={'triangles':len(ar),'world_area':float(ar[:,0].sum()),'uv_area':float(ar[:,1].sum()),'density_p05_p50_p95':np.percentile(ar[good,1]/ar[good,0],[5,50,95]).tolist()}
for v in me.vertices:
 groups=sorted(v.groups,key=lambda g:g.weight,reverse=True)
 for g in groups[4:]:body.vertex_groups[g.group].remove([v.index])
 total=sum(g.weight for g in v.groups)
 assert total>.9
 for g in list(v.groups):body.vertex_groups[g.group].add([v.index],g.weight/total,'REPLACE')
for f in me.polygons:f.use_smooth=True
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/anim_uv.blend'))
# Meshy receives rest geometry, one material and one UV domain per job.
for slot,label in [(0,'body'),(1,'head')]:
 obj=body.copy();obj.data=body.data.copy();obj.name='Medusa_'+label;sc.collection.objects.link(obj);obj.parent=None;obj.modifiers.clear();obj.vertex_groups.clear();bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index!=slot],context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(obj.data);bm.free();mat=obj.data.materials[slot];obj.data.materials.clear();obj.data.materials.append(mat)
 for f in obj.data.polygons:f.material_index=0
 bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
 bpy.ops.export_scene.gltf(filepath=str(P/'texturing'/f'med_{label}_upload.glb'),use_selection=True,export_format='GLB',export_animations=False,export_skins=False,export_attributes=False,export_morph=False)
 bpy.data.objects.remove(obj,do_unlink=True)
(P/'work/uv_stats.json').write_text(json.dumps(stats,indent=2)+'\n');print('REDUCED_UV',json.dumps(stats))
