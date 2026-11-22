"""Eevee close-ups of the single foot (sole, toes, ankle) with the base colour and the normal map (Meshy +y-down
convention, green inverted in the shader), and without the normal map: review/close_<view>_<n|flat>.png.
Args: -- [blend] (default foot_v2.blend)"""
import bpy, os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', a[0] if a else 'foot_v2.blend'))
ob = bpy.data.objects['Foot']; sc = bpy.context.scene
try:
    sc.render.engine = 'BLENDER_EEVEE_NEXT'
except TypeError:
    sc.render.engine = 'BLENDER_EEVEE'
T = os.path.join(HERE, 'textures')


def mat(use_normal):
    m = bpy.data.materials.new('m'); m.use_nodes = True; nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'); b.inputs['Roughness'].default_value = 0.7
    c = nt.nodes.new('ShaderNodeTexImage'); c.image = bpy.data.images.load(os.path.join(T, 'feet_basecolor_graded.png'))
    nt.links.new(c.outputs['Color'], b.inputs['Base Color'])
    if use_normal:
        n = nt.nodes.new('ShaderNodeTexImage'); n.image = bpy.data.images.load(os.path.join(T, 'feet_normal_1k.png'))
        n.image.colorspace_settings.name = 'Non-Color'
        sep = nt.nodes.new('ShaderNodeSeparateColor'); com = nt.nodes.new('ShaderNodeCombineColor')
        inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
        nt.links.new(n.outputs['Color'], sep.inputs['Color'])
        nt.links.new(sep.outputs['Red'], com.inputs['Red']); nt.links.new(sep.outputs['Blue'], com.inputs['Blue'])
        nt.links.new(sep.outputs['Green'], inv.inputs[1]); nt.links.new(inv.outputs[0], com.inputs['Green'])
        nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(com.outputs['Color'], nm.inputs['Color'])
        nt.links.new(nm.outputs['Normal'], b.inputs['Normal'])
    return m


if sc.world is None: sc.world = bpy.data.worlds.new('w')
sc.world.use_nodes = True
bg = next(n for n in sc.world.node_tree.nodes if n.type == 'BACKGROUND'); bg.inputs['Strength'].default_value = 0.4
sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = 3.0
so = bpy.data.objects.new('sun', sun); sc.collection.objects.link(so); so.rotation_euler = (math.radians(50), 0.3, 0.6)
VIEWS = {'sole': ((0.0, -0.02, -0.45), (0.0, -0.02, 0.02)), 'toes': ((0.12, -0.42, 0.2), (0.0, -0.11, 0.04)),
         'ankle': ((-0.35, 0.2, 0.25), (0.0, 0.06, 0.1))}
sc.render.resolution_x, sc.render.resolution_y = 700, 520
for key, use in (('n', True), ('flat', False)):
    ob.data.materials.clear(); ob.data.materials.append(mat(use))
    for v, (loc, tgt) in VIEWS.items():
        cd = bpy.data.cameras.new('c'); cd.lens = 50
        cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); cam.matrix_world = C.look(loc, tgt)
        sc.camera = cam
        sc.render.filepath = os.path.join(HERE, 'review', f'close_{v}_{key}.png')
        bpy.ops.render.render(write_still=True)
        bpy.data.objects.remove(cam, do_unlink=True)
print('CLOSEUPS done')
