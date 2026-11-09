"""Clay close-ups of a parts blend around a point. Args: tag cx cy cz size [views...]"""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
tag, cx, cy, cz, size = a[0], float(a[1]), float(a[2]), float(a[3]), float(a[4])
views = tuple(a[5:]) or ('front', 'left', 'back', 'right')
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, f'{tag}_parts.blend') if not tag.endswith('.blend')
                         else os.path.join(common.WORK, tag))
for o in bpy.data.objects:
    if o.type == 'MESH':
        o.show_wire = True
sc = bpy.context.scene
common.workbench_clay(sc)
sc.display.shading.color_type = 'MATERIAL'
name = os.path.splitext(os.path.basename(tag))[0]
common.render_views(os.path.join(common.REVIEW, f'{name}_at_{cx:.2f}_{cz:.2f}'), cz, size, views=views,
                    resolution=(450, 450), target=(cx, cy))
