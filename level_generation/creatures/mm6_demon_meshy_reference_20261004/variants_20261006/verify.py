"""Audit returned triangle/UV correspondence and unchanged animated source data before installation."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from scipy.spatial import cKDTree

stage = Path(__file__).resolve().parent
sys.path.insert(0, str(stage.parents[3] / 'tools'))
from build_actor_lods import accessor_bytes, read_glb


def corners(path):
    document, binary = read_glb(path)
    arrays = []
    for primitive in document['meshes'][0]['primitives']:
        def accessor(index):
            item = document['accessors'][index]
            dtype = {5123: '<u2', 5125: '<u4', 5126: '<f4'}[item['componentType']]
            return np.frombuffer(accessor_bytes(document, binary, index), dtype).reshape(item['count'], -1)
        values = np.column_stack([accessor(primitive['attributes']['POSITION']),
                                  accessor(primitive['attributes']['TEXCOORD_0'])])
        arrays.append(values[accessor(primitive['indices']).ravel()])
    return np.concatenate(arrays)


def triangles(indices):
    return Counter(min(tuple(np.roll(t, k)) for k in range(3)) for t in indices.reshape(-1, 3))


source = corners(stage / 'demon_neutral_upload.glb')
unique, inverse = np.unique(source, axis=0, return_inverse=True)
tree = cKDTree(unique)
center = (source[:, :3].min(0) + source[:, :3].max(0)) / 2
scale = (source[:, 1].max() - source[:, 1].min()) / 2
report = {}
for variant in ('demon_b', 'demon_c'):
    returned = corners(stage.parent / f'meshy/{variant}_texture_v1/model_urls_glb.glb')
    assert returned.shape == source.shape
    returned[:, :3] = returned[:, :3] * scale + center
    distance, indices = tree.query(returned)
    assert distance.max() < 2e-6, (variant, distance.max())
    assert triangles(indices) == triangles(inverse), variant
    report[variant] = {'position_uv_max_error': float(distance.max()), 'triangles_and_winding_match': True}
for name in ('mm6_demon_runtime.glb', 'mm6_demon_animated.glb'):
    original, binary = read_glb(stage.parent / 'attack_windup_20261006' / name)
    delivered, new_binary = read_glb(stage / name)
    assert new_binary[:len(binary)] == binary
    for key in ('nodes', 'skins', 'animations', 'accessors'):
        assert original[key] == delivered[key], key
    for before, after in zip(original['meshes'], delivered['meshes']):
        cleaned = json.loads(json.dumps(after))
        for primitive in cleaned['primitives']:
            primitive.pop('extensions', None)
        assert cleaned == before
    assert all(image['mimeType'] == 'image/png' for image in delivered['images'][len(original['images']):])
    if name == 'mm6_demon_runtime.glb':
        assert all(image['mimeType'] == 'image/png' for image in delivered['images'])
    assert len(delivered['extensions']['KHR_materials_variants']['variants']) == 3
    report[name] = {'rig_clips_lods_uvs_unchanged': True,
                    'sha256': hashlib.sha256((stage / name).read_bytes()).hexdigest()}
(stage / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
