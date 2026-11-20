"""Compare joint names and bind world positions of two MM9-converted GLBs."""
import sys, numpy as np, pygltflib
def world(path):
    g = pygltflib.GLTF2().load(path)
    sk = g.skins[0]; nodes = g.nodes
    par = {}
    for i, n in enumerate(nodes):
        for c in (n.children or []): par[c] = i
    def local(i):
        n = nodes[i]
        if n.matrix: return np.array(n.matrix).reshape(4, 4).T
        t = np.eye(4); q = n.rotation or [0, 0, 0, 1]; x, y, z, w = q
        R = np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)], [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)], [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])
        t[:3, :3] = R * np.array(n.scale or [1, 1, 1]); t[:3, 3] = n.translation or [0, 0, 0]; return t
    def W(i): return local(i) if i not in par else W(par[i]) @ local(i)
    return {nodes[j].name: W(j)[:3, 3] for j in sk.joints}
a, b = world(sys.argv[1]), world(sys.argv[2])
common = sorted(set(a) & set(b))
print('joints', len(a), len(b), 'common', len(common), 'only a', sorted(set(a) - set(b))[:10], 'only b', sorted(set(b) - set(a))[:10])
d = sorted(((np.linalg.norm(a[k] - b[k]), k) for k in common), reverse=True)
print('max diffs (m):', [(round(x, 4), k) for x, k in d[:8]])
