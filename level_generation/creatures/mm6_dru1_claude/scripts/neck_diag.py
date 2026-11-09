"""Which map makes the skin patches (review 2)? Lit EEVEE chest/face close-ups with: base only, base + normal map,
base + normal + roughness. Args: -- <blend> <out prefix>"""
import bpy, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
blend, out = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(HERE, 'textures')
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; b = bpy.data.objects['Body']; me = b.data
rig.animation_data_create(); rig.animation_data.action = None
hd = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hd)


def mat(name, pre, uv, use_n, use_r):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    u = nt.nodes.new('ShaderNodeUVMap'); u.uv_map = uv

    def tex(f, cs):
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(os.path.join(T, f)); t.image.colorspace_settings.name = cs
        nt.links.new(u.outputs['UV'], t.inputs['Vector']); return t
    nt.links.new(tex(pre + '_basecolor_1k.png', 'sRGB').outputs['Color'], bsdf.inputs['Base Color'])
    if use_n:
        nm = nt.nodes.new('ShaderNodeNormalMap'); nm.uv_map = uv
        nt.links.new(tex(pre + '_normal_1k.png', 'Non-Color').outputs['Color'], nm.inputs['Color'])
        nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    if use_r:
        sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(tex(pre + '_metal_rough_1k.png', 'Non-Color').outputs['Color'], sep.inputs['Color'])
        nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness'])
    else:
        bsdf.inputs['Roughness'].default_value = 0.6
    return m


scene = common.setup_render((700, 700))
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); scene.collection.objects.link(sun)
sun.rotation_euler = (0.9, 0.2, 0.3); sun.data.energy = 3.0
for tag, n_, r_ in (('base', False, False), ('normal', True, False), ('full', True, True)):
    me.materials.clear()
    me.materials.append(mat('B', 'dru1', 'UVMap', n_, r_)); me.materials.append(mat('H', 'dru1_head', 'HeadUV', n_, r_))
    me.polygons.foreach_set('material_index', hd.tolist())
    common.render_views(f'{out}_{tag}', 1.43, 0.22, views=('front', 'three_quarter'), resolution=(700, 700)) if tag in ('full', 'base') else None
