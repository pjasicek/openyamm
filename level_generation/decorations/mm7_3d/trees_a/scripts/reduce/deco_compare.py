"""Installed vs reduced decoration, textured (Eevee), front / three-quarter / close detail, same cameras:
review/<name>_compare.png. Usage: blender -b -P deco_compare.py -- name [name ...]"""
import os, sys, math, bpy
from mathutils import Vector
# MM7 trees_a copy: built (unreduced) work/<id>/mm7_deco_<id>.glb vs work/reduce/mm7_deco_<id>.glb -> review/<id>/reduce_compare.png
HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for name in sys.argv[sys.argv.index('--') + 1:]:
    shots = []
    for label, path in (('built', f'{HERE}/work/{name}/mm7_deco_{name}.glb'),
                        ('reduced', f'{HERE}/work/reduce/mm7_deco_{name}.glb')):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=path)
        ob = next(o for o in bpy.data.objects if o.type == 'MESH')
        pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
        lo = Vector([min(p[k] for p in pts) for k in range(3)]); hi = Vector([max(p[k] for p in pts) for k in range(3)])
        c = (lo + hi) / 2; size = max((hi - lo).x, (hi - lo).y, (hi - lo).z)
        sc = bpy.context.scene
        cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
        cam.data.type = 'ORTHO'
        sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3.5
        sun.rotation_euler = (math.radians(45), 0, math.radians(-35)); sc.collection.objects.link(sun)
        w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
        w.node_tree.nodes['Background'].inputs['Color'].default_value = (.35, .36, .4, 1)
        sc.view_settings.view_transform = 'Standard'; sc.render.engine = 'BLENDER_EEVEE'
        sc.render.resolution_x = sc.render.resolution_y = 420
        for view, d, scale, target in (('front', (0, -1, .15), 1.15, c), ('q34', (.7, -.7, .4), 1.15, c),
                                       ('close', (.6, -.8, .2), 0.45, c + Vector((0, 0, -(hi - lo).z * 0.25)))):
            dv = Vector(d).normalized(); cam.location = target + dv * size * 3
            cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
            cam.data.ortho_scale = size * scale
            f = os.path.join(HERE, 'work', 'reduce', f'_{name}_{label}_{view}.png'); sc.render.filepath = f
            bpy.ops.render.render(write_still=True); shots.append(f)
    print('SHOTS', name, len(shots))
