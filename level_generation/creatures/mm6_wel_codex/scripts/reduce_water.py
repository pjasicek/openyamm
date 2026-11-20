"""Protect face and digits while reducing the weighted, bent body; freeze separate head UVs."""
import bpy,bmesh,json,math
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_foam.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];sc=bpy.context.scene
rig.animation_data.action=bpy.data.actions['Attack'];sc.frame_set(40);me=body.data;rest=np.array([v.co[:] for v in me.vertices]);pa=np.array([v.value for v in me.attributes['part'].data]);att=me.attributes.new('rest_co','FLOAT_VECTOR','POINT');att.data.foreach_set('vector',rest.ravel());before=len(me.polygons)
me.materials.clear()
for name in ['WaterBody_A','WaterHead_A']:
 m=bpy.data.materials.new(name);m.use_nodes=True;me.materials.append(m)
headvertex=np.isin(pa,[2,4,7,12,14])|((pa==0)&(rest[:,2]>1.745))
for f in me.polygons:f.material_index=int(all(headvertex[v] for v in f.vertices))
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body;bpy.ops.object.modifier_apply(modifier='WaterSkin');protect=body.vertex_groups.new(name='KeepDetail');protect.add(np.where(headvertex|np.isin(pa,[1,6]))[0].tolist(),1,'REPLACE');mod=body.modifiers.new('BentReduction','DECIMATE');mod.ratio=.86;mod.vertex_group=protect.name;mod.invert_vertex_group=True;mod.vertex_group_factor=1000;mod.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=mod.name)
me=body.data;rc=np.empty(len(me.vertices)*3);me.attributes['rest_co'].data.foreach_get('vector',rc);me.vertices.foreach_set('co',rc);me.attributes.remove(me.attributes['rest_co']);body.vertex_groups.remove(body.vertex_groups['KeepDetail']);me.update();rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
mod=body.modifiers.new('WaterSkin','ARMATURE');mod.object=rig;bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
for v in me.vertices:
 gs=sorted(v.groups,key=lambda g:g.weight,reverse=True)
 for g in gs[4:]:body.vertex_groups[g.group].remove([v.index])
 total=sum(g.weight for g in v.groups);assert total>.8
 for g in list(v.groups):body.vertex_groups[g.group].add([v.index],g.weight/total,'REPLACE')
for f in me.polygons:f.use_smooth=True
if not me.uv_layers:me.uv_layers.new(name='UVMap')
while len(me.uv_layers)>1:me.uv_layers.remove(me.uv_layers[-1])
for slot in [0,1]:
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_mode(type='FACE');bpy.ops.mesh.select_all(action='DESELECT');bm=bmesh.from_edit_mesh(me)
 for f in bm.faces:f.select_set(f.material_index==slot)
 bmesh.update_edit_mesh(me);bpy.ops.uv.smart_project(angle_limit=math.radians(45),island_margin=.007,area_weight=0.,scale_to_bounds=False);bpy.ops.uv.pack_islands(margin=.006,rotate=True,shape_method='CONCAVE');bpy.ops.object.mode_set(mode='OBJECT')
me.calc_loop_triangles();assert len(me.loop_triangles)<before;stats={'original_triangles':before,'reduced_triangles':len(me.loop_triangles),'head_faces':sum(f.material_index==1 for f in me.polygons),'protected':'head including hair/beard/crown and both complete hands','bend_clip':'Attack','bend_frame':40};(P/'work/reduction.json').write_text(json.dumps(stats,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/anim_uv.blend'))
# The body job sees the complete silhouette; the head job receives only its own UV domain.
for label,head_only in [('body',False),('head',True)]:
 obj=body.copy();obj.data=me.copy();obj.parent=None;obj.modifiers.clear();obj.vertex_groups.clear();sc.collection.objects.link(obj)
 if head_only:
  bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index!=1],context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(obj.data);bm.free()
 obj.data.materials.clear();m=bpy.data.materials.new('Neutral_'+label);m.use_nodes=True;obj.data.materials.append(m)
 for f in obj.data.polygons:f.material_index=0
 bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj;bpy.ops.export_scene.gltf(filepath=str(P/'work'/f'{label}_upload.glb'),use_selection=True,export_format='GLB',export_animations=False,export_skins=False,export_attributes=False,export_morph=False);bpy.data.objects.remove(obj,do_unlink=True)
print('REDUCED',stats)
