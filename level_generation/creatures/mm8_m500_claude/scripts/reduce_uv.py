"""Reduce bent torso/tail while protecting face and claws; unwrap full body and a separate head set."""
import bpy,bmesh,json,math
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_v1.blend'))
body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];sc=bpy.context.scene
rig.animation_data.action=bpy.data.actions['Death'];sc.frame_set(10)
rest=np.array([v.co[:] for v in body.data.vertices]);att=body.data.attributes.new('rest_co','FLOAT_VECTOR','POINT');att.data.foreach_set('vector',rest.ravel())
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
bpy.ops.object.modifier_apply(modifier='SerpentSkin')
protect=body.vertex_groups.new(name='KeepDetail');ids=np.where((rest[:,2]>1.52)|((abs(rest[:,0])>.50)&(rest[:,2]<1.1))|((rest[:,1]>.15)&(rest[:,2]>.65)&(abs(rest[:,0])<.16))|((rest[:,1]>1.25)&(rest[:,2]>.65)))[0];protect.add(ids.tolist(),1.,'REPLACE')
mod=body.modifiers.new('BentReduction','DECIMATE');mod.ratio=.68;mod.vertex_group=protect.name;mod.invert_vertex_group=True;mod.vertex_group_factor=1000.;mod.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=mod.name)
me=body.data;rc=np.empty(len(me.vertices)*3);me.attributes['rest_co'].data.foreach_get('vector',rc);me.vertices.foreach_set('co',rc);me.attributes.remove(me.attributes['rest_co']);body.vertex_groups.remove(body.vertex_groups['KeepDetail']);me.update()
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
mod=body.modifiers.new('SerpentSkin','ARMATURE');mod.object=rig
bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();me.update()
body.data.materials.clear()
for n in ['WaterElementalBody','WaterElementalHead']:
 m=bpy.data.materials.new(n);m.diffuse_color=(.48,.53,.48,1);m.use_nodes=True;body.data.materials.append(m)
for f in me.polygons:f.material_index=0;f.use_smooth=True
# Retain a full-silhouette UV layout for the body texture job.
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(35),island_margin=.0015,area_weight=0,correct_aspect=True,scale_to_bounds=True);bpy.ops.uv.pack_islands(rotate=True,margin=.002,margin_method='FRACTION',shape_method='CONCAVE');bpy.ops.object.mode_set(mode='OBJECT')
me.uv_layers.active.name='UVMap';savedUV=[a.uv[:] for a in me.uv_layers['UVMap'].data]
me.uv_layers.new(name='BodyFull')
for a,b in zip(me.uv_layers['BodyFull'].data,savedUV):a.uv=b
uv=me.uv_layers['UVMap']
me.uv_layers.active=uv
sc.tool_settings.mesh_select_mode=(False,False,True)
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='DESELECT');bpy.ops.object.mode_set(mode='OBJECT')
for f in me.polygons:
 f.material_index=int(sum(me.vertices[i].co.z for i in f.vertices)/len(f.vertices)>1.54)
 f.select=f.material_index==1
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.hide(unselected=True);bpy.ops.uv.smart_project(angle_limit=math.radians(20),island_margin=.0015,area_weight=0,correct_aspect=True,scale_to_bounds=True);bpy.ops.uv.pack_islands(rotate=True,margin=.002,margin_method='FRACTION',shape_method='CONVEX');bpy.ops.mesh.reveal(select=False);bpy.ops.object.mode_set(mode='OBJECT')
for v in me.vertices:
 groups=sorted(v.groups,key=lambda g:g.weight,reverse=True)
 for g in groups[4:]:body.vertex_groups[g.group].remove([v.index])
 total=sum(g.weight for g in v.groups);assert total>.5
 for g in list(v.groups):body.vertex_groups[g.group].add([v.index],g.weight/total,'REPLACE')
me=body.data;uv=me.uv_layers['UVMap'];me.calc_loop_triangles();tri=np.array([t.vertices[:] for t in me.loop_triangles]);coords=np.array([v.co[:] for v in me.vertices]);u=np.array([[uv.data[i].uv[:] for i in t.loops] for t in me.loop_triangles]);slots=np.array([t.material_index for t in me.loop_triangles])
np.savez(P/'work/uv_geometry.npz',co=coords,tri=tri,uv=u,slots=slots)
report={'vertices':len(coords),'triangles':len(tri),'head_triangles':int(sum(slots==1)),'original_triangles':15527,'maximum_influences':max(len(v.groups) for v in me.vertices)}
assert len(tri)<14000 and len(tri)>9000,report
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/anim_uv.blend'))
(P/'texturing').mkdir(exist_ok=True)
for label in ['body','head']:
 obj=body.copy();obj.data=body.data.copy();obj.name='WaterElemental_'+label;sc.collection.objects.link(obj);obj.parent=None;obj.modifiers.clear();obj.vertex_groups.clear()
 if label=='body':
  for a,b in zip(obj.data.uv_layers['UVMap'].data,obj.data.uv_layers['BodyFull'].data):a.uv=b.uv
 else:
  bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index!=1],context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(obj.data);bm.free()
 obj.data.uv_layers.remove(obj.data.uv_layers['BodyFull']);obj.data.uv_layers.active=obj.data.uv_layers['UVMap'];obj.data.uv_layers.active.active_render=True
 mat=obj.data.materials[0];obj.data.materials.clear();obj.data.materials.append(mat)
 for f in obj.data.polygons:f.material_index=0
 bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
 bpy.ops.export_scene.gltf(filepath=str(P/'texturing'/f'm500_{label}_upload.glb'),use_selection=True,export_format='GLB',export_animations=False,export_skins=False,export_attributes=False,export_morph=False)
 bpy.data.objects.remove(obj,do_unlink=True)
(P/'work/reduction_uv.json').write_text(json.dumps(report,indent=2)+'\n');print('REDUCED',json.dumps(report))
