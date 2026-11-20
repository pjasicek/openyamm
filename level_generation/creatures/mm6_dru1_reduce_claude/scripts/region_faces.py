"""Per-face region labels of the source body (work/source.blend) by dominant bone weight, matching the face order of
work/mesh_in.npz (loop triangles): 0 rest, 1 head non-face (hair, hood; the face mask is protected separately),
2 hands + fingers, 3 cloak chains, 4 legs/boots. -> work/regions.npy; prints counts.
Usage: blender -b work/source.blend -P scripts/region_faces.py"""
import bpy, numpy as np
src = bpy.data.objects['Body']; me = src.data; me.calc_loop_triangles()
names = {g.index: g.name for g in src.vertex_groups}
def lab(n):
    if n in ('B_Head', 'B_Neck'): return 1
    if 'Hand' in n or 'Finger' in n or 'Thumb' in n or 'Index' in n or 'Middle' in n or 'Ring' in n or 'Pinky' in n: return 2
    if n.startswith('Cloak'): return 3
    if 'Thigh' in n or 'Calf' in n or 'Foot' in n or 'Toe' in n or 'Leg' in n: return 4
    return 0
vl = np.zeros((len(me.vertices), 5))
for v in me.vertices:
    for g in v.groups: vl[v.index, lab(names[g.group])] += g.weight
fl = np.array([np.argmax(sum(vl[i] for i in t.vertices)) for t in me.loop_triangles])
np.save('work/regions.npy', fl)
print('REGIONS', {k: int((fl == k).sum()) for k in range(5)})
print('BONES', sorted({n for n in names.values() if not n.startswith('Cloak')})[:80])
