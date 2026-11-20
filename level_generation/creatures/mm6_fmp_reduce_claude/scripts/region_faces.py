"""Per-face region labels of the source body (work/source.blend) by dominant bone weight of the face's vertices:
0 rest, 1 head (B_Head), 2 left hand + fingers, 3 right hand + fingers. -> work/regions.npy; prints counts."""
import bpy, numpy as np
src = bpy.data.objects['Body']; me = src.data
names = {g.index: g.name for g in src.vertex_groups}
def lab(n):
    if n == 'B_Head': return 1
    if n.startswith('B_L_Hand') or n.startswith('B_L_Finger'): return 2
    if n.startswith('B_R_Hand') or n.startswith('B_R_Finger'): return 3
    return 0
vl = np.zeros((len(me.vertices), 4))
for v in me.vertices:
    for g in v.groups: vl[v.index, lab(names[g.group])] += g.weight
fl = np.array([np.argmax(sum(vl[i] for i in p.vertices)) for p in me.polygons])
np.save('work/regions.npy', fl)
print('REGIONS', {k: int((fl == k).sum()) for k in range(4)})
