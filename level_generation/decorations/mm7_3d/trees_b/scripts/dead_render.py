"""Eevee review renders of a dead-tree blend, as the living trees' render_review.py (sun + sky, Standard view,
base colour x COLOR_0 'Color', Specular IOR Level 0.15 on every material) but framed on the model's larger extent
(height or width), so wide models (the swamp tree, the stump) fit. Args: out_prefix blend views [res] [noshadow].
Views: eye, three_quarter, back, side."""
import bpy, sys, math
from mathutils import Vector
args = sys.argv[sys.argv.index('--') + 1:]
prefix, blend, views = args[0], args[1], args[2].split(',')
res = int(args[3]) if len(args) > 3 else 540
bpy.ops.wm.open_mainfile(filepath=blend)
sc = bpy.context.scene
for engine in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
    try:
        sc.render.engine = engine; break
    except TypeError:
        continue
sc.view_settings.view_transform = 'Standard'
sc.render.film_transparent = True
sc.render.resolution_y = res; sc.render.resolution_x = res
world = sc.world or bpy.data.worlds.new('W'); sc.world = world; world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
bg.inputs['Color'].default_value = (0.55, 0.6, 0.68, 1); bg.inputs['Strength'].default_value = 0.5
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 3.6; sun.data.color = (1.0, 0.95, 0.86)
sun.rotation_euler = (math.radians(40), 0, math.radians(-35))
if 'noshadow' in args:
    sun.data.use_shadow = False
    sc.eevee.use_shadows = False; sc.eevee.use_fast_gi = False; sc.eevee.use_raytracing = False
for m in bpy.data.materials:
    if not m.use_nodes:
        continue
    nt = m.node_tree; bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bsdf is None or not bsdf.inputs['Base Color'].links:
        continue
    tex = bsdf.inputs['Base Color'].links[0].from_node
    bsdf.inputs['Specular IOR Level'].default_value = 0.15
    attr = nt.nodes.new('ShaderNodeAttribute'); attr.attribute_type = 'GEOMETRY'; attr.attribute_name = 'Color'
    mul = nt.nodes.new('ShaderNodeVectorMath'); mul.operation = 'MULTIPLY'
    nt.links.new(tex.outputs['Color'], mul.inputs[0]); nt.links.new(attr.outputs['Color'], mul.inputs[1])
    nt.links.new(mul.outputs[0], bsdf.inputs['Base Color'])
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 50
lods = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('Tree')]
base = bpy.data.objects['Tree']
corners = [base.matrix_world @ Vector(c) for c in base.bound_box]
Hh = max(c.z for c in corners); Ww = 2 * max(max(abs(c.x), abs(c.y)) for c in corners)
extent = max(Hh, Ww * 0.9)
CAMS = {'eye': (0.0, 0.24), 'three_quarter': (45.0, 0.8), 'back': (180.0, 0.24), 'side': (90.0, 0.24)}
for o in lods:
    for x in lods:
        x.hide_render = x is not o
    for view in views:
        yaw, height = CAMS[view]
        d = extent * 1.65
        cam.location = (math.sin(math.radians(yaw)) * d, -math.cos(math.radians(yaw)) * d, height * extent)
        aim = Vector((0, 0, Hh * 0.5))
        cam.rotation_euler = (aim - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = f'{prefix}_{o.name}_{view}.png'
        bpy.ops.render.render(write_still=True)
