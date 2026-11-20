"""Clay/material review renders of body + tall crest (no neck spines) + crown. Args: -- <blend> <out prefix>"""
import bpy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
src, prefix = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.open_mainfile(filepath=C.path(src))
rig = bpy.data.objects[C.RIG]
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
show = [C.MESH, 'Crown_Head'] + [o.name for o in bpy.data.objects if o.name.startswith('Crest_tall_') and '_LOD' not in o.name
                                 and not o.name.endswith('Neck1')]
bpy.data.materials['Glow'].diffuse_color = (0.35, 0.65, 1.0, 1)
bpy.data.materials['Glass'].diffuse_color = (0.05, 0.05, 0.07, 1)
for m in C.MESH,:
    for s in bpy.data.objects[m].material_slots:
        s.material.diffuse_color = (0.62, 0.6, 0.57, 1)
views = {'34': ((-3.2, -4.2, 1.9), (0, -0.5, 0.7), 3.4), 'side': ((-5, -0.4, 0.8), (0, -0.4, 0.8), 3.4),
         'front': ((0, -5, 1.2), (0, -0.5, 0.8), 2.4), 'head34': ((-1.4, -2.6, 1.4), (0, -1.25, 0.85), 1.1),
         'back': ((0, 5, 1.6), (0, -0.4, 0.8), 2.4)}
for k, (loc, tgt, sc) in views.items():
    C.render_ortho(loc, tgt, sc, C.path(f'{prefix}_{k}.png'), show=show, color='material', res=(900, 700))
print('VIEWS done')
