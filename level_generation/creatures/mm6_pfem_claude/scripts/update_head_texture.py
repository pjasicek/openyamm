"""Replace only the head half of a merged GLB's colour atlas; verify all model/animation data is unchanged."""
from pathlib import Path
import argparse
import copy
import hashlib
import io
import json
import sys
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[2] / 'tools'))
import merge_head_material as G

def update(source, target):
    before, original_binary = G.read_glb(source)
    doc, binary = copy.deepcopy(before), bytearray(original_binary)
    head = Image.open(ROOT / 'textures_v3/pfem_head_basecolor_repaired.png').convert('RGB')
    assert head.size == (1024, 1024)
    slots = {m['pbrMetallicRoughness']['baseColorTexture']['index'] for m in doc['materials']}
    for index in slots:
        atlas, _ = G.image_of(doc, binary, index)
        assert atlas.size == (2080, 1024)
        body = atlas.crop((0, 0, 1024, 1024))
        replacement = G.Atlas((1024, 1024), (1024, 1024)).compose(body, head.convert(atlas.mode))
        assert np.array_equal(np.asarray(body), np.asarray(replacement)[:, :1024])
        stream = io.BytesIO()
        replacement.save(stream, 'PNG', optimize=True)
        binary.extend(b'\0' * (-len(binary) % 4))
        doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(stream.getvalue())})
        binary.extend(stream.getvalue())
        doc['images'][doc['textures'][index]['source']]['bufferView'] = len(doc['bufferViews']) - 1
    doc, binary = G.compact(doc, binary)
    for key in ['nodes', 'skins', 'animations', 'meshes', 'scenes']:
        assert before[key] == doc[key], key
    for index in range(len(before['accessors'])):
        assert np.array_equal(G.accessor_array(before, original_binary, index), G.accessor_array(doc, binary, index)), index
    for old, new in zip(before['materials'], doc['materials']):
        for key in ['normalTexture', 'pbrMetallicRoughness', 'extras']:
            assert old[key] == new[key], key
    G.write_glb(target, doc, binary)
    return {'source': str(source), 'target': str(target),
            'before_sha256': hashlib.sha256(source.read_bytes()).hexdigest() if source != target else None,
            'after_sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
            'accessors_unchanged': len(before['accessors']),
            'geometry_uvs_skin_weights_rig_clips_lods_unchanged': True,
            'body_base_colour_unchanged': True}

if __name__ == '__main__':
    args = argparse.ArgumentParser()
    args.add_argument('source', type=Path)
    args.add_argument('target', type=Path)
    args.add_argument('--report', type=Path)
    opt = args.parse_args()
    result = update(opt.source, opt.target)
    if opt.report:
        opt.report.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
