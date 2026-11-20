"""Shared helper: LOD0 Body positions/indices/joints/weights of a GLB (first primitive set of the 'Body' node)."""
import json, struct, sys
import numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, accessor_bytes  # noqa: E402
TY = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}
def arr(doc, b, i):
    a = doc['accessors'][i]; return np.frombuffer(accessor_bytes(doc, b, i), TY[a['componentType']]).reshape(-1, NC[a['type']]) if NC[a['type']] > 1 else np.frombuffer(accessor_bytes(doc, b, i), TY[a['componentType']])
def body(path, node='Body'):
    doc, b = read_glb(Path(path)); n = next(x for x in doc['nodes'] if x.get('name') == node)
    out = {k: [] for k in ('pos', 'idx', 'uv', 'j', 'w')}; off = 0
    for p in doc['meshes'][n['mesh']]['primitives']:
        P = arr(doc, b, p['attributes']['POSITION']); out['pos'].append(P); out['idx'].append(arr(doc, b, p['indices']).reshape(-1, 3) + off)
        out['uv'].append(arr(doc, b, p['attributes']['TEXCOORD_0'])); out['j'].append(arr(doc, b, p['attributes']['JOINTS_0'])); out['w'].append(arr(doc, b, p['attributes']['WEIGHTS_0'])); off += len(P)
    r = {k: np.concatenate(v) for k, v in out.items()}
    r['joint_names'] = [doc['nodes'][i]['name'] for i in doc['skins'][n['skin']]['joints']]
    return r
