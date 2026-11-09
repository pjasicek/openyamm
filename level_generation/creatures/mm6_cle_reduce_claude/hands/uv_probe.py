import bpy, numpy as np
bpy.ops.wm.open_mainfile(filepath='mpfb_hands.blend')
for n in ('HandL', 'HandR'):
    me = bpy.data.objects[n].data; uv = np.array([d.uv[:] for d in me.uv_layers.active.data])
    print('UV', n, 'min', uv.min(0).round(3), 'max', uv.max(0).round(3), 'layers', [l.name for l in me.uv_layers], 'verts', len(me.vertices))
    # 3D size
    P = np.array([v.co[:] for v in me.vertices]); print('  size', (P.max(0) - P.min(0)).round(3))
