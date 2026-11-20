"""Prepare every active MM6-8 outdoor minimap from map geometry and mounted textures."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image
import yaml

HERE = Path(__file__).resolve().parent
DEFAULT_HERE = HERE
ROOT = HERE.parents[1]
HUD = ROOT/'level_generation/ui/hud_inventory'
sys.path.insert(0, str(ROOT/'util'))
from map_export import parse_odm_file


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2)+'\n')
    temporary.replace(path)


def descriptor(tile, world, master, banks):
    assert 0 <= tile < 234, ('Invalid terrain tile', tile)
    if tile < 90:
        return tile + ([0, 450, 630][master] if world == 'mm8' and tile and master < 3 else 0)
    return tile if master >= 3 else banks[(tile-90)//36]+(tile-90)%36


def texture_index(world):
    enhanced, native = {}, {}
    # Match mounted texture lookup: active world, engine, then the other world packages. The native BMPs and the
    # x2 surface PNGs are source art in assets_source, under each package's same relative path.
    names = [Path('worlds')/world, Path('engine')] + [Path('worlds')/p.name for p in
                                                     sorted((ROOT/'assets_dev/worlds').iterdir())
                                                     if p.is_dir() and p.name != world]
    for package in [root/name for name in names for root in (ROOT/'assets_dev', ROOT/'assets_source')]:
        for kind in ['terrain', 'textures']:
            for suffix, index in [('_x2', enhanced), ('', native)]:
                directory = package/(kind+suffix)
                if directory.exists():
                    for path in sorted(directory.iterdir()):
                        if path.suffix.lower() in ['.png', '.bmp']:
                            index.setdefault(path.stem.lower(), path)
    for name, path in native.items():
        enhanced.setdefault(name, path)
    return enhanced, native


def main():
    global HERE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--world', choices=['mm6', 'mm7', 'mm8'])
    parser.add_argument('--workspace', type=Path, default=DEFAULT_HERE, help='New revision directory')
    args = parser.parse_args()
    HERE = args.workspace.resolve()
    assert not (HERE/'accepted.json').exists(), 'Published revision is immutable; prepare a new revision directory'
    accepted = json.loads((HUD/'accepted_icons.json').read_text())['records']
    tables = ROOT/'assets_dev/engine/data_tables'
    water_table = tables/'hw_water_textures.txt'
    aliases = dict(row.split('\t')[:2] for row in water_table.read_text().splitlines()[1:] if '\t' in row)
    stats = [row.split('\t') for row in (tables/'map_stats.txt').read_text().splitlines()[3:]]
    names = {row[2].lower(): row[1] for row in stats if len(row) > 2}
    records = []
    for world in ['mm6', 'mm7', 'mm8']:
        if args.world and world != args.world:
            continue
        enhanced, native = texture_index(world)
        table_path = tables/('terrain_tile_data'+{'mm6':'_3', 'mm7':'_2', 'mm8':''}[world]+'.txt')
        table = {int(row.split('\t')[0]): row.split('\t')[1].lower() for row in table_path.read_text().splitlines()[1:]}
        presentation = ROOT/'assets_dev/worlds'/world/'ui/maps/catalog.yml'
        assert not presentation.exists(), 'Implement explicit non-default presentation bounds before rendering '+world
        for map_path in sorted((ROOT/'assets_dev/worlds'/world/'maps').glob('*.odm')):
            stem = map_path.stem
            output = HERE/'maps'/world/stem
            target = f'worlds-{world}--icons--{stem}.bmp'
            record = dict(world=world, map=map_path.name, name=names.get(map_path.name, stem), target=target,
                          directory=str(output.relative_to(HERE)),x2_size=accepted[target]['x2_size'])
            records.append(record)
            output.mkdir(parents=True, exist_ok=True)
            data = parse_odm_file(map_path)['payload']
            original = ROOT/'assets_legacy/icons_20260926/worlds'/world/'icons'/(stem+'.bmp')
            prior = accepted[target]
            assert sha(ROOT/prior['runtime_output_path']) == prior['sha256'], target
            native_size = list(Image.open(original).size)
            assert native_size in [[512,512],[512,510]], (target,native_size)
            assert prior['x2_size'] == [n*2 for n in native_size]
            Image.open(original).convert('RGB').save(output/'original.png')
            Image.open(prior['artifact']).convert('RGB').save(output/'previous.png')
            sources = {str(path.relative_to(ROOT)): sha(path) for path in [original, map_path, table_path, water_table]}

            def texture(name):
                path = enhanced[name.lower()]
                sources[str(path.relative_to(ROOT))] = sha(path)
                return Image.open(path).convert('RGBA')

            water_name = aliases[{'mm6':'6wtrtyl', 'mm7':'7wtrtyl', 'mm8':'wtrtyl'}[world]]+'000'
            water = texture(water_name)
            tiles, mapping = {}, {}
            for tile in sorted(set(data['tile_map'])):
                index = descriptor(tile, world, data['master_tile'], data['tile_set_lookup_indices'])
                name = table[index]
                resolved = aliases[name]+'000' if name in aliases else name
                image = texture(resolved)
                pixels = np.array(image)
                magenta = (pixels[:, :, 0] >= 248) & (pixels[:, :, 1] <= 8) & (pixels[:, :, 2] >= 248)
                cyan = (pixels[:, :, 0] <= 8) & (pixels[:, :, 1] >= 248) & (pixels[:, :, 2] >= 248)
                pixels[magenta | cyan, 3] = 0
                image = Image.alpha_composite(water.resize(image.size), Image.fromarray(pixels))
                tiles[tile] = np.array(image.convert('RGB').resize((32, 32), Image.Resampling.LANCZOS))
                mapping[tile] = dict(descriptor=index, name=name, texture=resolved)
            atlas = np.zeros((4096, 4096, 3), np.uint8)
            for y in range(128):
                for x in range(128):
                    atlas[y*32:(y+1)*32, x*32:(x+1)*32] = tiles[data['tile_map'][y*128+x]]
            Image.fromarray(atlas).save(output/'terrain.png')
            materials = {}
            for name in sorted({face['texture_name'].lower() for model in data['bmodels'] for face in model['faces']
                                if not face['attributes'] & 0x2000 and len(face['vertex_indices']) >= 3}):
                image = texture(name)
                native_path = native[name]
                sources[str(native_path.relative_to(ROOT))] = sha(native_path)
                cache = HERE/'textures'/world/(name+'.png')
                cache.parent.mkdir(parents=True, exist_ok=True)
                image.save(cache)
                materials[name] = dict(path=str(cache), logical_size=list(Image.open(native_path).size))
            scene = dict(**record, height_map=data['height_map'], tile_map=data['tile_map'], bmodels=data['bmodels'],
                         materials=materials, terrain=str(output/'terrain.png'), tile_mapping=mapping,
                         master_tile=data['master_tile'], banks=data['tile_set_lookup_indices'])
            save(output/'scene.json', scene)
            save(output/'sources.json', dict(sources=sources, previous=prior, scene_sha256=sha(output/'scene.json'),
                terrain_sha256=sha(output/'terrain.png'), texture_cache={m['path']: sha(m['path']) for m in materials.values()}))
            print(world, stem, len(materials), 'materials', len(data['bmodels']), 'models', flush=True)
    worlds = {world: sum(row['world'] == world for row in records) for world in ['mm6', 'mm7', 'mm8']}
    expected = {'mm6':15, 'mm7':13, 'mm8':14}
    assert worlds == {world: count if not args.world or world == args.world else 0 for world,count in expected.items()}
    save(HERE/'scope.json', dict(records=records, count=len(records), worlds=worlds,
        exclusions='Indoor maps use vector automaps; MM9 has a separate native presentation pipeline.'))


if __name__ == '__main__':
    main()
