"""Skinned geometry of the retextured master for swap_lod0.py: one UV layer (body faces from UVMap, head faces from
HeadUV), material slots Peasant_A / PeasantHead_A by the `head` face attribute, node `Peasant`, 4 influences, no
clips. Out: work/cand_export.glb."""
import bpy, os
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'master_r45.blend'))
rig = bpy.data.objects['Rig']; rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
body = bpy.data.objects['Body']; me = body.data
head = [a.value for a in me.attributes['head'].data]
uv, huv = me.uv_layers['UVMap'].data, me.uv_layers['HeadUV'].data
for p in me.polygons:
    if head[p.index]:
        for li in p.loop_indices:
            uv[li].uv = huv[li].uv
me.uv_layers.remove(me.uv_layers['HeadUV'])
if 'UVMeshy' in me.uv_layers: me.uv_layers.remove(me.uv_layers['UVMeshy'])
me.uv_layers.active = me.uv_layers['UVMap']
me.materials.clear()
for old in list(bpy.data.materials):
    old.name = 'Old_' + old.name
for name in ('Peasant_A', 'PeasantHead_A'):
    m = bpy.data.materials.new(name); m.use_nodes = True; me.materials.append(m)
me.polygons.foreach_set('material_index', head)
for name in [a.name for a in me.attributes if a.name in ('head', 'piece')]:
    me.attributes.remove(me.attributes[name])
body.name = 'Peasant'
bpy.ops.object.select_all(action='DESELECT'); body.select_set(True); rig.select_set(True); bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'work', 'cand_export.glb'), use_selection=True, export_format='GLB',
                          export_yup=True, export_animations=False, export_skins=True, export_all_influences=False,
                          export_attributes=False, export_morph=False, export_image_format='NONE')
print('EXPORTED', sum(len(p.vertices) - 2 for p in me.polygons), 'head faces', sum(head))
