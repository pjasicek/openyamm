"""Bandanna poking through the head skin (rest pose): bandanna vertices outside the skin surface (signed distance along
the nearest skin face's normal) within 2 cm, for the source and decimated meshes (work/mesh_<tag>.npz).
Usage: blender -b -P band_poke.py -- <tag,...> [mm threshold, default 0.2]"""
import os, sys
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def components(n, f):
    parent = np.arange(n)
    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    for a, b, c in f:
        ra, rb, rc = root(a), root(b), root(c); parent[rb] = ra; parent[root(rc)] = ra
    return np.array([root(i) for i in range(n)])
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); W = os.path.join(HERE, 'work')
args = sys.argv[sys.argv.index('--') + 1:]
thr = float(args[1]) / 1000 if len(args) > 1 else 0.0002
src = np.load(f'{W}/mesh_in.npz'); g = np.load(f'{W}/groups.npy')
sb = src['verts'][src['faces'][g == 3]].mean((0, 1)); ss = src['verts'][src['faces'][g == 1]].mean((0, 1))
def pieces(tag):
    d = np.load(f'{W}/mesh_{tag}.npz'); v, f = d['verts'], d['faces']
    lab = components(len(v), f); pc = lab[f[:, 0]]; cen = v[f].mean(1)
    band = pc[np.argmin(np.linalg.norm(cen - sb, axis=1))]; skin = pc[np.argmin(np.linalg.norm(cen - ss, axis=1))]
    return v, np.unique(f[pc == band]), BVHTree.FromPolygons([Vector(p) for p in v], f[pc == skin].tolist())


def signed(tree, p):
    loc, nor, _, dist = tree.find_nearest(Vector(p))
    return (Vector(p) - loc).dot(nor) if dist < 0.02 else -1.0


_, _, src_skin = pieces('in')
for tag in ['in'] + args[0].split(','):
    v, bv, skin = pieces(tag)
    shown, poked = [], []
    for i in bv:
        s0, s1 = signed(src_skin, v[i]), signed(skin, v[i])
        if s1 > thr and s0 <= thr:
            shown.append((s1, i))  # the skin moved inward over this bandanna point
        elif s1 > thr:
            poked.append((s1, i))  # outside the source skin too (the bandanna moved, or the source has it)
    shown.sort(reverse=True); poked.sort(reverse=True)
    np.save(f'{W}/poke_{tag}.npy', np.array([i for _, i in shown + poked], int))
    print('POKE', tag, 'skin moved inward over bandanna:', len(shown), [(tuple(v[i].round(3)), round(s * 1000, 1)) for s, i in shown[:8]])
    print('POKE', tag, 'bandanna outside both skins:', len(poked), [(tuple(v[i].round(3)), round(s * 1000, 1)) for s, i in poked[:8]])
