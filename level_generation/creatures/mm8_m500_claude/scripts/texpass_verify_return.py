"""Check a Meshy retexture return against its upload: same triangles with the same UVs (sorted UV triples, 1e-4),
and positions equal up to Meshy's uniform recenter/scale. Usage: texpass_verify_return.py <upload.glb> <return.glb>"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from texpass_glb import floats, np, read_glb, source_faces  # noqa: E402


def triangles(path):
    doc, binary = read_glb(Path(path))
    out_uv, out_pos = [], []
    for mesh in doc['meshes']:
        for p in mesh['primitives']:
            f = source_faces(doc, binary, p)
            out_uv.append(floats(doc, binary, p['attributes']['TEXCOORD_0'])[f])
            out_pos.append(floats(doc, binary, p['attributes']['POSITION'])[f])
    return np.concatenate(out_uv), np.concatenate(out_pos)


def keys(uv, pos):
    order = np.lexsort((uv[:, :, 1], uv[:, :, 0]))
    uv = np.take_along_axis(uv, order[:, :, None], 1)
    pos = np.take_along_axis(pos, order[:, :, None], 1)
    k = np.round(uv.reshape(len(uv), -1), 4)
    o = np.lexsort(k.T[::-1])
    return k[o], pos[o]


(ua, pa), (ub, pb) = triangles(sys.argv[1]), triangles(sys.argv[2])
ka, qa = keys(ua, pa)
kb, qb = keys(ub, pb)
print('triangles', len(ka), len(kb))
same = len(ka) == len(kb) and np.abs(ka - kb).max() < 2e-4
print('uv triples equal:', same, 'max diff', float(np.abs(ka - kb).max()) if len(ka) == len(kb) else None)
if same:
    a, b = qa.reshape(-1, 3), qb.reshape(-1, 3)
    a0, b0 = a - a.mean(0), b - b.mean(0)
    s = np.sqrt((b0 ** 2).sum() / (a0 ** 2).sum())
    print('uniform scale', round(float(s), 6), 'position residual max', float(np.abs(a0 * s - b0).max() / s))
