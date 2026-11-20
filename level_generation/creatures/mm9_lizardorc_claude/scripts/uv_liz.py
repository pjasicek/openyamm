"""Sharp-texture UVs (claude_shared/uv_atlas.py). Sets: body (mat 0, fitted pose), head (skin, teeth, tongue; open pose at runtime scale). Writes work/uv.npz: uvb[faces,3,2], uvh, uvc and face lists.
Never re-run once its uploads went to Meshy."""
import bpy, bmesh, sys, os, json
import numpy as np
sys.path.insert(0, '/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared')
import uv_atlas
A = sys.argv[sys.argv.index('--') + 1:]
D = np.load(A[0]); co, tri, mat, up = D['co'], D['tri'], D['mat'], D['co_up']; copies = set(D['ringcopy'].tolist()); part = D['part']
b_ = lambda p: np.c_[p[:, 0], -p[:, 2], p[:, 1]]
def layout(P, F, name, dense=None, factor=1.0, **opt):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    used, inv = np.unique(F, return_inverse=True); Q = P[used]; Tt = inv.reshape(-1, 3)
    me = bpy.data.meshes.new(name); ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
    me.from_pydata(Q.tolist(), [], Tt.tolist()); me.update()
    bpy.context.view_layer.objects.active = ob; ob.select_set(True)
    g = ob.vertex_groups.new(name='DENSE')
    if dense is not None:
        ids = np.where(dense[used])[0]
        if len(ids): g.add(ids.tolist(), 1.0, 'REPLACE')
    rep = uv_atlas.unwrap(ob, head_groups=('DENSE',), head_factor=factor, **opt)
    print('USE', name, rep, flush=True)
    uv = me.uv_layers['UVMap'].data; n = len(me.polygons); out = np.zeros((n, 3, 2)); fo = np.zeros((n, 3), int)
    for i, p in enumerate(me.polygons):
        for k, li in enumerate(p.loop_indices):
            out[i, k] = uv[li].uv; fo[i, k] = used[me.loops[li].vertex_index]
    return out, fo
fb = tri[mat == 0]; fh_all = tri[mat == 1]; strip = np.isin(fh_all, list(copies)).any(1); fh = fh_all[~strip]
hand = (np.abs(co[:, 0]) > .55) & (co[:, 1] < .2) & (co[:, 1] > -.3)
W = A[2]
Hp = up * .68
dense = (part == 3) | (part == 4) | (part == 7)
if W == 'body': u, o = layout(b_(co), fb, 'body', hand, 1.45, size=2048, margin_px=2, cut_closed=True, steps=3)
if W == 'head': u, o = layout(b_(Hp), fh, 'head', dense, 1.5, size=2048, margin_px=2, cut_closed=True, steps=3)
np.savez(A[1] + '_' + W + '.npz', u=u, o=o)
print('UVDONE', W)
