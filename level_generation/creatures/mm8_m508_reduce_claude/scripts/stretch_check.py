"""Faces of the source and ladder candidates (work/<blend>) that stretch over 20x their rest area at any 2nd frame
of any clip: split seams (beak, lips) that the decimation bridged. Usage: blender -b -P stretch_check.py -- <blend> <Cand_70,...>"""
import os, sys, bpy, bmesh
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', args[0]))
sc = bpy.context.scene; rig = bpy.data.objects['Rig']


def areas(o):
    b = bmesh.new(); b.from_object(o, bpy.context.evaluated_depsgraph_get()); b.faces.ensure_lookup_table()
    a = np.array([f.calc_area() for f in b.faces]); c = np.array([f.calc_center_median()[:] for f in b.faces]); b.free()
    return a, c


for name in ['Body'] + args[1].split(','):
    o = bpy.data.objects[name]; rig.animation_data.action = None
    for pb in rig.pose.bones:
        pb.matrix_basis.identity()
    bpy.context.view_layer.update(); a0, c0 = areas(o); worst = {}
    for act in bpy.data.actions:
        rig.animation_data.action = act
        for f in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1, 2):
            sc.frame_set(f); a1, _ = areas(o)
            for i in np.where((a1 > 1e-6) & (a1 > 20 * (a0 + 1e-9)))[0]:
                worst.setdefault(int(i), f'{act.name}:{f}')
    print('STRETCH', name, len(worst), [(i, np.round(c0[i], 3).tolist(), w) for i, w in list(worst.items())[:6]], flush=True)
