"""Shaded candidate views for picking a scan: blender --background --python views.py -- <out_dir> <key:yaw:el[:M][:rX_Y_Z]>...
Each spec renders scan <key> (mirrored in x with M, rotated by rX_Y_Z degrees, grounded) from yaw/elevation degrees to <out_dir>/<spec>.png."""
import bpy, bmesh, math, os, sys
from mathutils import Euler, Matrix, Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scans

args = sys.argv[sys.argv.index('--') + 1:]
out, specs = args[0], args[1:]
os.makedirs(out, exist_ok=True)


def bounds(objs):
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    return (Vector([min(p[i] for p in pts) for i in range(3)]), Vector([max(p[i] for p in pts) for i in range(3)]))


loaded = None
for spec in specs:
    key, yaw, el, *flags = spec.split(':')
    yaw, el = float(yaw), float(el)
    if loaded != (key, tuple(flags)):
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
            o.data.transform(o.matrix_world); o.matrix_world.identity()
            if 'M' in flags:
                o.data.transform(Matrix.Scale(-1, 4, (1, 0, 0)))
                o.data.flip_normals()
            for f in flags:
                if f.startswith('r'):
                    o.data.transform(Euler([math.radians(float(a)) for a in f[1:].split('_')]).to_matrix().to_4x4())
        lo, hi = bounds(keep)
        for o in keep:
            o.location -= Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
        bpy.context.view_layer.update()
        lo, hi = bounds(keep)
        scene = bpy.context.scene
        scene.render.film_transparent = True
        scene.render.engine = 'BLENDER_EEVEE'
        scene.render.resolution_x = scene.render.resolution_y = 384
        scene.eevee.taa_render_samples = 16
        scene.view_settings.view_transform = 'Standard'
        world = bpy.data.worlds.new('W'); scene.world = world; world.use_nodes = True
        bg = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
        bg.inputs['Color'].default_value = (0.55, 0.62, 0.72, 1); bg.inputs['Strength'].default_value = 0.9
        sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3.2
        scene.collection.objects.link(sun)
        cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); scene.collection.objects.link(cam)
        scene.camera = cam; cam.data.lens = 50
        loaded = (key, tuple(flags))
    # light from the upper left of the view, as the sprites are lit
    sun.rotation_euler = (math.radians(45), 0, math.radians(yaw - 45))
    centre = (lo + hi) / 2; radius = (hi - lo).length / 2
    fov = 2 * math.atan(cam.data.sensor_width / (2 * cam.data.lens)); dist = radius * 1.05 / math.sin(fov / 2)
    d = Vector((math.sin(math.radians(yaw)) * math.cos(math.radians(el)),
                -math.cos(math.radians(yaw)) * math.cos(math.radians(el)), math.sin(math.radians(el))))
    cam.location = centre + d * dist
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = os.path.join(out, spec.replace(':', '_') + '.png')
    bpy.ops.render.render(write_still=True)
