"""Silhouette survey: render every candidate scan (each set piece alone, grounded) from 24 yaws at 10 and 20 degrees
elevation, as alpha masks (Workbench) in ../work/survey/<key>_e<el>_y<yaw>.png, plus shaded Eevee thumbnails at
45 degree steps in ../work/survey_shaded/. Usage: blender --background --python survey.py -- [key...]"""
import bpy, math, os, sys
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scans

args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
shaded = '--shaded' in args
keys = [a for a in args if not a.startswith('--')] or list(scans.SCANS)
out = os.path.join(scans.HERE, 'work', 'survey_shaded' if shaded else 'survey'); os.makedirs(out, exist_ok=True)


def bounds(objs):
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    return (Vector([min(p[i] for p in pts) for i in range(3)]), Vector([max(p[i] for p in pts) for i in range(3)]))


for key in keys:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    path, node = scans.SCANS[key]
    bpy.ops.import_scene.gltf(filepath=path)
    objs = [o for o in bpy.data.objects if o.type == 'MESH']
    keep = [o for o in objs if node is None or o.name.startswith(node) or o.data.name.startswith(node)]
    for o in bpy.data.objects:
        if o not in keep:
            bpy.data.objects.remove(o)
    for o in keep:
        o.parent = None
    lo, hi = bounds(keep)
    for o in keep:
        o.location -= Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    bpy.context.view_layer.update()
    lo, hi = bounds(keep)
    scene = bpy.context.scene
    scene.render.film_transparent = True
    if shaded:
        scene.render.engine = 'BLENDER_EEVEE'
        scene.render.resolution_x = scene.render.resolution_y = 256
        scene.eevee.taa_render_samples = 8
        world = bpy.data.worlds.new('W'); scene.world = world; world.use_nodes = True
        bg = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
        bg.inputs['Color'].default_value = (0.55, 0.62, 0.72, 1); bg.inputs['Strength'].default_value = 0.9
        sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3.2
        scene.collection.objects.link(sun); sun.rotation_euler = (math.radians(40), 0, math.radians(-35))
    else:
        scene.render.engine = 'BLENDER_WORKBENCH'
        scene.render.resolution_x = scene.render.resolution_y = 160
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); scene.collection.objects.link(cam)
    scene.camera = cam; cam.data.lens = 50
    centre = (lo + hi) / 2; radius = (hi - lo).length / 2
    fov = 2 * math.atan(cam.data.sensor_width / (2 * cam.data.lens)); dist = radius * 1.05 / math.sin(fov / 2)
    views = [(15, y) for y in range(0, 360, 45)] if shaded else [(e, y) for e in (10, 20) for y in range(0, 360, 15)]
    for el, yaw in views:
        d = Vector((math.sin(math.radians(yaw)) * math.cos(math.radians(el)),
                    -math.cos(math.radians(yaw)) * math.cos(math.radians(el)), math.sin(math.radians(el))))
        cam.location = centre + d * dist
        cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = os.path.join(out, f'{key}_e{el:02d}_y{yaw:03d}.png')
        bpy.ops.render.render(write_still=True)
    print('SURVEY', key, [round(v, 3) for v in hi - lo])
