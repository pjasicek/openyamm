"""Include the entire hair fan in the head set; avoid cutting the atlas boundary through the nape."""
import bpy,bmesh,math,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_master.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];me=body.data;rig.animation_data_clear()
for pb in rig.pose.bones:pb.matrix_basis.identity()
added=[]
for f in me.polygons:
 c=sum((me.vertices[i].co for i in f.vertices),Vector())/len(f.vertices)
 if f.material_index==0 and c.z>1.24 and c.y>.09 and abs(c.x+.01)<.18:f.material_index=1;added.append(f.index)
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body;bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='DESELECT');bpy.ops.object.mode_set(mode='OBJECT')
for f in me.polygons:f.select=f.material_index==1
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.uv.smart_project(angle_limit=math.radians(50),island_margin=.004,area_weight=0,correct_aspect=True,scale_to_bounds=True);bpy.ops.uv.pack_islands(rotate=True,margin=.004,margin_method='FRACTION');bpy.ops.object.mode_set(mode='OBJECT')
if 'head' not in me.attributes:me.attributes.new('head','INT','FACE')
me.attributes['head'].data.foreach_set('value',[int(f.material_index==1) for f in me.polygons])
for a in bpy.data.actions:a.use_fake_user=True
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_master.blend'))
obj=body.copy();obj.data=me.copy();obj.parent=None;obj.modifiers.clear();obj.vertex_groups.clear();bpy.context.collection.objects.link(obj);bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index!=1],context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(obj.data);bm.free();obj.data.materials.clear();m=bpy.data.materials.new('Neutral');m.use_nodes=True;obj.data.materials.append(m)
for f in obj.data.polygons:f.material_index=0
bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
bpy.ops.export_scene.gltf(filepath=str(P/'texturing/hrp_head_upload_v2.glb'),use_selection=True,export_format='GLB',export_animations=False,export_skins=False,export_attributes=False,export_morph=False)
(P/'work/head_domain_v2.json').write_text(json.dumps({'added_faces':len(added),'head_faces':len(obj.data.polygons),'reason':'Complete nape and hair fan in one continuous texture domain'},indent=2));print('HEAD DOMAIN',len(added),'added',len(obj.data.polygons),'total',flush=True)
