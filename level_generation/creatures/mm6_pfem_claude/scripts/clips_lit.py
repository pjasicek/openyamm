"""Lit textured playback sheet frames for every clip (EEVEE). Args: skin."""
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
skin = sys.argv[sys.argv.index('--') + 1]
T = os.path.join(common.PROJECT, 'textures')
mesh = bpy.data.objects['Peasant']
mat = bpy.data.materials.new('Lit'); mat.use_nodes = True; mat.use_backface_culling = False; nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
def tex(name, cs):
    img = bpy.data.images.load(os.path.join(T, name)); img.colorspace_settings.name = cs
    n = nt.nodes.new('ShaderNodeTexImage'); n.image = img; return n
bc = tex(f'pfem_{skin}_basecolor.png', 'sRGB'); nt.links.new(bc.outputs['Color'], bsdf.inputs['Base Color'])
nm = tex('pfem_normal_1k.png', 'Non-Color'); nmap = nt.nodes.new('ShaderNodeNormalMap')
nt.links.new(nm.outputs['Color'], nmap.inputs['Color']); nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
mr = tex('pfem_metal_rough_1k.png', 'Non-Color'); sep = nt.nodes.new('ShaderNodeSeparateColor')
nt.links.new(mr.outputs['Color'], sep.inputs['Color'])
nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness']); nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
mesh.data.materials.clear(); mesh.data.materials.append(mat)
for o in bpy.data.objects:
    if o.type == 'MESH': o.hide_render = o.name != 'Peasant'
scene = bpy.context.scene
for engine in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
    try:
        scene.render.engine = engine; break
    except TypeError:
        pass
world = scene.world or bpy.data.worlds.new('W'); scene.world = world; world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND'); bg.inputs[0].default_value = (0.55, 0.6, 0.68, 1); bg.inputs[1].default_value = 0.8
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); scene.collection.objects.link(sun)
sun.data.energy = 3.5; sun.rotation_euler = (math.radians(50), 0, math.radians(-30))
scene.view_settings.view_transform = 'Standard'
rig = bpy.data.objects['Peasant_Rig']
PLAN = {'Standing': ([1, 49], ['front', 'left']), 'Fidget': ([1, 7, 10, 13, 19], ['front']),
        'Walking': ([1, 4, 7, 10, 13, 16, 19, 22], ['left', 'front']),
        'Attack': ([1, 4, 7, 10, 13, 16, 19], ['front', 'three_quarter']),
        'Hit': ([1, 4, 7, 10, 13, 16, 19], ['front', 'left']),
        'Death': ([1, 4, 7, 10, 13, 16], ['front', 'three_quarter']), 'Dead': ([1, 13, 25], ['front', 'three_quarter'])}
for clip, (frames, views) in PLAN.items():
    rig.animation_data.action = bpy.data.actions[clip]
    for i, f in enumerate(frames):
        scene.frame_set(f)
        common.render_views(os.path.join(common.REVIEW, 'tmp', f'lit_{skin}_{clip}_{i:02d}'), 0.78, 1.75, views=views, resolution=(300, 300))
