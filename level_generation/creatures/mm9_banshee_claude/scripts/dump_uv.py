"""Per-face arrays of the UV master for compose/alpha. Args: <blend> <out npz>"""
import bpy, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
out = {}
for name in ('Body', 'Head'):
    o = bpy.data.objects[name]; me = o.data
    n = len(me.polygons)
    idx = np.array([p.vertices[:] for p in me.polygons])
    co = np.array([tuple(o.matrix_world @ v.co) for v in me.vertices])
    uv = np.zeros((len(me.loops), 2)); me.uv_layers['UVMap'].data.foreach_get('uv', uv.ravel())
    ls = np.array([p.loop_indices[:] for p in me.polygons])
    out[name + '_idx'] = idx; out[name + '_co'] = co; out[name + '_uv'] = uv[ls]
    for at in ('part', 'hand'):
        if at in me.attributes:
            v = np.zeros(n, np.int32); me.attributes[at].data.foreach_get('value', v); out[name + '_' + at] = v
    for at in ('robe_s', 'robe_t', 'hpart'):
        if at in me.attributes:
            if at == 'hpart':
                v = np.zeros(len(me.vertices), np.int32)
            else:
                v = np.zeros(len(me.vertices), np.float32)
            me.attributes[at].data.foreach_get('value', v); out[name + '_' + at] = v
np.savez(a[1], **out)
print('DUMP', {k: v.shape for k, v in out.items()})
