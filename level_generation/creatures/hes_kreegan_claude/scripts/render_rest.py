"""Clay/textured turnaround of a blend's objects in rest pose. Args: -- <blend> <out_prefix> [textured 0|1] [views...]"""
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
tex = len(a) > 2 and a[2] == '1'
views = a[3:] or ['front', 'three_quarter', 'left', 'back']
for o in bpy.data.objects:
    if o.type == 'ARMATURE':
        if o.animation_data: o.animation_data.action = None
        for pb in o.pose.bones: pb.matrix_basis.identity()
sc = common.setup_render((600, 900)); common.workbench_clay(sc, tex)
sc.display.shading.color_type = 'TEXTURE' if tex else 'MATERIAL'
common.render_views(a[1], 0.86, 1.95, views, resolution=(600, 900))
