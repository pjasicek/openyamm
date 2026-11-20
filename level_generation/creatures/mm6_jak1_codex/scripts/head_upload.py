import bpy,bmesh,json,math
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/production_body.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];me=body.data;rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
pv=[x.value for x in me.attributes['piece'].data];head=[int(pv[p.vertices[0]]==2 or (pv[p.vertices[0]]==0 and min(me.vertices[i].co.z for i in p.vertices)>1.495))for p in me.polygons];me.attributes['head'].data.foreach_set('value',head);me.uv_layers.new(name='HeadUV');me.uv_layers.active=me.uv_layers['HeadUV']
for o in bpy.data.objects:o.select_set(o==body)
bpy.context.view_layer.objects.active=body;bpy.ops.object.mode_set(mode='EDIT');bm=bmesh.from_edit_mesh(me);bm.faces.ensure_lookup_table()
for f in bm.faces:f.select=bool(head[f.index])
bmesh.update_edit_mesh(me);bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.008);bpy.ops.uv.pack_islands(margin=.008,rotate=True);bpy.ops.object.mode_set(mode='OBJECT');bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/head_uv_master.blend'))
ob=bpy.data.objects.new('JackalmanHeadUpload',me.copy());bpy.context.collection.objects.link(ob);bm=bmesh.new();bm.from_mesh(ob.data);bm.faces.ensure_lookup_table();bmesh.ops.delete(bm,geom=[f for f in bm.faces if not head[f.index]],context='FACES');bm.to_mesh(ob.data);bm.free()
for uv in list(ob.data.uv_layers):
 if uv.name!='HeadUV':ob.data.uv_layers.remove(uv)
ob.data.uv_layers['HeadUV'].name='UVMap';ob.data.materials.clear()
for o in bpy.data.objects:o.select_set(o==ob)
bpy.context.view_layer.objects.active=ob;bpy.ops.export_scene.gltf(filepath=str(P/'work/head_retexture.glb'),use_selection=True,export_format='GLB',export_skins=False,export_animations=False,export_attributes=False,export_materials='NONE')
(P/'work/head_split.json').write_text(json.dumps({'faces':sum(head),'total_faces':len(head),'selection':'Skin above z=1.495m plus the entire headcloth; neck seam lies beneath the cheek cloth.'},indent=2));print('HEAD',sum(head),'of',len(head),flush=True)
