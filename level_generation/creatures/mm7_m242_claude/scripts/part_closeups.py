"""Close renders of the st_v1 parts blend: hands (front/side) and wings (top/back). Args: -- <parts blend> <tag>"""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
src, tag = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
sc = bpy.context.scene; common.workbench_clay(sc); sc.display.shading.color_type = 'MATERIAL'
for o in bpy.data.objects:
    if o.type == 'MESH': o.show_wire = True
for side, x in (('R', -0.38), ('L', 0.38)):
    common.render_views(os.path.join(common.REVIEW, f'{tag}_hand{side}'), 0.82, 0.32, views=('front', 'left', 'back'),
                        resolution=(500, 500), target=(x, 0.0))
