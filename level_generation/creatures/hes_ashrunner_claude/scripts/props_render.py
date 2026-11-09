"""Textured EEVEE renders of a prop (work/<name>.blend, object <Name>) from both sides, three-quarter and above, framed
on its bounds -> review/props/<name>_<view>.png. Args: -- <name> [<name> ...]"""
import bpy, os, sys, math
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.makedirs(os.path.join(HERE, 'review', 'props'), exist_ok=True)
for name in sys.argv[sys.argv.index('--') + 1:]:
    bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', f'{name}.blend'))
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
    sc.render.resolution_x, sc.render.resolution_y = 900, 500
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND').inputs[1].default_value = 1.5
    sun = bpy.data.objects.new('s', bpy.data.lights.new('s', 'SUN')); sc.collection.objects.link(sun); sun.rotation_euler = (0.6, 0.3, 0.8)
    ob = next(o for o in bpy.data.objects if o.type == 'MESH')
    co = [ob.matrix_world @ v.co for v in ob.data.vertices]
    lo = Vector([min(c[i] for c in co) for i in range(3)]); hi = Vector([max(c[i] for c in co) for i in range(3)])
    c = (lo + hi) / 2; L = max(hi - lo) * 1.9
    for view, d in (('right', (1, 0, 0)), ('left', (-1, 0, 0)), ('tq', (0.7, 0.55, 0.45)), ('top', (0.05, 0, 1))):
        cam = bpy.data.objects.new(view, bpy.data.cameras.new(view)); sc.collection.objects.link(cam); cam.data.lens = 45
        cam.location = c + Vector(d).normalized() * L
        cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y' if view != 'top' else 'X').to_euler()
        sc.camera = cam; sc.render.filepath = os.path.join(HERE, 'review', 'props', f'{name}_{view}.png')
        bpy.ops.render.render(write_still=True)
    print('RENDERED', name)
