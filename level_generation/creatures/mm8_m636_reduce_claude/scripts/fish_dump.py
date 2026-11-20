#!/usr/bin/env python3
"""Fish template of the installed school: the twelve fish of every LOD are exact similarity copies of Fish00 (same
vertex order, triangles, UVs and weights; joints offset by 5 per fish, scale 1.0 down to 0.308). Dumps Fish00 of
LOD0 (glTF vertices and the welded MeshLab input work/mesh_in.npz: positions, faces, wedge UVs) and each fish's
similarity transform (scale, rotation, offset; max fit error) -> work/fish.npz.
Usage: fish_dump.py <school glb>"""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parents[2] / 'tools'))
from build_actor_lods import read_glb, accessor_bytes  # noqa: E402


def acc(d, b, i):
    a = d['accessors'][i]; ct = {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8}[a['componentType']]
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
    r = np.frombuffer(accessor_bytes(d, b, i), ct)
    return (r.reshape(a['count'], n) if n > 1 else r).copy()


def lod_arrays(d, b, mesh):
    p = d['meshes'][mesh]['primitives'][0]; at = p['attributes']
    return {k: acc(d, b, at[a]) for k, a in (('P', 'POSITION'), ('N', 'NORMAL'), ('UV', 'TEXCOORD_0'),
                                               ('J', 'JOINTS_0'), ('W', 'WEIGHTS_0'))} | {'I': acc(d, b, p['indices']).reshape(-1, 3)}


def split_fish(a):
    fish = (a['J'][np.arange(len(a['J'])), a['W'].argmax(1)].astype(int) - 1) // 5
    return fish


def similarity(a, c):
    ma, mc = a.mean(0), c.mean(0); A, C = a - ma, c - mc
    s = np.sqrt((C ** 2).sum() / (A ** 2).sum())
    U, _, Vt = np.linalg.svd(A.T @ C); R = U @ Vt
    if np.linalg.det(R) < 0:
        U[:, -1] *= -1; R = U @ Vt
    t = mc - s * ma @ R
    return s, R, t, float(np.abs(s * a @ R + t - c).max())


if __name__ == '__main__':
    d, b = read_glb(Path(sys.argv[1])); a = lod_arrays(d, b, 0); fish = split_fish(a)
    n = int((fish == 0).sum()); nt = len(a['I']) // 12
    f0 = {k: v[:n] for k, v in a.items() if k != 'I'}; I0 = a['I'][:nt]
    assert I0.max() < n and np.all(fish[:n] == 0)
    S, R, T = [], [], []
    for k in range(12):
        s, r, t, e = similarity(f0['P'], a['P'][fish == k]); S.append(s); R.append(r); T.append(t)
        assert e < 1e-5, (k, e)
        assert np.array_equal(a['I'][k * nt:(k + 1) * nt] - k * n, I0)
    # weld positions for MeshLab (UV seams become wedge UVs)
    key = np.round(f0['P'] / 1e-7).astype(np.int64)
    _, weld, inv = np.unique(key, axis=0, return_index=True, return_inverse=True); inv = inv.reshape(-1)
    faces = inv[I0]; wuv = f0['UV'][I0].reshape(-1, 2)
    jloc = np.where(f0['W'] > 0, f0['J'], 0)
    np.savez(HERE / 'work' / 'mesh_in.npz', verts=f0['P'][weld].astype(np.float64), faces=faces, wuv=wuv,
             protect=np.zeros(len(faces)))
    np.savez(HERE / 'work' / 'fish.npz', P=f0['P'], N=f0['N'], UV=f0['UV'], J=f0['J'], W=f0['W'], I=I0, weld=inv,
             S=np.array(S), R=np.array(R), T=np.array(T))
    print('FISH', n, 'verts', nt, 'tris;', len(weld), 'welded; scales', np.round(S, 3).tolist())
