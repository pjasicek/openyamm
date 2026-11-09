"""Old and new UVs of every triangle after the texture pass, for the colour pin and the class transfer.
Writes <out>/pairs_body.npz and pairs_head.npz: old, new (M x 3 x 2), same surface point per corner.
Args (Blender): <final blend> <old uv npz from uv_body.py> <out dir>"""
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
me = bpy.data.objects['Body'].data
old = np.load(a[1])
n = len(me.polygons)
assert all(len(p.vertices) == 3 for p in me.polygons) and len(old['head']) == n


def corners(layer):
    flat = np.zeros(len(me.loops) * 2, np.float32)
    me.uv_layers[layer].data.foreach_get('uv', flat)
    return flat.reshape(-1, 3, 2)


hd = np.zeros(n, np.int32); me.attributes['head'].data.foreach_get('value', hd)
assert np.array_equal(hd, old['head'])
mo = np.zeros(n, np.int32); me.attributes['mouth'].data.foreach_get('value', mo)
body, head = hd == 0, (hd > 0) & (mo == 0)
np.savez(os.path.join(a[2], 'pairs_body.npz'), old=old['uvmap'][body], new=corners('UVMap')[body])
np.savez(os.path.join(a[2], 'pairs_head.npz'), old=old['headuv'][head], new=corners('HeadUV')[head])
assert np.allclose(old['headuv'][mo > 0], corners('HeadUV')[mo > 0])
print('PAIRS', int(body.sum()), int(head.sum()), 'mouth UVs unchanged', int((mo > 0).sum()))
