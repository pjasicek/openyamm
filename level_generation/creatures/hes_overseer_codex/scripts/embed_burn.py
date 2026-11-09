"""Bake each final UV layout, embed burn maps, and share them across its tier materials.

Uses the shared baker and the MM6 demon embed_burn.py variant propagation pattern.
Run before material variants for new LOD0 builds, and after the final LOD UV bake.
Usage: embed_burn.py source.glb destination.glb
"""
import copy
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image

P = Path(__file__).resolve().parents[1]
SHARED = P.parent / 'claude_shared'
sys.path.insert(0, str(SHARED))
from burn_maps import add_burn_maps
from region_variants import read_glb, write_glb, _compact


def embed_burn(source, destination):
    source, destination = Path(source), Path(destination)
    doc, binary = read_glb(source)
    node = next(n for n in doc['nodes'] if 'mesh' in n and 'skin' in n)
    chain = [node['mesh']] + doc['meshes'][node['mesh']].get('extras', {}).get('openyamm_lods', [])
    work = P / 'work/burn_bake' / destination.stem
    textures = P / 'textures/burn' / destination.stem
    work.mkdir(parents=True, exist_ok=True)
    textures.mkdir(parents=True, exist_ok=True)
    maps = {}
    for level, mesh_index in enumerate(chain):
        bake = copy.deepcopy(doc)
        next(n for n in bake['nodes'] if n.get('name') == node['name'])['mesh'] = mesh_index
        temporary = work / f'lod{level}.glb'
        bake['meshes'][mesh_index]['primitives'] = [p for p in bake['meshes'][mesh_index]['primitives']
            if not bake['materials'][p['material']]['name'].startswith('OV_Glow')]
        write_glb(temporary, bake, binary)
        names = [doc['materials'][p['material']]['name'] for p in doc['meshes'][mesh_index]['primitives']]
        prefix = textures / f'lod{level}'
        command = [sys.executable, str(SHARED / 'bake_burn_maps.py'), str(temporary), str(prefix),
                   '--node', node['name'], '--size', str([1024, 1024, 512, 256][level]),
                   '--ignite', 'B_Head', 'B_Wing_L_Finger1', 'B_Wing_L_Finger2', 'B_Wing_L_Finger3',
                   'B_Wing_R_Finger1', 'B_Wing_R_Finger2', 'B_Wing_R_Finger3']
        for index, name in enumerate(names):
            if not name.startswith('OV_Glow'):
                command += ['--material', f'{name}=p{index}']
        subprocess.run(command, check=True)
        stats = json.loads(Path(f'{prefix}_burn.json').read_text())
        for index, name in enumerate(names):
            path = Path(f'{prefix}_p{index}_burn.png')
            if name.startswith('OV_Glow'):
                # The fitted glow strips have a single UV; burn that small emitter together halfway through.
                Image.new('RGB', (4, 4), (128, 0, 0)).save(path)  # 4x4: a 1x1 map cooks without the mips its sampler wants
                stats['maps'][f'p{index}'] = {'uniform_emitter_order': 128 / 255}
            else:
                assert stats['maps'][f'p{index}']['covered_texels'] > 0, name
            maps.setdefault(name, path)
        Path(f'{prefix}_burn.json').write_text(json.dumps(stats, indent=2) + '\n')
    embedded = work / 'embedded.glb'
    add_burn_maps(source, embedded, maps)
    doc, binary = read_glb(embedded)
    for mesh in doc['meshes']:
        for primitive in mesh['primitives']:
            burn = doc['materials'][primitive['material']]['extras']['openyamm_burn_map']
            for mapping in primitive.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', []):
                doc['materials'][mapping['material']].setdefault('extras', {})['openyamm_burn_map'] = dict(burn)
    assert all('openyamm_burn_map' in m.get('extras', {}) for m in doc['materials'])
    write_glb(destination, *_compact(doc, binary))
    print(f'BURN_MAPS {destination.name}: {len(maps)} maps, {len(doc["materials"])} materials', flush=True)


if __name__ == '__main__':
    embed_burn(*sys.argv[1:])
