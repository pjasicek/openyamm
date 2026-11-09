import bpy, bmesh, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
ob = bpy.data.objects['Body']; rig = ob.parent
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
bm = bmesh.new(); bm.from_mesh(ob.data); lh = bm.faces.layers.int['hand']
mw = ob.matrix_world
print('PROBE rig mw', [round(x,3) for x in rig.matrix_world.translation], 'ob mw', [round(x,3) for x in mw.translation], ob.parent_type)
for tok in ('L','R'):
    a0 = np.array(rig.matrix_world @ rig.data.bones[f'Bip01 {tok} Forearm'].head_local)
    a1 = np.array(rig.matrix_world @ rig.data.bones[f'Bip01 {tok} Hand'].head_local)
    ax = (a1-a0)/np.linalg.norm(a1-a0)
    hv = np.array([tuple(mw @ v.co) for f in bm.faces if f[lh] for v in f.verts])
    s = (hv - a1) @ ax
    print('PROBE', tok, 'a0', np.round(a0,3), 'a1', np.round(a1,3), 'hand verts', len(hv), 's range', round(s.min(),3), round(s.max(),3), 'hand centre', np.round(hv.mean(0),3))
