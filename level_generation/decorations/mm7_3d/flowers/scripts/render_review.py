"""Blender Eevee review renders of work/<id>/plant.blend (sun + sky, alpha clip, Standard view, base colour x COLOR_0,
specular scaled by openyamm_specular as in the engine; orthographic at a fixed metres-per-pixel per species so the
sheet can match the sprite's scale): review/<id>_<mesh>_<view>.png, views front (8 degrees up), three_quarter
(40 degrees round, 30 up) and top for LOD0, front for every LOD. Usage: -- <id> [resolution]"""
import bpy, math, os, sys
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import HERE, dims
args = sys.argv[sys.argv.index('--') + 1:]
SID = args[0]
res = int(args[1]) if len(args) > 1 else 768
W, H = dims(SID)
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', SID, 'plant.blend'))
sc = bpy.context.scene
if os.environ.get('FLOWERS_CPU'):   # other sessions hold the GPU: Cycles on the CPU instead of Eevee
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = 24
    sc.cycles.max_bounces = 1          # closer to the Eevee look the grading was measured with (darker otherwise)
else:
    for engine in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
        try:
            sc.render.engine = engine
            break
        except TypeError:
            continue
sc.view_settings.view_transform = 'Standard'
sc.render.film_transparent = True
sc.render.resolution_x = sc.render.resolution_y = res
world = sc.world or bpy.data.worlds.new('W')
sc.world = world
world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
bg.inputs['Color'].default_value = (0.55, 0.6, 0.68, 1)
bg.inputs['Strength'].default_value = 0.5
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN'))
sc.collection.objects.link(sun)
sun.data.energy = 3.6
sun.data.color = (1.0, 0.95, 0.86)
sun.rotation_euler = (math.radians(40), 0, math.radians(-35))
for m in bpy.data.materials:
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    tex = bsdf.inputs['Base Color'].links[0].from_node
    attr = nt.nodes.new('ShaderNodeAttribute'); attr.attribute_type = 'GEOMETRY'; attr.attribute_name = 'Color'
    mul = nt.nodes.new('ShaderNodeVectorMath'); mul.operation = 'MULTIPLY'
    nt.links.new(tex.outputs['Color'], mul.inputs[0]); nt.links.new(attr.outputs['Color'], mul.inputs[1])
    nt.links.new(mul.outputs[0], bsdf.inputs['Base Color'])
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
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.type = 'ORTHO'
cam.data.ortho_scale = max(W, H) * 1.25
lods = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('Plant')]
views = {'front': (0.0, 8.0), 'three_quarter': (40.0, 30.0), 'top': (0.0, 89.0)}
for o in lods:
    for x in lods:
        x.hide_render = x is not o
    for view, (yaw, pitch) in views.items():
        if o.name != 'Plant' and view != 'front':
            continue
        d = 10.0
        target = Vector((0, 0, H * 0.5 if view != 'top' else 0.0))
        cam.location = target + Vector((math.sin(math.radians(yaw)) * d * math.cos(math.radians(pitch)),
                                        -math.cos(math.radians(yaw)) * d * math.cos(math.radians(pitch)),
                                        d * math.sin(math.radians(pitch))))
        cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(HERE, 'review', f'{SID}_{o.name}_{view}.png')
        bpy.ops.render.render(write_still=True)
        print('RENDERED', sc.render.filepath)
