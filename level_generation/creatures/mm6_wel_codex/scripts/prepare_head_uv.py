import bpy,bmesh,math,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_uv.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];sc=bpy.context.scene;me=body.data;rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body;bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_mode(type='FACE');bpy.ops.mesh.select_all(action='DESELECT');bm=bmesh.from_edit_mesh(me)
for f in bm.faces:f.select_set(f.material_index==1)
bmesh.update_edit_mesh(me);bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=0.,area_weight=0.,scale_to_bounds=False);bpy.ops.object.mode_set(mode='OBJECT')
uv=me.uv_layers.active.data;parts=me.attributes['part'].data
for f in me.polygons:
 if f.material_index!=1:continue
 scale=1.9 if parts[f.vertices[0]].value in [0,12,14] else .8 if parts[f.vertices[0]].value==4 else 1
 for li in f.loop_indices:uv[li].uv*=scale
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.uv.pack_islands(margin=.0025,rotate=True,shape_method='CONCAVE');bpy.ops.object.mode_set(mode='OBJECT');bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/anim_uv.blend'))
# The body job sees the complete silhouette; the head job receives only its own UV domain.
for label,head_only in [('head',True)]:
 obj=body.copy();obj.data=me.copy();obj.parent=None;obj.modifiers.clear();obj.vertex_groups.clear();sc.collection.objects.link(obj)
 if head_only:
  bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index!=1],context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(obj.data);bm.free()
 obj.data.materials.clear();m=bpy.data.materials.new('Neutral_'+label);m.use_nodes=True;obj.data.materials.append(m)
 for f in obj.data.polygons:f.material_index=0
 bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj;bpy.ops.export_scene.gltf(filepath=str(P/'work'/f'{label}_upload.glb'),use_selection=True,export_format='GLB',export_animations=False,export_skins=False,export_attributes=False,export_morph=False);bpy.data.objects.remove(obj,do_unlink=True)

