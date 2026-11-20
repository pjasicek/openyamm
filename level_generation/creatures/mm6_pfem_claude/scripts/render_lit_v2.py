"""Lit EEVEE renders of the textured Peasant (front/three-quarter/back) for a given skin. Args: skin tag action frame views."""
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
args = sys.argv[sys.argv.index('--') + 1:]
skin, tag = args[0], args[1]
action = args[2] if len(args) > 2 else 'Standing'; frame = float(args[3]) if len(args) > 3 else 1
views = args[4].split(',') if len(args) > 4 else ['front', 'three_quarter', 'back']
cz = float(args[5]) if len(args) > 5 else 0.8; hh = float(args[6]) if len(args) > 6 else 1.75
T = os.path.join(common.PROJECT, os.environ.get('TEXDIR', 'textures'))
mesh = bpy.data.objects['Peasant']
mat = bpy.data.materials.new('Lit'); mat.use_nodes = True; nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
def tex(name, cs):
    img = bpy.data.images.load(os.path.join(T, name)); img.colorspace_settings.name = cs
    n = nt.nodes.new('ShaderNodeTexImage'); n.image = img; return n
bc = tex(f'pfem_{skin}_basecolor.png', 'sRGB'); nt.links.new(bc.outputs['Color'], bsdf.inputs['Base Color'])
if os.environ.get('NONORMAL') != '1':
    nm = tex('pfem_normal.png', 'Non-Color'); nmap = nt.nodes.new('ShaderNodeNormalMap')
    nt.links.new(nm.outputs['Color'], nmap.inputs['Color']); nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
mr = tex('pfem_metal_rough.png', 'Non-Color'); sep = nt.nodes.new('ShaderNodeSeparateColor')
nt.links.new(mr.outputs['Color'], sep.inputs['Color'])
nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness']); nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
mesh.data.materials.clear(); mesh.data.materials.append(mat)
for o in bpy.data.objects:
    if o.type == 'MESH': o.hide_render = o.name != 'Peasant'
rig = bpy.data.objects['Peasant_Rig']; rig.animation_data.action = bpy.data.actions[action]
scene = bpy.context.scene
scene.frame_set(int(frame))
for engine in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
    try:
        scene.render.engine = engine; break
    except TypeError:
        pass
world = scene.world or bpy.data.worlds.new('W'); scene.world = world; world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND'); bg.inputs[0].default_value = (0.55, 0.6, 0.68, 1); bg.inputs[1].default_value = 0.8
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); scene.collection.objects.link(sun)
sun.data.energy = 3.5; sun.data.use_shadow = os.environ.get("SHADOW", "1") == "1"; sun.rotation_euler = (math.radians(50), 0, math.radians(-30))
scene.view_settings.view_transform = 'Standard'
common.render_views(os.path.join(common.REVIEW, tag), cz, hh, views=views, resolution=(600, 600))
