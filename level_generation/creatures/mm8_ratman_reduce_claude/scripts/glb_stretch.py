"""stretch_check.py on GLBs as exported (each with its own rig and clips): faces of the full-detail mesh that stretch
over 20x their rest area at any frame of any clip. Usage: blender -b -P glb_stretch.py -- <label=glb,...> [node]"""
import os, sys, bpy, bmesh
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[sys.argv.index('--') + 1:]; NODE = args[1] if len(args) > 1 else 'Ratman'
for item in args[0].split(','):
    label, glb = item.split('=')
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE'); o = bpy.data.objects[NODE]

    def areas():
        b = bmesh.new(); b.from_object(o, bpy.context.evaluated_depsgraph_get()); b.faces.ensure_lookup_table()
        a = np.array([f.calc_area() for f in b.faces]); c = np.array([f.calc_center_median()[:] for f in b.faces]); b.free()
        return a, c
    rig.animation_data.action = None
    for pb in rig.pose.bones:
        pb.matrix_basis.identity()
    bpy.context.view_layer.update(); a0, c0 = areas(); bad = {}
    for act in bpy.data.actions:
        rig.animation_data.action = act
        for f in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1):
            sc.frame_set(f); a1, _ = areas()
            for i in np.where((a1 > 1e-6) & (a1 > 20 * (a0 + 1e-9)))[0]:
                bad.setdefault(int(i), f'{act.name}:{f}')
    print('STRETCH', label, len(bad), [(i, np.round(c0[i], 3).tolist(), w) for i, w in sorted(bad.items())[:8]], flush=True)
