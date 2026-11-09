"""Blender Eevee review renders of work/<id>/plant.blend (sun + sky, alpha clip, Standard view, base colour x COLOR_0
and specular scaled by openyamm_specular as in the engine): review/<id>_<LOD>_<view>.png for views eye and three_quarter. Usage: -- <id> [resolution]"""
import bpy, math, os, sys
from mathutils import Vector
args = sys.argv[sys.argv.index('--') + 1:]
SID = args[0]; res = int(args[1]) if len(args) > 1 else 512
HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # the leftovers batch folder
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'plants', SID, 'plant.blend'))
sc = bpy.context.scene
os.makedirs(os.path.join(HERE, 'review', SID), exist_ok=True)
for engine in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
    try:
        sc.render.engine = engine; break
    except TypeError:
        continue
sc.view_settings.view_transform = 'Standard'; sc.render.film_transparent = True
sc.render.resolution_x = sc.render.resolution_y = res
world = sc.world or bpy.data.worlds.new('W'); sc.world = world; world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
bg.inputs['Color'].default_value = (0.55, 0.6, 0.68, 1); bg.inputs['Strength'].default_value = 0.5
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 3.6; sun.data.color = (1.0, 0.95, 0.86); sun.rotation_euler = (math.radians(40), 0, math.radians(-35))
for m in bpy.data.materials:
    nt = m.node_tree; bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    tex = bsdf.inputs['Base Color'].links[0].from_node
    attr = nt.nodes.new('ShaderNodeAttribute'); attr.attribute_type = 'GEOMETRY'; attr.attribute_name = 'Color'
    mul = nt.nodes.new('ShaderNodeVectorMath'); mul.operation = 'MULTIPLY'
    nt.links.new(tex.outputs['Color'], mul.inputs[0]); nt.links.new(attr.outputs['Color'], mul.inputs[1])
    nt.links.new(mul.outputs[0], bsdf.inputs['Base Color'])
    clip = nt.nodes.new('ShaderNodeMath'); clip.operation = 'GREATER_THAN'; clip.inputs[1].default_value = 0.5
    nt.links.new(tex.outputs['Alpha'], clip.inputs[0]); nt.links.new(clip.outputs[0], bsdf.inputs['Alpha'])
    # The engine scales the whole specular term (Fresnel included) by openyamm_specular; Eevee's IOR level only lowers
    # F0, so grazing cards would catch a near-full sky sheen. Mix a specular-free copy with the full shader instead.
    plain = nt.nodes.new('ShaderNodeBsdfPrincipled'); plain.inputs['Specular IOR Level'].default_value = 0.0
    for name in ('Base Color', 'Alpha', 'Normal'):
        if bsdf.inputs[name].links:
            nt.links.new(bsdf.inputs[name].links[0].from_socket, plain.inputs[name])
    for name in ('Roughness', 'Metallic'):
        plain.inputs[name].default_value = bsdf.inputs[name].default_value
    bsdf.inputs['Specular IOR Level'].default_value = 0.5
    mix = nt.nodes.new('ShaderNodeMixShader'); mix.inputs['Fac'].default_value = m.get('openyamm_specular', 1.0)
    out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
    nt.links.new(plain.outputs['BSDF'], mix.inputs[1]); nt.links.new(bsdf.outputs['BSDF'], mix.inputs[2])
    nt.links.new(mix.outputs['Shader'], out.inputs['Surface'])
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'
lods = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('Plant')]
H = max((o.matrix_world @ Vector(c)).z for o in lods for c in o.bound_box)
W = max(max(abs((o.matrix_world @ Vector(c)).x), abs((o.matrix_world @ Vector(c)).y)) for o in lods for c in o.bound_box)
cam.data.ortho_scale = max(2.2 * W, 1.25 * H)
for o in lods:
    for x in lods:
        x.hide_render = x is not o
    for view, (yaw, pitch) in {'eye': (0.0, 8.0), 'three_quarter': (40.0, 30.0)}.items():
        d = 3.0
        cam.location = (math.sin(math.radians(yaw)) * d * math.cos(math.radians(pitch)),
                        -math.cos(math.radians(yaw)) * d * math.cos(math.radians(pitch)),
                        H * 0.45 + d * math.sin(math.radians(pitch)))
        cam.rotation_euler = (Vector((0, 0, H * 0.45)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(HERE, 'review', SID, f'flower_{o.name}_{view}.png')
        bpy.ops.render.render(write_still=True)
        print('RENDERED', sc.render.filepath)
