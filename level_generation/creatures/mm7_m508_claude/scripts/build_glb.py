"""export/mm7_*.glb: the installed MM8 model with MM7 variant names, material names and region ramps (batch M).

scripts/project.json "build" lists each output: the MM8 source in assets_source/worlds/mm8/models/, the output name,
variant renames, material renames and, for a model with region ramps, textures/<stem>_ramps.json (variant -> ramps).
Only glTF JSON changes; a model that needs no change (same art and palette, no variants) is copied byte for byte.
The script asserts that the binary chunk (geometry, skin, clips, LODs, images) is
byte-identical to the source and that nothing else in the JSON changed, and prints both hashes.
"""
import copy
import hashlib
import json
import shutil
import sys
from pathlib import Path

P = Path(__file__).resolve().parents[1]
REPO = P.parents[2]
sys.path.insert(0, str(P.parent / 'claude_shared'))
import region_variants as RV  # noqa: E402

MODELS = REPO / 'assets_source/worlds/mm8/models'


def variant_names(doc):
    return [v['name'] for v in doc.get('extensions', {}).get('KHR_materials_variants', {}).get('variants', [])]


def build(entry):
    source = MODELS / entry['source']
    doc, binary = RV.read_glb(source)
    original = copy.deepcopy(doc)
    renames = entry.get('variants', {})
    names = variant_names(doc)
    assert sorted(names) == sorted(renames), (names, renames)
    if names:
        doc['extensions']['KHR_materials_variants']['variants'] = [{'name': renames[name]} for name in names]
    ramps = json.loads((P / entry['ramps']).read_text())['materials'][0]['ramps'] if entry.get('ramps') else None
    # Which variant each material serves, from the primitives' variant mappings.
    serves = {}
    for mesh in doc['meshes']:
        for primitive in mesh['primitives']:
            for mapping in primitive.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', []):
                for index in mapping['variants']:
                    serves.setdefault(mapping['material'], set()).add(renames[names[index]])
    for index, material in enumerate(doc['materials']):
        new_name = entry.get('materials', {}).get(material['name'])
        if new_name:
            material['name'] = new_name
        if ramps is not None and 'openyamm_region_ramps' in material.get('extras', {}):
            (variant,) = serves[index]
            assert len(material['extras']['openyamm_region_ramps']) == len(ramps[variant])
            material['extras']['openyamm_region_ramps'] = ramps[variant]
    # Nothing but variant names, material names and ramps may differ from the source.
    stripped = [copy.deepcopy(original), copy.deepcopy(doc)]
    for d in stripped:
        d.get('extensions', {}).pop('KHR_materials_variants', None)
        for material in d['materials']:
            material.pop('name', None)
            material.get('extras', {}).pop('openyamm_region_ramps', None)
    assert stripped[0] == stripped[1], 'unexpected JSON change'
    out = P / 'export' / entry['out']
    if doc == original:
        shutil.copyfile(source, out)  # same art and palette: the MM8 file itself
    else:
        RV.write_glb(out, doc, binary)
    _, written = RV.read_glb(out)
    assert written == binary, 'binary chunk differs from the source'
    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    print(out.relative_to(REPO), digest, out.stat().st_size, 'source', entry['source'],
          hashlib.sha256(source.read_bytes()).hexdigest(), 'variants', variant_names(doc),
          'materials', [m['name'] for m in doc['materials']])
    return {'path': str(out.relative_to(P)), 'sha256': digest, 'bytes': out.stat().st_size,
            'source': str(source.relative_to(REPO)), 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
            'binary_chunk_identical': True}


def main():
    config = json.loads((P / 'scripts/project.json').read_text())
    results = [build(entry) for entry in config['build']]
    (P / 'review/export_record.json').write_text(json.dumps(results, indent=1) + '\n')


if __name__ == '__main__':
    sys.exit(main())
