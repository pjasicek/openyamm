"""Rest-pose renders of work/st_v1_parts.blend with the listed parts in red (everything else clay): which hidden
pieces show from outside. Args: -- <parts blend> <out prefix> <piece numbers...>"""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
want = {f'P{int(x):02d}' for x in a[2:]}
red = bpy.data.materials.new('red'); red.diffuse_color = (1, 0.05, 0.05, 1)
grey = bpy.data.materials.new('grey'); grey.diffuse_color = (0.7, 0.7, 0.7, 1)
for o in bpy.data.objects:
    if o.type == 'MESH':
        o.data.materials.clear(); o.data.materials.append(red if o.name in want else grey)
sc = bpy.context.scene; common.workbench_clay(sc); sc.display.shading.color_type = 'MATERIAL'
common.render_views(a[1], 1.35, 0.9, views=('back', 'left', 'right', 'three_quarter'), resolution=(500, 500))
