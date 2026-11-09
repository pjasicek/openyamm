"""Per-face labels of work/source.blend / work/mesh_in.npz: dominant-weight regions (0 rest, 1 head, 2 left hand,
3 right hand, 4 tail, 5 loin flap, 6 string bones) -> work/regions.npy, LizardBow_A faces -> work/stringmat.npy,
connected pieces -> work/comp.npy; keep = string/arrow faces + pieces of <= 80 faces -> work/keep_a.npy;
groups 1 head+neck piece, 2 hands, 3 tunic piece -> work/groups_b.npy.
Run: blender -b work/source.blend -P regions.py (weights), then python3 regions.py (pieces; Blender has no scipy)."""
import numpy as np
try:
    import bpy
except ImportError:
    bpy = None
if bpy is not None:
    src = bpy.data.objects['Body']; me = src.data
    names = {g.index: g.name for g in src.vertex_groups}
    def lab(n):
        if n == 'B_Head': return 1
        if n.startswith('B_L_Hand') or n.startswith('B_L_Finger'): return 2
        if n.startswith('B_R_Hand') or n.startswith('B_R_Finger'): return 3
        if n.startswith('Tail'): return 4
        if n == 'LoinFlap': return 5
        if n.startswith('String'): return 6
        return 0
    vl = np.zeros((len(me.vertices), 7))
    for v in me.vertices:
        for g in v.groups: vl[v.index, lab(names[g.group])] += g.weight
    me.calc_loop_triangles()
    reg = np.array([np.argmax(sum(vl[i] for i in t.vertices)) for t in me.loop_triangles])
    sm = np.array([t.material_index == 1 for t in me.loop_triangles])
    np.save('work/regions.npy', reg); np.save('work/stringmat.npy', sm); print('REGIONS', np.bincount(reg).tolist())
    raise SystemExit
from scipy.sparse import coo_matrix  # noqa: E402
from scipy.sparse.csgraph import connected_components  # noqa: E402
reg, sm = np.load('work/regions.npy'), np.load('work/stringmat.npy')
d = np.load('work/mesh_in.npz'); f = d['faces']; n = len(d['verts']); assert len(f) == len(reg)
r = np.r_[f[:, 0], f[:, 1], f[:, 2]]; c = np.r_[f[:, 1], f[:, 2], f[:, 0]]
comp = connected_components(coo_matrix((np.ones(len(r)), (r, c)), shape=(n, n)), directed=False)[1][f[:, 0]]
size = np.bincount(comp)
head = np.bincount(comp[reg == 1]).argmax()
cz = np.array([d['verts'][f[comp == k]].reshape(-1, 3).mean(0) if size[k] else np.zeros(3) for k in range(len(size))])
# tunic: the largest torso-height piece without hand or head faces
cands = [k for k in np.argsort(-size) if k != head and 1.1 < cz[k][2] < 1.4 and not np.isin(reg[comp == k], [1, 2, 3]).any()]
tunic = cands[0]
keep = sm | (size[comp] <= 80)
g = np.zeros(len(f), int); g[comp == head] = 1; g[(reg == 2) | (reg == 3)] = 2; g[comp == tunic] = 3
for name, arr in (('comp', comp), ('keep_a', keep), ('groups_b', g)):
    np.save(f'work/{name}.npy', arr)
print('PIECES', len(size), 'head', head, size[head], 'tunic', tunic, size[tunic], np.round(cz[tunic], 2), 'kept', int(keep.sum()),
      'groups', {k: int((g == k).sum()) for k in range(4)})
