"""Per-face region labels of the source body (work/source.blend) by dominant bone weight of the face's vertices:
0 rest, 1 head (Head), 2 left hand, 3 right hand (Titan: Meshy rig, no finger bones). -> work/regions.npy; prints counts."""
import bpy, numpy as np
src = bpy.data.objects['Body']; me = src.data
names = {g.index: g.name for g in src.vertex_groups}
def lab(n):
    if n in ('Head', 'head_end', 'headfront'): return 1
    if n in ('LeftHand', 'Socket_Palm_Left'): return 2
    if n in ('RightHand', 'Socket_Palm_Right'): return 3
    return 0
vl = np.zeros((len(me.vertices), 4))
for v in me.vertices:
    for g in v.groups: vl[v.index, lab(names[g.group])] += g.weight
fl = np.array([np.argmax(sum(vl[i] for i in p.vertices)) for p in me.polygons])
np.save('work/regions.npy', fl)
print('REGIONS', {k: int((fl == k).sum()) for k in range(4)})
