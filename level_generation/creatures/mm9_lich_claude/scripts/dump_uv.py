"""Corner UVs (UVMap, HeadUV), positions and part/fid per face of the master. Args: blend, out npz"""
import bpy, sys
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
b = bpy.data.objects['Body']; me = b.data
n = len(me.polygons)
part = np.zeros(n, np.int32); me.attributes['part'].data.foreach_get('value', part)
fid = np.zeros(n, np.int32); me.attributes['fid'].data.foreach_get('value', fid)
idx = np.array([list(p.vertices) for p in me.polygons]); lidx = np.array([list(p.loop_indices) for p in me.polygons])
uv = np.array([tuple(d.uv) for d in me.uv_layers['UVMap'].data]); hu = np.array([tuple(d.uv) for d in me.uv_layers['HeadUV'].data])
co = np.array([v.co for v in me.vertices])
# dominant bone per vertex
names = [g.name for g in b.vertex_groups]
dom = np.array([names[max(v.groups, key=lambda g: g.weight).group] for v in me.vertices])
np.savez(argv[1], part=part, fid=fid, idx=idx, uv=uv[lidx], hu=hu[lidx], co=co, dom=dom)
print('DUMP', n)
