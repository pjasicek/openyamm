"""Meshy returns keep the uploaded UVs (enable_original_uv): every upload corner must find a returned corner at the
same position (after the return's scale/centre fit) with the same UV. Prints PARITY per set; fails over 0.2 % changed."""
import os, bpy
import numpy as np
from mathutils import Vector, kdtree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True)


def load(path):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=path)
    o = next(x for x in bpy.data.objects if x not in before and x.type == 'MESH'); return o


for label in ('body', 'head'):
    up = load(os.path.join(HERE, 'work', f'{label}_upload.glb'))
    ret = load(os.path.join(HERE, 'meshy', f'{label}_retexture_r55', 'model_urls_glb.glb'))
    U = np.array([up.matrix_world @ v.co for v in up.data.vertices]); S = np.array([ret.matrix_world @ v.co for v in ret.data.vertices])
    scale = np.ptp(U, axis=0).max() / np.ptp(S, axis=0).max(); S = S * scale + (U.max(0) + U.min(0)) / 2 - (S.max(0) + S.min(0)) / 2 * scale
    tree = kdtree.KDTree(len(ret.data.loops)); ruv = ret.data.uv_layers.active.data
    for li, loop in enumerate(ret.data.loops):
        tree.insert(Vector(S[loop.vertex_index]), li)
    tree.balance()
    uuv = up.data.uv_layers.active.data; unmatched = changed = count = 0; worst = 0.0
    for li, loop in enumerate(up.data.loops):
        near = tree.find_range(Vector(U[loop.vertex_index]), 1e-4)
        if not near:
            unmatched += 1; continue
        d = min((ruv[j].uv - uuv[li].uv).length for _, j, _ in near); worst = max(worst, d); count += 1
        changed += d > 1e-4
    print('PARITY', label, 'corners', count, 'unmatched', unmatched, 'changed', changed, 'max uv error', round(worst, 6))
    assert changed / max(count, 1) < .002 and unmatched / max(count, 1) < .002, label
