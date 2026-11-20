"""Check the burn loader contract and prove the accepted non-burn content is unchanged."""
import copy
import hashlib
import io
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import read_glb, accessor_bytes
from merge_head_material import accessor_array


def digest(data):
    return hashlib.sha256(data).hexdigest()


def texture_bytes(doc, binary, index):
    image = doc['images'][doc['textures'][index]['source']]
    view = doc['bufferViews'][image['bufferView']]
    start = view.get('byteOffset', 0)
    return bytes(binary[start:start + view['byteLength']])


def non_burn_content(doc, binary):
    result = copy.deepcopy(doc)
    def accessor(index):
        meta = doc['accessors'][index]
        return {k: v for k, v in meta.items() if k not in ('bufferView', 'byteOffset')} | {
            'sha256': digest(accessor_bytes(doc, binary, index))}
    def textures(value):
        if isinstance(value, dict):
            if 'index' in value:
                index = value['index']
                value['index'] = digest(texture_bytes(doc, binary, index))
                sampler = doc['textures'][index].get('sampler')
                value['sampler'] = doc['samplers'][sampler] if sampler is not None else None
            else:
                for child in value.values():
                    textures(child)
        elif isinstance(value, list):
            for child in value:
                textures(child)
    for material in result['materials']:
        material.get('extras', {}).pop('openyamm_burn_map', None)
        textures(material)
    for mesh in result['meshes']:
        for primitive in mesh['primitives']:
            primitive['attributes'] = {k: accessor(v) for k, v in primitive['attributes'].items()}
            primitive['indices'] = accessor(primitive['indices'])
    for skin in result.get('skins', []):
        skin['inverseBindMatrices'] = accessor(skin['inverseBindMatrices'])
    for animation in result.get('animations', []):
        for sampler in animation['samplers']:
            for key in ('input', 'output'):
                sampler[key] = accessor(sampler[key])
    for key in ('accessors', 'bufferViews', 'buffers', 'images', 'textures', 'samplers'):
        result.pop(key, None)
    return result


def check_maps(doc, binary, cooked=False):
    covered = 0
    maps = set()
    for mesh in doc['meshes']:
        for primitive in mesh['primitives']:
            assert 'JOINTS_0' in primitive['attributes']
            indices = {primitive['material']} | {m['material'] for m in
                primitive.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', [])}
            burn = {doc['materials'][i]['extras']['openyamm_burn_map']['index'] for i in indices}
            assert len(burn) == 1, (mesh['name'], 'variants must share the burn map')
            maps |= burn
            if cooked:
                index = primitive['attributes']['_BURN_ORDER']
                order = accessor_array(doc, binary, index)
                if doc['accessors'][index].get('normalized'):
                    order = order.astype(float) / np.iinfo(order.dtype).max
                assert len(order) == doc['accessors'][primitive['attributes']['POSITION']]['count']
                assert np.isfinite(order).all() and order.min() >= 0 and order.max() <= 1
            covered += 1
    if not cooked:
        for index in maps:
            image = np.asarray(Image.open(io.BytesIO(texture_bytes(doc, binary, index))).convert('RGB'))
            assert image[..., 0].min() < 255 and image[..., 0].max() > 0
    return {'primitives_including_shadows': covered, 'materials': len(doc['materials']), 'burn_maps': len(maps)}


def main():
    report = {'models': {}, 'unchanged_rigid_attachments': []}
    backup = P / 'work/before_burn_20261024/export'
    runtime = P.parents[2] / 'output/hesper_stage/assets_editor_dev/worlds/hesper/models'
    for path in sorted((P / 'export').glob('*.glb')):
        old = backup / path.name
        if path.name not in ('hes_overseer.glb', 'hes_kreegan_winged.glb'):
            assert path.read_bytes() == old.read_bytes(), path
            report['unchanged_rigid_attachments'].append(path.name)
            continue
        doc, binary = read_glb(path)
        previous, pb = read_glb(old)
        assert non_burn_content(doc, binary) == non_burn_content(previous, pb), (path, 'non-burn content changed')
        cooked, cb = read_glb(runtime / path.name)
        report['models'][path.name] = {'source_sha256': digest(path.read_bytes()),
            'runtime_sha256': digest((runtime / path.name).read_bytes()),
            'source': check_maps(doc, binary), 'cooked': check_maps(cooked, cb, cooked=True),
            'non_burn_content_preserved': True}
    assert (P / 'integration/actors.yml').read_bytes() == (backup.parent / 'integration/actors.yml').read_bytes()
    (P / 'review/burn_validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
