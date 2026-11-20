"""Front profile (min y over |x|<w) per z band and arm extent, for the MM9 mesh (all pieces but the staff) and a Meshy
mesh, to pick a common scale landmark. Args: <mm9 glb> <meshy glb>"""
import bpy, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
def load(p, skip=()):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=p)
    dg = bpy.context.evaluated_depsgraph_get(); pts = []
    for o in bpy.context.scene.objects:
        if o.type == 'MESH' and not any(o.name.startswith(s) for s in skip):
            m = o.evaluated_get(dg).to_mesh(); pts += [tuple(o.matrix_world @ v.co) for v in m.vertices]
    return np.array(pts)
for nm, p, skip in (('MM9', a[0], ('staff', 'Icosphere')), ('OURS', a[1], ())):
    q = load(p, skip); z0, z1 = q[:, 2].min(), q[:, 2].max(); H = z1 - z0
    print('PROF', nm, 'zmin', round(z0, 3), 'zmax', round(z1, 3), 'xspan', round(q[:, 0].min(), 3), round(q[:, 0].max(), 3))
    for f in np.arange(0.70, 0.98, 0.01):
        z = z0 + f * H; m = (np.abs(q[:, 2] - z) < H * 0.006) & (np.abs(q[:, 0]) < H * 0.02)
        if m.sum():
            print('PROF', nm, 'f %.2f z %.3f miny %.3f maxy %.3f wid %.3f' % (f, z, q[m, 1].min(), q[m, 1].max(),
                  np.ptp(q[np.abs(q[:, 2] - z) < H * 0.006][:, 0]) if True else 0))
