"""Blender Eevee review renders of a desert plant: base colour x COLOR_0, alpha clip 0.5, specular scaled by
openyamm_specular as in the engine, sun + sky, Standard view, orthographic camera framed on LOD0 so every level
renders at the same scale. Writes <out_prefix>_<object>_<view>.png. A billboard impostor is turned to face the
camera. Usage: -- <blend> <out_prefix> <resolution> <views: front,three_quarter,back,top> [objects,...] [noshadow]"""
import bpy, math, os, sys
from mathutils import Vector
args = sys.argv[sys.argv.index('--') + 1:]
blend, prefix, res, views = args[0], args[1], int(args[2]), args[3].split(',')
only = args[4].split(',') if len(args) > 4 and args[4] != 'all' else None
noshadow = 'noshadow' in args
bpy.ops.wm.open_mainfile(filepath=blend)
sc = bpy.context.scene
for engine in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
    try:
        sc.render.engine = engine; break
    except TypeError:
        continue
sc.eevee.taa_render_samples = 32
sc.view_settings.view_transform = 'Standard'; sc.render.film_transparent = True
world = sc.world or bpy.data.worlds.new('W'); sc.world = world; world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
bg.inputs['Color'].default_value = (0.55, 0.6, 0.68, 1); bg.inputs['Strength'].default_value = 0.55
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 3.6; sun.data.color = (1.0, 0.95, 0.86); sun.rotation_euler = (math.radians(40), 0, math.radians(-35))
sun.data.angle = math.radians(2)
if noshadow:
    sun.data.use_shadow = False
for m in bpy.data.materials:
    if not m.use_nodes:
        continue
    nt = m.node_tree; bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bsdf is None or not bsdf.inputs['Base Color'].links:
        continue
    tex = bsdf.inputs['Base Color'].links[0].from_node
    attr = nt.nodes.new('ShaderNodeAttribute'); attr.attribute_type = 'GEOMETRY'; attr.attribute_name = 'Color'
    mul = nt.nodes.new('ShaderNodeVectorMath'); mul.operation = 'MULTIPLY'
    nt.links.new(tex.outputs['Color'], mul.inputs[0]); nt.links.new(attr.outputs['Color'], mul.inputs[1])
    nt.links.new(mul.outputs[0], bsdf.inputs['Base Color'])
    if bsdf.inputs['Alpha'].links:
        clip = nt.nodes.new('ShaderNodeMath'); clip.operation = 'GREATER_THAN'; clip.inputs[1].default_value = 0.5
        nt.links.new(tex.outputs['Alpha'], clip.inputs[0]); nt.links.new(clip.outputs[0], bsdf.inputs['Alpha'])
    m.surface_render_method = 'DITHERED'
    spec = m.get('openyamm_specular', 1.0)
    plain = nt.nodes.new('ShaderNodeBsdfPrincipled'); plain.inputs['Specular IOR Level'].default_value = 0.0
    for name in ('Base Color', 'Alpha', 'Normal'):
        if bsdf.inputs[name].links:
            nt.links.new(bsdf.inputs[name].links[0].from_socket, plain.inputs[name])
    for name in ('Roughness', 'Metallic'):
        plain.inputs[name].default_value = bsdf.inputs[name].default_value
    bsdf.inputs['Specular IOR Level'].default_value = 0.5
    mix = nt.nodes.new('ShaderNodeMixShader'); mix.inputs['Fac'].default_value = spec
    out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
    nt.links.new(plain.outputs['BSDF'], mix.inputs[1]); nt.links.new(bsdf.outputs['BSDF'], mix.inputs[2])
    nt.links.new(mix.outputs['Shader'], out.inputs['Surface'])
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'
lods = sorted([o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('Plant')], key=lambda o: o.name)
base = bpy.data.objects['Plant']
pts = [base.matrix_world @ Vector(c) for c in base.bound_box]
Hm = max(p.z for p in pts)
Wm = max(max(abs(p.x), abs(p.y)) for p in pts)
cam.data.ortho_scale = max(2.15 * Wm, 1.12 * Hm)
sc.render.resolution_x = sc.render.resolution_y = res
VIEWS = {'front': (0.0, 6.0), 'three_quarter': (40.0, 25.0), 'back': (180.0, 6.0), 'top': (0.0, 60.0)}
targets = [o for o in lods if only is None or o.name in only]
for o in targets:
    for x in lods:
        x.hide_render = x is not o
    for view in views:
        yaw, pitch = VIEWS[view]
        d = 30.0
        cam.location = (math.sin(math.radians(yaw)) * d * math.cos(math.radians(pitch)),
                        -math.cos(math.radians(yaw)) * d * math.cos(math.radians(pitch)),
                        Hm * 0.5 + d * math.sin(math.radians(pitch)))
        cam.rotation_euler = (Vector((0, 0, Hm * 0.5)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
        if o.name.endswith('LOD3'):
            o.rotation_euler = (0, 0, math.radians(yaw))
        sc.render.filepath = f'{prefix}_{o.name}_{view}.png'
        bpy.ops.render.render(write_still=True)
        print('RENDERED', sc.render.filepath)
