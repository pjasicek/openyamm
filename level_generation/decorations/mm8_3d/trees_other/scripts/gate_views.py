"""Black-patch gate views of Tree and Tree_LOD1 (Eevee, sun + sky, base colour x COLOR_0, alpha-clipped cards,
back faces culled on opaque materials and no shadow maps, as in the engine): 'under' = 2 m up (at most 0.35 of the height), 1 m from the
trunk, looking up at 60 degrees toward the trunk; 'low_tq' = three-quarter view from 1 m up at the eye distance.
Prints the fraction of covered pixels darker than 20/255 (sRGB luminance) per view.
Usage: blender --background --python gate_views.py -- <tree.blend> <out_prefix>"""
import bpy, sys, math
import numpy as np
from mathutils import Vector
args = sys.argv[sys.argv.index('--') + 1:]
blend, prefix = args[0], args[1]
bpy.ops.wm.open_mainfile(filepath=blend)
sc = bpy.context.scene
for engine in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
    try:
        sc.render.engine = engine; break
    except TypeError:
        continue
sc.view_settings.view_transform = 'Standard'; sc.render.film_transparent = True
sc.render.resolution_x = sc.render.resolution_y = 480
world = sc.world or bpy.data.worlds.new('W'); sc.world = world; world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
bg.inputs['Color'].default_value = (0.55, 0.6, 0.68, 1); bg.inputs['Strength'].default_value = 0.5
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 3.6; sun.data.color = (1.0, 0.95, 0.86); sun.rotation_euler = (math.radians(40), 0, math.radians(-35))
# like the engine: no shadow maps on trees (self-shadowing is in COLOR_0), no screen-space occlusion
sun.data.use_shadow = False
try:
    sc.eevee.use_shadows = False; sc.eevee.use_fast_gi = False; sc.eevee.use_raytracing = False
except AttributeError:
    pass
for m in bpy.data.materials:
    if not m.use_nodes:
        continue
    nt = m.node_tree; bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bsdf is None or not bsdf.inputs['Base Color'].links:
        continue
    if not bsdf.inputs['Alpha'].links:
        m.use_backface_culling = True                   # opaque: single-sided in the engine
    bsdf.inputs['Specular IOR Level'].default_value = 0.15
    tex = bsdf.inputs['Base Color'].links[0].from_node
    attr = nt.nodes.new('ShaderNodeAttribute'); attr.attribute_type = 'GEOMETRY'; attr.attribute_name = 'Color'
    mul = nt.nodes.new('ShaderNodeVectorMath'); mul.operation = 'MULTIPLY'
    nt.links.new(tex.outputs['Color'], mul.inputs[0]); nt.links.new(attr.outputs['Color'], mul.inputs[1])
    nt.links.new(mul.outputs[0], bsdf.inputs['Base Color'])
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 24
for name in ('Tree', 'Tree_LOD1'):
    o = bpy.data.objects[name]
    for x in bpy.data.objects:
        if x.type == 'MESH':
            x.hide_render = x is not o
    H = max((o.matrix_world @ Vector(c)).z for c in o.bound_box)
    xs = [(o.matrix_world @ Vector(c)).x for c in o.bound_box]; cx = 0.5 * (min(xs) + max(xs))
    for view in ('under', 'low_tq'):
        if view == 'under':
            z = min(2.0, 0.35 * H)
            cam.location = Vector((0.7, -0.7, z))
            look = Vector((-0.7, 0.7, 0)).normalized() * math.cos(math.radians(60)) + Vector((0, 0, math.sin(math.radians(60))))
            cam.rotation_euler = look.to_track_quat('-Z', 'Y').to_euler()
        else:
            d = 1.6 * max(H, max(xs) - min(xs))
            cam.location = Vector((cx + d * math.sin(math.radians(45)), -d * math.cos(math.radians(45)), 1.0))
            cam.data.lens = 50
            cam.rotation_euler = (Vector((cx, 0, 0.45 * H)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
        path = f'{prefix}_{name}_{view}.png'
        sc.render.filepath = path; bpy.ops.render.render(write_still=True)
        cam.data.lens = 24
        img = bpy.data.images.load(path); px = np.array(img.pixels[:]).reshape(-1, 4)
        cov = px[:, 3] > 0.5
        lum = px[cov, :3] @ np.array([0.2126, 0.7152, 0.0722])
        print(f'GATEVIEW {name} {view} covered {cov.mean():.3f} black(<20/255) {(lum < 20 / 255).mean():.4f} '
              f'p5 {np.percentile(lum, 5) * 255:.0f}')
