"""Lit full-body render (front, three-quarter); was: lit close-up of the face (rest pose) with both texture sets, for the face/eye review. Args: -- <blend> <out png>"""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
blend, out = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; b = bpy.data.objects['Body']; me = b.data
rig.animation_data_create(); rig.animation_data.action = None
import numpy as np
hd = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hd)
def mat(name, png, uv):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(png)
    u = nt.nodes.new('ShaderNodeUVMap'); u.uv_map = uv
    nt.links.new(u.outputs['UV'], t.inputs['Vector']); nt.links.new(t.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.7
    return m
me.materials.clear()
me.materials.append(mat('B', os.path.join(HERE, 'textures', 'dru1_basecolor_1k.png'), 'UVMap'))
me.materials.append(mat('H', os.path.join(HERE, 'textures', 'dru1_head_basecolor_1k.png'), 'HeadUV'))
me.polygons.foreach_set('material_index', hd.tolist())
scene = common.setup_render((800, 800))
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); scene.collection.objects.link(sun)
sun.rotation_euler = (0.9, 0.2, 0.3); sun.data.energy = 3.0
scene.world.color = (0.5, 0.5, 0.5)
common.render_views(out[:-4], 1.0, 0.9, views=('front',), resolution=(700, 700))
