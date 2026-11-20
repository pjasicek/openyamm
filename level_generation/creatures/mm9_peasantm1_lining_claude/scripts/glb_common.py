"""Shared helpers for the PeasantM1 lining (copied from PeasantM1d) (GLB level): LOD0 primitives, welded topology, pieces, images, bind-pose joints."""
import io, sys
from collections import defaultdict
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parent))
import glbpack as G  # noqa: E402
import bglbio  # noqa: E402

NODE = 'PeasantM1'


def load(path):
    doc, binary = G.read(path)
    nd = next(n for n in doc['nodes'] if n.get('name') == NODE and 'mesh' in n)
    prims = {}
    for p in doc['meshes'][nd['mesh']]['primitives']:
        a = p['attributes']; name = doc['materials'][p['material']]['name']
        prims[name] = dict(prim=p, P=G.acc(doc, bytes(binary), a['POSITION']).astype(np.float64),
                           N=G.acc(doc, bytes(binary), a['NORMAL']).astype(np.float64),
                           UV=G.acc(doc, bytes(binary), a['TEXCOORD_0']).astype(np.float64),
                           J=G.acc(doc, bytes(binary), a['JOINTS_0']).astype(np.int64),
                           W=G.acc(doc, bytes(binary), a['WEIGHTS_0']).astype(np.float64),
                           T=G.acc(doc, bytes(binary), p['indices']).reshape(-1, 3).astype(np.int64))
    skin = doc['skins'][nd['skin']]
    jn = [doc['nodes'][j]['name'] for j in skin['joints']]
    return doc, binary, nd, prims, jn


def image(doc, binary, tex_index):
    im = doc['images'][doc['textures'][tex_index]['source']]; v = doc['bufferViews'][im['bufferView']]
    o = v.get('byteOffset', 0)
    return np.asarray(Image.open(io.BytesIO(bytes(binary[o:o + v['byteLength']]))).convert('RGBA'), np.float64) / 255


def texel(img, uv):
    uv = np.atleast_2d(uv); h, w = img.shape[:2]
    return img[np.clip((uv[:, 1] % 1 * h).astype(int), 0, h - 1), np.clip((uv[:, 0] % 1 * w).astype(int), 0, w - 1)]


def weld(P):
    _, inv = np.unique(P.round(6), axis=0, return_inverse=True)
    return inv.ravel()


def pieces(TT, n):
    par = np.arange(n)
    def f(x):
        while par[x] != x:
            par[x] = par[par[x]]; x = par[x]
        return x
    for t in TT:
        a = f(t[0]); par[f(t[1])] = a; par[f(t[2])] = a
    return np.array([f(x) for x in range(n)])


def boundary_loops(TT):
    ec = defaultdict(list)
    for fi, t in enumerate(TT):
        for i in range(3):
            ec[tuple(sorted((t[i], t[(i + 1) % 3])))].append(fi)
    bnd = {e: fs[0] for e, fs in ec.items() if len(fs) == 1}
    adj = defaultdict(list)
    for a, b in bnd:
        adj[a].append(b); adj[b].append(a)
    seen, loops = set(), []
    for e in bnd:
        if e[0] in seen:
            continue
        st, comp = [e[0]], []
        while st:
            x = st.pop()
            if x in seen:
                continue
            seen.add(x); comp.append(x); st += adj[x]
        loops.append(sorted(comp))
    return loops, bnd, ec


def joint_segments(doc, binary, nd):
    skin = doc['skins'][nd['skin']]
    m = G.acc(doc, bytes(binary), skin['inverseBindMatrices']).astype(np.float64).reshape(-1, 4, 4)
    world = np.array([np.linalg.inv(x.T) for x in m])          # column-major glTF -> row-major
    head = world[:, :3, 3]
    joints = skin['joints']; idx = {j: k for k, j in enumerate(joints)}
    tail = head.copy()
    for k, j in enumerate(joints):
        kids = [idx[c] for c in doc['nodes'][j].get('children', []) if c in idx]
        if kids:
            tail[k] = head[kids].mean(0) if len(kids) > 1 else head[kids[0]]
    return head, tail
