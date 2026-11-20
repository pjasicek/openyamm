"""Dump triangles of named objects (world space) to npz: <blend> <out npz> <obj>... (key per object)."""
import bpy, sys, numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
out = {}
for name in argv[2:]:
    o = bpy.data.objects[name]
    me = o.data; me.calc_loop_triangles()
    out[name + '_v'] = np.array([tuple(o.matrix_world @ v.co) for v in me.vertices], np.float32)
    out[name + '_t'] = np.array([tuple(t.vertices) for t in me.loop_triangles], np.int32)
    if me.attributes.get('comp'):
        a = me.attributes['comp']
        out[name + '_c'] = np.array([a.data[t.polygon_index].value for t in me.loop_triangles], np.int32)
np.savez(argv[1], **out)
print('DUMP', {k: v.shape for k, v in out.items()})
