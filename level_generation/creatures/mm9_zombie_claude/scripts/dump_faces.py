"""Per-face UVs and bind positions for numpy composes. Args: <blend> <out npz>"""
import bpy, sys
import numpy as np
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=IN)
b = bpy.data.objects['Body']; me = b.data
n = len(me.polygons)
assert all(len(p.vertices) == 3 for p in me.polygons)
co = np.array([[me.vertices[i].co[:] for i in p.vertices] for p in me.polygons], np.float32)
loops = np.array([list(p.loop_indices) for p in me.polygons])
uvb = np.array([d.uv[:] for d in me.uv_layers['UVMap'].data], np.float32); uvh = np.array([d.uv[:] for d in me.uv_layers['HeadUV'].data], np.float32)
hd = np.zeros(n, np.int32); me.attributes['head'].data.foreach_get('value', hd)
to = np.zeros(n, np.int32); me.attributes['torso'].data.foreach_get('value', to)
uvt = np.array([d.uv[:] for d in me.uv_layers['TorsoUV'].data], np.float32)
pv = np.zeros(len(me.vertices), np.int32); me.attributes['part'].data.foreach_get('value', pv)
part = np.array([pv[p.vertices[0]] for p in me.polygons])
np.savez(OUT, co=co, uv=np.where(hd[:, None, None] > 0, uvh[loops], uvb[loops]), uvb=uvb[loops], uvh=uvh[loops], uvt=uvt[loops], torso=to, head=hd, part=part)
print('DUMPED', n)
