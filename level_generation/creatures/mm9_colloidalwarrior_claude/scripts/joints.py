"""Rest world positions of joints in a GLB (node matrices composed). Usage: joints.py <glb> [substr...]"""
import sys
import numpy as np
from pygltflib import GLTF2
def qm(q):
    x, y, z, w = q
    return np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)], [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)], [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])
def world(g):
    par = {}
    for i, n in enumerate(g.nodes):
        for c in n.children or []:
            par[c] = i
    W = {}
    def get(i):
        if i in W: return W[i]
        n = g.nodes[i]; M = np.eye(4)
        if n.matrix: M = np.array(n.matrix).reshape(4, 4).T
        else:
            M[:3, :3] = qm(n.rotation or [0, 0, 0, 1]) * np.array(n.scale or [1, 1, 1])
            M[:3, 3] = n.translation or [0, 0, 0]
        W[i] = (get(par[i]) @ M) if i in par else M
        return W[i]
    for i in range(len(g.nodes)): get(i)
    return W
if __name__ == '__main__':
    g = GLTF2().load(sys.argv[1]); W = world(g)
    for i, n in enumerate(g.nodes):
        if len(sys.argv) < 3 or any(s in (n.name or '') for s in sys.argv[2:]):
            print(f'{n.name:28s}', np.round(W[i][:3, 3], 3))
