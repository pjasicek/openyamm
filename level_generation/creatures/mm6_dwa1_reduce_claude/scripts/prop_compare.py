"""Installed vs reduced held props, textured (Eevee) and clay (workbench with cavity), four views on the longest
axis: review/props/_<name>_*.png (prop_sheet.py <name> -> <name>_compare.png), one row per model (installed first, then each tag).
Usage: blender -b -P prop_compare.py -- name tag [tag ...]   (export/mm6_dwa1_<name>_<tag>.glb)"""
import os, sys, math, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.abspath(os.path.join(HERE, '../../..'))
OUT = os.path.join(HERE, 'review', 'props'); os.makedirs(OUT, exist_ok=True)
name, *tags = sys.argv[sys.argv.index('--') + 1:]
rows = []
for label, path in [('installed', f'{ROOT}/assets_source/worlds/mm6/models/mm6_dwa1_{name}.glb')] + \
        [(t, f'{HERE}/export/mm6_dwa1_{name}_{t}.glb') for t in tags]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)
    ob = next(o for o in bpy.data.objects if o.type == 'MESH' and 'LOD' not in o.name)
    for o in bpy.data.objects:
        if o.type == 'MESH' and o is not ob: o.hide_render = True
    pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    lo = Vector([min(p[k] for p in pts) for k in range(3)]); hi = Vector([max(p[k] for p in pts) for k in range(3)])
    c = (lo + hi) / 2; ext = hi - lo; size = max(ext)
    axes = sorted(range(3), key=lambda k: ext[k])  # thinnest axis first: look along it for the flat views
    n = Vector([1.0 if k == axes[0] else 0.0 for k in range(3)]); m = Vector([1.0 if k == axes[1] else 0.0 for k in range(3)])
    sc = bpy.context.scene
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3.5
    sun.rotation_euler = (math.radians(45), 0, math.radians(-35)); sc.collection.objects.link(sun)
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    next(nd for nd in w.node_tree.nodes if nd.type == 'BACKGROUND').inputs[0].default_value = (.35, .36, .4, 1)
    sc.view_settings.view_transform = 'Standard'
    sc.render.resolution_x = sc.render.resolution_y = 400
    up = Vector([1.0 if k == axes[2] else 0.0 for k in range(3)])
    views = (('face', n, 1.1), ('back', -n, 1.1), ('q34', (n + m * .8 + up * .3).normalized(), 1.1),
             ('edge', m, 1.1))
    shots = []
    for engine in ('EEVEE', 'WORKBENCH'):
        sc.render.engine = 'BLENDER_' + engine
        if engine == 'WORKBENCH':
            sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.show_cavity = True
        for view, d, scale in views:
            cam.location = c + d * size * 3
            cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Z' if abs(d.z) < .9 else 'Y').to_euler()
            cam.data.ortho_scale = size * scale
            f = os.path.join(OUT, f'_{name}_{label}_{view}_{engine}.png'); sc.render.filepath = f
            bpy.ops.render.render(write_still=True); shots.append(f)
    rows.append(shots)
open(os.path.join(OUT, f'_{name}_rows.txt'), 'w').write('\n'.join(' '.join(r) for r in rows))
print('SHOTS', name, len(rows))  # prop_sheet.py <name> assembles review/props/<name>_compare.png
