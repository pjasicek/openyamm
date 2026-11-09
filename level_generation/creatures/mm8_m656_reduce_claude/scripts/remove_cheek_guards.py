"""Remove the helmet's two cheek guards from every mesh of a Mercenary GLB (user review 2026-10-19: "I would remove
these from the helmet"). In the source mesh they are two separate 28-face pieces of the head set (work/face_info.npz
pieces 74 and 75), kept exactly by the reduction and kept as separate pieces by every colour and shadow LOD. A piece
of a mesh (vertices welded by position, so UV seams do not split it) is removed when all its bind-pose vertices lie in
one of the two boxes below (glTF axes: x, y up, z back; source bounds plus 18 mm, since the distant LODs drift; at most
40 faces). Unused vertices are dropped.
Usage: remove_cheek_guards.py in.glb out.glb"""
import sys
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from merge_head_material import read_glb, write_glb, accessor_array, append_accessor, compact

M = 0.018
BOXES = [((-0.096, 1.486, -0.107), (-0.056, 1.569, 0.047)), ((0.059, 1.486, -0.109), (0.100, 1.569, 0.048))]
src, dst = Path(sys.argv[1]), Path(sys.argv[2])
doc, binary = read_glb(src)
for mesh in doc['meshes']:
    for pr in mesh['primitives']:
        pos = accessor_array(doc, binary, pr['attributes']['POSITION']).astype(np.float64)
        tri = accessor_array(doc, binary, pr['indices']).reshape(-1, 3).astype(np.int64)
        _, weld = np.unique(np.round(pos / 1e-4).astype(np.int64), axis=0, return_inverse=True)
        weld = weld.ravel(); n = weld.max() + 1
        e = weld[np.concatenate([tri[:, [0, 1]], tri[:, [1, 2]]])]
        _, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
        piece = lab[weld[tri[:, 0]]]
        drop = np.zeros(len(tri), bool); found = []
        for lo, hi in BOXES:
            inside = np.all((pos >= np.array(lo) - M) & (pos <= np.array(hi) + M), axis=1)
            used = np.zeros(lab.max() + 1, bool); used[lab[weld]] = True
            bad = np.zeros(lab.max() + 1, bool); np.logical_or.at(bad, lab[weld], ~inside)
            hit = np.flatnonzero(used & ~bad)
            hit = [p for p in hit if 0 < (piece == p).sum() <= 40]
            assert len(hit) == 1, f"{mesh['name']}: expected one cheek guard piece in {lo}..{hi}, found {len(hit)}"
            drop |= piece == hit[0]; found.append(int((piece == hit[0]).sum()))
        keep = tri[~drop]; verts = np.unique(keep); remap = np.full(len(pos), -1); remap[verts] = np.arange(len(verts))
        for name, index in list(pr['attributes'].items()):
            values = accessor_array(doc, binary, index)[verts]
            pr['attributes'][name] = append_accessor(doc, binary, values, doc['accessors'][index], 34962)
        idx = remap[keep].ravel(); itype = 5123 if idx.max() < 65536 else 5125
        pr['indices'] = append_accessor(doc, binary, idx.astype(np.uint16 if itype == 5123 else np.uint32),
                                        {'componentType': itype, 'type': 'SCALAR'}, 34963)
        print('CHEEK', mesh['name'], 'removed', found, 'triangles', len(tri), '->', len(keep), 'vertices', len(pos), '->', len(verts))
write_glb(dst, *compact(doc, binary))
