"""Per-face UV pairs of the body faces between two layouts of the same master mesh (texture pass 2026-10-30): the
approved layout (before texpass_uv.py) and the new one, for match_skin.py's resampling of the approved paint.
Args (Blender): <old blend> <new blend> <out npz>   (writes old (F,3,2), new (F,3,2) UVMap corner UVs of the faces
that are neither head nor hand)"""
import bpy, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]


def uvs(path):
    bpy.ops.wm.open_mainfile(filepath=path)
    me = bpy.data.objects['Body'].data
    n = len(me.polygons)
    hd = np.zeros(n, np.int32); hn = np.zeros(n, np.int32)
    me.attributes['head'].data.foreach_get('value', hd)
    me.attributes['hand'].data.foreach_get('value', hn)
    flat = np.zeros(len(me.loops) * 2, np.float32)
    me.uv_layers['UVMap'].data.foreach_get('uv', flat)
    flat = flat.reshape(-1, 2)
    tri = np.array([flat[list(p.loop_indices)] for p in me.polygons])
    vid = np.array([[me.loops[i].vertex_index for i in p.loop_indices] for p in me.polygons])
    return tri, vid, (hd | hn) == 0


o, ov, ob = uvs(a[0])
nw, nv, nb = uvs(a[1])
assert (ov == nv).all() and (ob == nb).all()
np.savez(a[2], old=o[ob], new=nw[nb])
print('UV_PAIRS', int(ob.sum()), 'body faces')
