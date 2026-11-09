"""Textured static export of the master for clips_mm9.py: three materials (SkelWar body set, SkelWarHead head set, Scimitar),
head faces take HeadUV, smooth normals, the armature lifted so model y = 0 is the floor. Args: <blend> <out glb>"""
import bpy, sys, os
import numpy as np
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=IN)
TX = bpy.path.abspath('//../textures')
body = bpy.data.objects['Body']; rig = body.parent; me = body.data
if rig.animation_data: rig.animation_data.action = None
for a in list(bpy.data.actions): bpy.data.actions.remove(a)
for b in rig.pose.bones: b.matrix_basis.identity()
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o is not body: bpy.data.objects.remove(o)
nf = len(me.polygons)
hd = np.zeros(nf, np.int32); sc = np.zeros(nf, np.int32)
me.attributes['head'].data.foreach_get('value', hd); me.attributes['scim'].data.foreach_get('value', sc)
huv, buv = me.uv_layers['HeadUV'].data, me.uv_layers['UVMap'].data
for p in me.polygons:
    if hd[p.index]:
        for li in p.loop_indices: buv[li].uv = huv[li].uv
me.uv_layers.active = me.uv_layers['UVMap']
me.uv_layers.remove(me.uv_layers['HeadUV'])


def material(name, base, normal=None, mr=None, rough=None, metal=None):
    mat = bpy.data.materials.new(name); mat.use_nodes = True; mat.use_backface_culling = True
    nt = mat.node_tree; bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')

    def tex(fname, cs):
        img = bpy.data.images.load(os.path.join(TX, fname), check_existing=True); img.colorspace_settings.name = cs
        n = nt.nodes.new('ShaderNodeTexImage'); n.image = img; return n
    nt.links.new(tex(base, 'sRGB').outputs['Color'], bsdf.inputs['Base Color'])
    if normal:
        nmap = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(tex(normal, 'Non-Color').outputs['Color'], nmap.inputs['Color'])
        nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
    if mr:
        sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(tex(mr, 'Non-Color').outputs['Color'], sep.inputs['Color'])
        nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness']); nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
    else:
        bsdf.inputs['Roughness'].default_value = rough; bsdf.inputs['Metallic'].default_value = metal
    return mat


me.materials.clear()
me.materials.append(material('SkelWar', 'skelwar_basecolor_final.png', 'skelwar_normal_1k.png', 'skelwar_metal_rough_1k.png'))
me.materials.append(material('SkelWarHead', 'skelwar_head_basecolor_final.png', 'skelwar_head_normal_1k.png', 'skelwar_head_metal_rough_1k.png'))
me.materials.append(material('Scimitar', 'skelwar_scimitar_basecolor.png', rough=0.4, metal=0.0))
me.polygons.foreach_set('material_index', (hd + 2 * sc).tolist())
for a in [a.name for a in me.attributes if a.name in ('head', 'hand', 'scim', 'lining', 'pid', 'fitco')]:
    me.attributes.remove(me.attributes[a])
bpy.context.view_layer.objects.active = body
for o in bpy.data.objects: o.select_set(o == body)
bpy.ops.object.shade_smooth()
lift = -min((body.matrix_world @ v.co).z for v in me.vertices)
rig.location.z += lift
bpy.context.view_layer.update()
print('LIFT', round(lift, 4))
body.name = 'SkelWar'; me.name = 'SkelWar'
for o in bpy.data.objects: o.select_set(o in (body, rig))
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', use_selection=True, export_animations=False, export_skins=True,
                          export_yup=True, export_image_format='AUTO', export_attributes=False)
print('EXPORTED', OUT, len(me.polygons))
