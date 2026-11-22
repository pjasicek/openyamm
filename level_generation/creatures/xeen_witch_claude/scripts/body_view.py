"""Clay renders of 'Body' in a blend. Args: -- <blend> <tag> <cz> <height> [views csv]"""
import bpy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
views = tuple(a[4].split(',')) if len(a) > 4 else ('front', 'left', 'three_quarter', 'back')
for o in bpy.data.objects:
    if o.type == 'MESH':
        o.show_wire = os.environ.get('WIRE') == '1'
scene = bpy.context.scene; common.workbench_clay(scene)
common.render_views(os.path.join(common.REVIEW, a[1]), float(a[2]), float(a[3]), views=views, resolution=(600, 600))
