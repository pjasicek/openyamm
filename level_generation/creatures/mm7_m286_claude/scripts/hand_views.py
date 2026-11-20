"""Close orthographic views of both hands of 'Body' in a blend (wireframe on clay). Args: -- <blend> <out prefix>"""
import bpy, sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
J = json.load(open(os.path.join(HERE, 'work', 'joints_final.json')))['joints']
for o in bpy.data.objects:
    if o.type == 'MESH':
        o.show_wire = True
        for p in o.data.polygons:
            p.use_smooth = True
scene = bpy.context.scene
common.workbench_clay(scene)
for s in ('L', 'R'):
    w = J[f'{s}_Hand']
    common.render_views(os.path.abspath(a[1]) + f'_{s}', w[2] - 0.12, 0.42, views=('front', 'left', 'back', 'right'),
                        resolution=(500, 500), target=(w[0], w[1]))
