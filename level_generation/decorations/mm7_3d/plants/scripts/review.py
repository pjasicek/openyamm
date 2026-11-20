"""Adapted from the MM6 succulents' review.py. Blender Eevee review renders of work/<id>.blend (orthographic, sun + sky, Standard view): base colour x COLOR_0,
cut-outs clipped at 0.5, and the specular term scaled by openyamm_specular as the engine does (a specular-free copy
mixed with the full shader). Writes review/<id>/lod0_{front,three_quarter,side}.png and level<N>.png (every LOD from
the three-quarter view at the same scale). With --final, renders LOD0 of the finished work/mm7_deco_<id>.glb (linked,
cards cut) instead, as review/<id>/final_front.png. Usage: blender --background --python review.py -- <id> [resolution]
[--final]"""
import bpy, math, os, sys
from mathutils import Vector
args = sys.argv[sys.argv.index('--') + 1:]
FINAL = '--final' in args; CPU = '--cpu' in args; args = [a for a in args if a not in ('--final', '--cpu')]
SID = args[0]; res = int(args[1]) if len(args) > 1 else 640
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, 'review', SID); os.makedirs(OUT, exist_ok=True)
if FINAL:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'work', f'mm7_deco_{SID}.glb'))
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.data.color_attributes:
            o.data.color_attributes[0].name = 'Color'
else:
    bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', f'{SID}.blend'))
sc = bpy.context.scene
for engine in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
    try:
        sc.render.engine = engine; break
    except TypeError:
        continue
sc.eevee.taa_render_samples = 32
if CPU:                                   # GPU short of memory: Cycles on the CPU
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 32
sc.view_settings.view_transform = 'Standard'; sc.render.film_transparent = True
sc.render.resolution_x = sc.render.resolution_y = res
world = sc.world or bpy.data.worlds.new('W'); sc.world = world; world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
bg.inputs['Color'].default_value = (0.55, 0.6, 0.68, 1); bg.inputs['Strength'].default_value = 0.6
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 3.4; sun.data.color = (1.0, 0.95, 0.86); sun.data.angle = math.radians(3)
sun.rotation_euler = (math.radians(42), 0, math.radians(-30))
for m in bpy.data.materials:
    if not m.node_tree:
        continue
    nt = m.node_tree; bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    tex = next(n for n in nt.nodes if n.type == 'TEX_IMAGE' and n.image and 'basecolor' in n.image.name.lower()
               or n.type == 'TEX_IMAGE' and n.outputs['Color'].links and not n.image.colorspace_settings.is_data)
    attr = nt.nodes.new('ShaderNodeAttribute'); attr.attribute_type = 'GEOMETRY'; attr.attribute_name = 'Color'
    mul = nt.nodes.new('ShaderNodeVectorMath'); mul.operation = 'MULTIPLY'
    nt.links.new(tex.outputs['Color'], mul.inputs[0]); nt.links.new(attr.outputs['Color'], mul.inputs[1])
    nt.links.new(mul.outputs[0], bsdf.inputs['Base Color'])
    if bsdf.inputs['Alpha'].links or (FINAL and m.blend_method != 'OPAQUE' if hasattr(m, 'blend_method') else False):
        clip = nt.nodes.new('ShaderNodeMath'); clip.operation = 'GREATER_THAN'; clip.inputs[1].default_value = 0.5
        nt.links.new(tex.outputs['Alpha'], clip.inputs[0]); nt.links.new(clip.outputs[0], bsdf.inputs['Alpha'])
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
lods = sorted([o for o in bpy.data.objects if o.type == 'MESH'], key=lambda o: (len(o.name), o.name))
pts = [o.matrix_world @ Vector(c) for o in lods for c in o.bound_box]
H = max(p.z for p in pts); W = max(max(abs(p.x), abs(p.y)) for p in pts)
cam.data.ortho_scale = max(2.15 * W, 1.12 * H)


def shoot(obj, yaw, pitch, path):
    for x in lods:
        x.hide_render = x is not obj
    d = 20.0
    cam.location = (math.sin(math.radians(yaw)) * d * math.cos(math.radians(pitch)),
                    -math.cos(math.radians(yaw)) * d * math.cos(math.radians(pitch)),
                    H * 0.45 + d * math.sin(math.radians(pitch)))
    cam.rotation_euler = (Vector((0, 0, H * 0.45)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


if FINAL:
    shoot(lods[0], 0, 6, os.path.join(OUT, 'final_front.png'))
else:
    for view, (yaw, pitch) in {'front': (0, 6), 'three_quarter': (40, 22), 'side': (90, 6)}.items():
        shoot(lods[0], yaw, pitch, os.path.join(OUT, f'lod0_{view}.png'))
    for level, obj in enumerate(lods):
        shoot(obj, 0, 6, os.path.join(OUT, f'level{level}.png'))
print('REVIEW', OUT, [o.name for o in lods])
