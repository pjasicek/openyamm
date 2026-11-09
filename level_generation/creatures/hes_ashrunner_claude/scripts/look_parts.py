"""Review render of selected Smart Topology parts (work/st_v1_parts.blend): the listed parts coloured, the rest grey,
orthographic views around a centre. Args: -- <tag> <centre z> <height> <part,part,...|all> [views]"""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
tag, cz, h, sel = a[0], float(a[1]), float(a[2]), a[3]
views = tuple(a[4].split(',')) if len(a) > 4 else ('front', 'left', 'back', 'right')
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'st_v1_parts.blend'))
want = None if sel == 'all' else {f'P{int(x):02d}' for x in sel.split(',')}
grey = bpy.data.materials.new('grey'); grey.diffuse_color = (0.75, 0.75, 0.75, 1)
for o in bpy.data.objects:
    if o.type == 'MESH' and want is not None and o.name not in want:
        o.data.materials.clear(); o.data.materials.append(grey)
    if o.type == 'MESH':
        o.show_wire = False
scene = bpy.context.scene; common.workbench_clay(scene); scene.display.shading.color_type = 'MATERIAL'
common.render_views(os.path.join(common.REVIEW, f'look_{tag}'), cz, h, views=views, resolution=(700, 700))
