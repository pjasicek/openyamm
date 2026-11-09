"""Dwarf region survey on work/source.blend: dominant-bone labels (0 rest, 1 head, 2 left hand, 3 right hand), head
texture set (atlas u > 0.5), welded connected components. -> work/regions.npy, work/headset.npy, work/comp.npy."""
import bpy, bmesh, numpy as np
src = bpy.data.objects['Body']; me = src.data
names = {g.index: g.name for g in src.vertex_groups}
print('BONES', sorted(names.values()))
def lab(n):
    if n in ('B_Head', 'B_Jaw'): return 1
    if n.startswith('B_L_Hand') or n.startswith('B_L_Finger') or n.startswith('B_L_Thumb') or n.startswith('B_L_Index') or n.startswith('B_L_Middle') or n.startswith('B_L_Ring') or n.startswith('B_L_Pinky'): return 2
    if n.startswith('B_R_Hand') or n.startswith('B_R_Finger') or n.startswith('B_R_Thumb') or n.startswith('B_R_Index') or n.startswith('B_R_Middle') or n.startswith('B_R_Ring') or n.startswith('B_R_Pinky'): return 3
    return 0
vl = np.zeros((len(me.vertices), 4))
for v in me.vertices:
    for g in v.groups: vl[v.index, lab(names[g.group])] += g.weight
me.calc_loop_triangles(); uv = me.uv_layers.active.data
tris = me.loop_triangles
fl = np.array([np.argmax(sum(vl[i] for i in t.vertices)) for t in tris])
hs = np.array([np.mean([uv[l].uv[0] for l in t.loops]) > 0.5 for t in tris])
np.save('work/regions.npy', fl); np.save('work/headset.npy', hs)
print('REGIONS', {k: int((fl == k).sum()) for k in range(4)}, 'HEADSET', int(hs.sum()))
# components over vertex connectivity of triangles
par = list(range(len(me.vertices)))
def f(a):
    while par[a] != a: par[a] = par[par[a]]; a = par[a]
    return a
for t in tris:
    a, b, c = (f(i) for i in t.vertices); par[b] = a; par[f(c)] = a
roots = np.array([f(t.vertices[0]) for t in tris]); u, inv, cnt = np.unique(roots, return_inverse=True, return_counts=True)
np.save('work/comp.npy', inv)
z = np.array([np.mean([me.vertices[i].co.z for i in t.vertices]) for t in tris])
x = np.array([np.mean([me.vertices[i].co.x for i in t.vertices]) for t in tris])
y = np.array([np.mean([me.vertices[i].co.y for i in t.vertices]) for t in tris])
order = np.argsort(-cnt)
print('COMPONENTS', len(u))
for k in order:
    m = inv == k
    print(f'  comp {k:4d} faces {cnt[k]:5d} z {z[m].mean():.3f} x {x[m].mean():+.3f} y {y[m].mean():+.3f} region {np.bincount(fl[m], minlength=4).tolist()} headset {int(hs[m].sum())}')
