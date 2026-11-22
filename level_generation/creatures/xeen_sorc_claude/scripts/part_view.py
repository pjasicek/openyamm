"""Render chosen parts of work/st_v1_parts.blend alone. Args: -- <tag> <cz> <height> <part,part,...|all-but:...>"""
import bpy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
tag, cz, h, sel = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'st_v1_parts.blend'))
neg = sel.startswith('not:')
names = set(sel[4:].split(',') if neg else sel.split(','))
for o in bpy.data.objects:
    if o.type == 'MESH':
        o.hide_render = (o.name in names) if neg else (o.name not in names)
        o.show_wire = True
scene = bpy.context.scene; common.workbench_clay(scene)
common.render_views(os.path.join(common.REVIEW, f'pv_{tag}'), float(cz), float(h), views=('front', 'left', 'three_quarter'), resolution=(500, 500))
