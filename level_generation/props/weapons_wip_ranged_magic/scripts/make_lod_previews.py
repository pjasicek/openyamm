"""Material-preserving LOD preview files for Blender's importer (which ignores engine LOD extras)."""
import copy
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parents[2] / 'tools'))
from link_static_model_lods import read_glb, write_glb

folder = HERE / 'work/lod_preview'
folder.mkdir(exist_ok=True)
previews = {}
for icon in ['7item045', '7item046', 'item060']:
    path = HERE / f'work/exports/item_{icon}.glb'
    document, binary = read_glb(path)
    node_index = document['scenes'][0]['nodes'][0]
    base = document['nodes'][node_index]['mesh']
    lod = document['meshes'][base]['extras']['openyamm_lods'][0]
    previews[icon] = {}
    for label, index in [('base', base), ('lod1', lod)]:
        preview = copy.deepcopy(document)
        preview['nodes'][node_index]['mesh'] = index
        out = folder / f'{icon}_{label}.glb'
        write_glb(out, preview, binary.copy())
        assert read_glb(out)[0]['nodes'][node_index]['mesh'] == index
        previews[icon][label] = str(out)
(folder / 'previews.json').write_text(json.dumps(previews, indent=2) + '\n')
