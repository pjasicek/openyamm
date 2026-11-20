"""Textured static export of the rigged master for clips_mm9.py: body faces on the composed body maps, skull faces on the
skull set (HeadUV copied into the one UV layer), smooth normals, model y = 0 the floor. Args: blend out glb"""
import bpy, os, sys
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(HERE, 'textures')
bpy.ops.wm.open_mainfile(filepath=argv[0])
body = bpy.data.objects['Body']; rig = body.parent
if rig.animation_data:
    rig.animation_data.action = None
for a in list(bpy.data.actions):
    bpy.data.actions.remove(a)
for b in rig.pose.bones:
    b.matrix_basis.identity()
me = body.data
part = np.zeros(len(me.polygons), np.int32); me.attributes['part'].data.foreach_get('value', part)
sel = part == 30
huv, buv = me.uv_layers['HeadUV'].data, me.uv_layers['UVMap'].data
for p in me.polygons:
    if sel[p.index]:
        for li in p.loop_indices:
            buv[li].uv = huv[li].uv
me.uv_layers.active = me.uv_layers['UVMap']
me.uv_layers.remove(me.uv_layers['HeadUV'])


def material(name, base, normal, mr):
    mat = bpy.data.materials.new(name); mat.use_nodes = True; mat.use_backface_culling = True
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')

    def tex(fname, cs):
        img = bpy.data.images.load(os.path.join(T, fname), check_existing=True)
        img.colorspace_settings.name = cs
        n = nt.nodes.new('ShaderNodeTexImage'); n.image = img
        return n
    nt.links.new(tex(base, 'sRGB').outputs['Color'], bsdf.inputs['Base Color'])
    nmap = nt.nodes.new('ShaderNodeNormalMap')
    nt.links.new(tex(normal, 'Non-Color').outputs['Color'], nmap.inputs['Color'])
    nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
    sep = nt.nodes.new('ShaderNodeSeparateColor')
    nt.links.new(tex(mr, 'Non-Color').outputs['Color'], sep.inputs['Color'])
    nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness'])
    nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
    return mat


me.materials.clear()
me.materials.append(material('Lich', 'lich_basecolor_graded.png', 'lich_normal_1k.png', 'lich_metal_rough_1k.png'))
me.materials.append(material('LichHead', 'lich_head_basecolor_graded.png', 'lich_head_normal_1k.png', 'lich_head_metal_rough_1k.png'))
me.polygons.foreach_set('material_index', sel.astype(np.int32).tolist())
for at in ('part', 'fid'):
    if at in me.attributes:
        me.attributes.remove(me.attributes[at])
bpy.context.view_layer.objects.active = body
for o in bpy.data.objects:
    o.select_set(o == body)
bpy.ops.object.shade_smooth()
lift = -min((body.matrix_world @ v.co).z for v in me.vertices)
rig.location.z += lift
bpy.context.view_layer.update()
print('LIFT', round(lift, 4))
body.name = 'Lich'; me.name = 'Lich'
for o in bpy.data.objects:
    o.select_set(o in (body, rig))
bpy.ops.export_scene.gltf(filepath=argv[1], export_format='GLB', use_selection=True, export_animations=False,
                          export_skins=True, export_yup=True, export_image_format='AUTO', export_attributes=False)
print('EXPORTED', argv[1], len(me.polygons), int(sel.sum()))
