"""1024 rasters per texture set from the master (body: non-head faces in UVMap; head: head faces in HeadUV):
coverage, rest position, face normal, piece per texel -> work/uvraster_{UVMap,HeadUV}.npz (asserts no overlap)."""
import bpy, os, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'master_r45.blend'))
rig = bpy.data.objects['Rig']; rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
body = bpy.data.objects['Body']; me = body.data; N = 1024
T = np.array([(body.matrix_world @ v.co)[:] for v in me.vertices]); head = np.array([a.value for a in me.attributes['head'].data])
pieces = np.array([a.value for a in me.attributes['piece'].data]); me.calc_loop_triangles()
for layer in ['UVMap', 'HeadUV']:
    want = layer == 'HeadUV'; hits = np.zeros((N, N), np.uint16); pos = np.zeros((N, N, 3), np.float32)
    piece = np.full((N, N), -1, np.int16); uvd = me.uv_layers[layer].data
    normal = np.zeros((N, N, 3), np.float32)
    for t in me.loop_triangles:
        if bool(head[t.polygon_index]) != want: continue
        a, b, c = [np.array(uvd[l].uv) * N for l in t.loops]
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-10: continue
        lo = np.maximum(np.floor(np.minimum(np.minimum(a, b), c)).astype(int), 0); hi = np.minimum(np.ceil(np.maximum(np.maximum(a, b), c)).astype(int), N - 1)
        x, y = np.meshgrid(np.arange(lo[0], hi[0] + 1) + .5, np.arange(lo[1], hi[1] + 1) + .5)
        w0 = ((b[1] - c[1]) * (x - c[0]) + (c[0] - b[0]) * (y - c[1])) / den; w1 = ((c[1] - a[1]) * (x - c[0]) + (a[0] - c[0]) * (y - c[1])) / den; w2 = 1 - w0 - w1
        m = (w0 > -1e-6) & (w1 > -1e-6) & (w2 > -1e-6); ix = (x[m] - .5).astype(int); iy = N - 1 - (y[m] - .5).astype(int)
        inside = (w0 > 1e-6) & (w1 > 1e-6) & (w2 > 1e-6); hits[N - 1 - (y[inside] - .5).astype(int), (x[inside] - .5).astype(int)] += 1
        V = list(t.vertices); piece[iy, ix] = pieces[V[0]]; normal[iy, ix] = (body.matrix_world.to_3x3() @ me.polygons[t.polygon_index].normal).normalized()[:]
        pos[iy, ix] = w0[m, None] * T[V[0]] + w1[m, None] * T[V[1]] + w2[m, None] * T[V[2]]
    cov = piece >= 0
    print('RASTER', layer, 'coverage', round(float(cov.mean()), 3), 'overlap', int((hits > 1).sum()))
    assert int((hits > 1).sum()) == 0
    np.savez_compressed(os.path.join(HERE, 'work', f'uvraster_{layer}.npz'), coverage=cov, pos=pos, piece=piece, normal=normal)
