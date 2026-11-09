import bpy,bmesh,json,math
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_uv.blend'));body=bpy.data.objects['Body'];me=body.data;sc=bpy.context.scene
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
me.uv_layers.active=me.uv_layers['UVMap'];sc.tool_settings.mesh_select_mode=(False,False,True)
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='DESELECT');bpy.ops.object.mode_set(mode='OBJECT')
for f in me.polygons:f.select=f.material_index==1
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.hide(unselected=True);bpy.ops.uv.smart_project(angle_limit=math.radians(20),island_margin=.002,area_weight=0,correct_aspect=True,scale_to_bounds=True);bpy.ops.uv.pack_islands(rotate=True,margin=.002,margin_method='FRACTION',shape_method='CONVEX');bpy.ops.mesh.reveal(select=False);bpy.ops.object.mode_set(mode='OBJECT')
uv=me.uv_layers['UVMap'];me.calc_loop_triangles();tri=np.array([t.vertices[:] for t in me.loop_triangles]);coords=np.array([v.co[:] for v in me.vertices]);u=np.array([[uv.data[i].uv[:] for i in t.loops] for t in me.loop_triangles]);slots=np.array([t.material_index for t in me.loop_triangles]);np.savez(P/'work/uv_geometry.npz',co=coords,tri=tri,uv=u,slots=slots)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/anim_uv.blend'))
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
