"""Per-face sets of the rest mesh for the m628 ladder (same order as work/mesh_in.npz): dominant bone per face,
bow material, string, fingers/hands, coincident-vertex neighbourhoods -> work/sets.npz. Prints counts."""
import os, collections, bpy, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'source.blend'))
o = bpy.data.objects['Body']; me = o.data; me.calc_loop_triangles()
gn = {g.index: g.name for g in o.vertex_groups}
dom = [gn[max(v.groups, key=lambda g: g.weight).group] if v.groups else '' for v in me.vertices]
tris = me.loop_triangles
fdom = np.array([collections.Counter(dom[i] for i in t.vertices).most_common(1)[0][0] for t in tris])
mat = np.array([t.material_index for t in tris])
sharp = np.array([not me.polygons[t.polygon_index].use_smooth for t in tris])
v = np.array([x.co[:] for x in me.vertices])
key = collections.defaultdict(list)
for i, p in enumerate(np.round(v, 6)):
    key[tuple(p)].append(i)
pairs = np.array(sorted(i for l in key.values() if len(l) > 1 for i in l), int)
for i in pairs:
    print('COINCIDENT', i, np.round(v[i], 3), dom[i])
np.savez(os.path.join(HERE, 'work', 'sets.npz'), dom=fdom, mat=mat, sharp=sharp, pairs=pairs)
print('sharp by bone', collections.Counter(fdom[sharp]).most_common(20))
