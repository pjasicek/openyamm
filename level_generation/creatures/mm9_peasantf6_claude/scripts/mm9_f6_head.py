"""Dump MM9 PeasantF6 and PeasantF5 head-region geometry in our Blender frame (x, -z, y of the ABC, scale 0.0256): vertices, triangles,
dominant bone, distance to the other model. Writes work/mm9_f6_head.npz."""
import sys
from pathlib import Path
R = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(R / 'tools/mm9_import_discovery'))
from convert_abc_model import read_abc
import numpy as np
from scipy.spatial import cKDTree
D = R / 'mm9/extracted/MODELS/MODELS'
def load(name):
    m = read_abc(D / name); P, B, T = [], [], []
    for pc in m.pieces:
        if pc.name.lower().startswith('ngon'): continue
        l = pc.lods[0]; base = len(P)
        for v in l.vertices:
            P.append(v.position); w = max(v.weights, key=lambda w: w.bias); B.append(m.nodes[w.node_index].name)
        for f in l.faces: T.append([base + fv.vertex_index for fv in f.vertices][:3])
    P = np.array(P, float) * 0.0256; P = np.c_[P[:, 0], -P[:, 2], P[:, 1]]
    return P, np.array(B), np.array(T, int)
P6, B6, T6 = load('PEASANTF6.abc'); P5, B5, T5 = load('PEASANTF5.abc')
d6 = cKDTree(P5).query(P6)[0]; d5 = cKDTree(P6).query(P5)[0]
np.savez(R / 'level_generation/creatures/mm9_peasantf6_claude/work/mm9_f6_head.npz', P6=P6, B6=B6, T6=T6, d6=d6, P5=P5, B5=B5, T5=T5, d5=d5)
for bone in ('FHP Head', 'FHP Ponytail11', 'FHP Ponytail12', 'FHP Neck'):
    m = (B6 == bone)
    if m.any():
        print('F6', bone, m.sum(), 'z', P6[m, 2].min().round(3), P6[m, 2].max().round(3), 'x', P6[m, 0].min().round(3), P6[m, 0].max().round(3), 'y', P6[m, 1].min().round(3), P6[m, 1].max().round(3))
    m = (B5 == bone)
    if m.any():
        print('F5', bone, m.sum(), 'z', P5[m, 2].min().round(3), P5[m, 2].max().round(3), 'x', P5[m, 0].min().round(3), P5[m, 0].max().round(3), 'y', P5[m, 1].min().round(3), P5[m, 1].max().round(3))
# ear tips: the head vertices furthest from the midline
h = B6 == 'FHP Head'; i = np.argsort(-np.abs(P6[h, 0]))[:6]; print('F6 widest head verts', P6[h][i].round(3))
