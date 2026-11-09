"""Export the retained rig's whole body and a separately unwrapped head for the playbook's two texture sets."""
from pathlib import Path
import bpy,bmesh,math,json
P=Path(__file__).resolve().parents[1];(P/'texturing').mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v1.blend'))
body=bpy.data.objects['Body'];me=body.data;rig=bpy.data.objects['Rig'];me.uv_layers.new(name='UVMap')
head=me.attributes.new('head','INT','FACE');head_group=body.vertex_groups['Head'].index
for face in me.polygons:
    verts=[me.vertices[i]for i in face.vertices]
    is_head=all(v.co.z>2.15 for v in verts)or all(sum(g.weight for g in v.groups if g.group==head_group)>.99 for v in verts)
    head.data[face.index].value=int(is_head)
me.uv_layers.new(name='HeadUV');me.uv_layers.active=me.uv_layers['HeadUV']
for o in bpy.context.scene.objects:o.select_set(o==body)
bpy.context.view_layer.objects.active=body
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='DESELECT');bpy.ops.object.mode_set(mode='OBJECT')
for face in me.polygons:face.select=bool(head.data[face.index].value)
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.008,scale_to_bounds=False);bpy.ops.uv.pack_islands(margin=.008);bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_uv_v1.blend'))
for kind in ('body','head'):
    ob=body.copy();ob.data=me.copy();ob.parent=None;ob.modifiers.clear();ob.vertex_groups.clear();bpy.context.collection.objects.link(ob)
    if kind=='head':
        bm=bmesh.new();bm.from_mesh(ob.data);layer=bm.faces.layers.int['head'];bmesh.ops.delete(bm,geom=[f for f in bm.faces if not f[layer]],context='FACES');bm.to_mesh(ob.data);bm.free()
    uv='HeadUV'if kind=='head'else'UVMap'
    for layer in list(ob.data.uv_layers):
        if layer.name!=uv:ob.data.uv_layers.remove(layer)
    ob.data.materials.clear();mat=bpy.data.materials.new('Neutral');mat.use_nodes=True;ob.data.materials.append(mat)
    for f in ob.data.polygons:f.material_index=0
    for o in bpy.context.scene.objects:o.select_set(o==ob)
    bpy.context.view_layer.objects.active=ob
    bpy.ops.export_scene.gltf(filepath=str(P/'texturing'/f'centaur_{kind}_upload.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=False,export_skins=False,export_morph=False,export_attributes=False)
    print('UPLOAD',kind,len(ob.data.polygons));bpy.data.objects.remove(ob,do_unlink=True)
