"""Prepare a New Sorpigal minimap comparison without changing accepted assets."""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OUT = HERE / 'new_sorpigal'
sys.path.insert(0, str(ROOT / 'util'))
from map_export import parse_odm_file


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for folder in ['esrgan_input', 'esrgan_raw', 'esrgan_anime_raw', 'materials']:
        (OUT / folder).mkdir(exist_ok=True)
    native = ROOT / 'assets_legacy/icons_20260926/worlds/mm6/icons/oute3.bmp'
    runtime = ROOT / 'assets_dev/worlds/mm6/icons_x2/oute3.bmp'
    original = Image.open(native).convert('RGB')
    assert original.size == (512, 512)
    original.save(OUT / 'original.png')
    Image.open(runtime).convert('RGB').save(OUT / 'installed.png')
    original.resize((1024, 1024), Image.Resampling.NEAREST).save(OUT / 'original_x2.png')
    original.resize((1024, 1024), Image.Resampling.LANCZOS).save(OUT / 'lanczos_x2.png')
    # A mild, separately labelled dither-reduction trial; no resampling/warping.
    smoothed = Image.blend(original, original.filter(ImageFilter.MedianFilter(3)), .4)
    for name, image in [('faithful', original), ('light_denoise', smoothed)]:
        Image.fromarray(np.pad(np.array(image), ((16, 16), (16, 16), (0, 0)), mode='reflect')).save(
            OUT / 'esrgan_input' / (name + '.png'))

    map_path = ROOT / 'assets_dev/worlds/mm6/maps/oute3.odm'
    payload = parse_odm_file(map_path)['payload']
    tile_rows = [line.split('\t') for line in
                 (ROOT / 'assets_dev/engine/data_tables/terrain_tile_data_3.txt').read_text().splitlines()[1:]]
    palette = {}
    for tile in set(payload['tile_map']):
        assert tile < 234, f'Unmapped terrain tile {tile}'
        descriptor = tile if tile < 90 else payload['tile_set_lookup_indices'][(tile-90)//36] + (tile-90)%36
        palette[tile] = dict(texture=tile_rows[descriptor][1].lower())
    water_rows = (ROOT / 'assets_dev/engine/data_tables/hw_water_textures.txt').read_text().splitlines()[1:]
    water_aliases = dict(line.split('\t')[:2] for line in water_rows if '\t' in line)
    packages = [ROOT / 'assets_dev/worlds/mm6', ROOT / 'assets_dev/engine']
    textures, native_textures = {}, {}
    for package in packages:
        for kind in ['terrain', 'textures']:
            for suffix, index in [('_x2', textures), ('', native_textures)]:
                directory = package / (kind + suffix)
                if directory.exists():
                    for path in sorted(directory.iterdir()):
                        if path.suffix.lower() in ('.bmp', '.png'):
                            index.setdefault(path.stem.lower(), path)
    for name, path in native_textures.items():
        textures.setdefault(name, path)
    provenance = {}

    def texture(name):
        path = textures[name.lower()]
        provenance[str(path.relative_to(ROOT))] = sha(path)
        return Image.open(path).convert('RGBA')

    water_name = water_aliases['6wtrtyl'] + '000'
    water = texture(water_name)
    water.convert('RGB').save(OUT / 'materials/water.png')
    tiles = {}
    for index, entry in palette.items():
        name = entry['texture']
        resolved = water_aliases[name] + '000' if name in water_aliases else name
        image = texture(resolved)
        pixels = np.array(image)
        # Match the consumer key on the actual texture; blend alpha over water too.
        magenta = (pixels[:, :, 0] >= 248) & (pixels[:, :, 1] <= 8) & (pixels[:, :, 2] >= 248)
        cyan = (pixels[:, :, 0] <= 8) & (pixels[:, :, 1] >= 248) & (pixels[:, :, 2] >= 248)
        pixels[magenta | cyan, 3] = 0
        image = Image.alpha_composite(water.resize(image.size), Image.fromarray(pixels))
        tiles[index] = np.array(image.convert('RGB').resize((32, 32), Image.Resampling.LANCZOS))
    atlas = np.zeros((4096, 4096, 3), np.uint8)
    for y in range(128):
        for x in range(128):
            atlas[y*32:(y+1)*32, x*32:(x+1)*32] = tiles[payload['tile_map'][y*128+x]]
    Image.fromarray(atlas).save(OUT / 'materials/terrain.png')
    materials = {}
    for name in sorted({f['texture_name'].lower() for m in payload['bmodels'] for f in m['faces']
                        if not f['attributes'] & 0x2000}):
        image = texture(name)
        native_path = native_textures.get(name)
        assert native_path, name
        with Image.open(native_path) as im:
            logical_size = list(im.size)
        destination = OUT / 'materials' / (name + '.png')
        image.save(destination)
        materials[name] = dict(path=str(destination), logical_size=logical_size)

    # Actual roof polygons and face centers: stable overlay controls, no hand-picked image positions.
    roof_polygons, landmarks = [], []
    for model in payload['bmodels']:
        vertices = np.array([[v[a] for a in 'xyz'] for v in model['vertices']], float)
        for face in model['faces']:
            if face['attributes'] & 0x2000 or len(face['vertex_indices']) < 3:
                continue
            points = vertices[face['vertex_indices']]
            normal = np.cross(points[1]-points[0], points[2]-points[0])
            area_xy = abs(np.sum(points[:, 0]*np.roll(points[:, 1], -1)-points[:, 1]*np.roll(points[:, 0], -1)))/2
            if normal[2] > 0 and area_xy > 1000:
                roof_polygons.append(dict(model=model['index'], points=points[:, :2].tolist()))
        if model['name'].lower() in ['temple', 'tavern', 'castle']:
            landmarks.append(dict(label=model['name'], position=vertices.mean(axis=0).tolist()))
    save(OUT / 'scene_data.json', dict(height_map=payload['height_map'], tile_map=payload['tile_map'],
        bmodels=payload['bmodels'], materials=materials, roof_polygons=roof_polygons, landmarks=landmarks))
    index = json.loads((HERE.parent / 'accepted_icons.json').read_text())
    scope = {}
    for world in ['mm6', 'mm7', 'mm8']:
        maps = sorted((ROOT / 'assets_dev/worlds' / world / 'maps').glob('*.odm'))
        scope[world] = [dict(map=p.name, target=f'worlds-{world}--icons--{p.stem}.bmp',
                            indexed=f'worlds-{world}--icons--{p.stem}.bmp' in index['records']) for p in maps]
    save(HERE / 'outdoor_scope.json', scope)
    save(OUT / 'sources.json', dict(status='comparison_only_not_accepted',
        sources={str(p.relative_to(ROOT)): sha(p) for p in [native, runtime, map_path,
            ROOT / 'assets_dev/engine/data_tables/terrain_tile_data_3.txt',
            ROOT / 'assets_dev/engine/data_tables/hw_water_textures.txt']},
        textures=provenance, ledger_sha256=sha(HERE.parent / 'checkpoint/state.json'),
        index_sha256=sha(HERE.parent / 'accepted_icons.json'),
        mapping=dict(min_x=-32768, max_x=32768, min_y=-32768, max_y=32768, flip_v=True,
            width=1024, height=1024, world_units_per_pixel=64),
        geometry=dict(models=len(payload['bmodels']), faces=sum(len(m['faces']) for m in payload['bmodels']),
                      terrain_cells=[127, 127], roof_polygons=len(roof_polygons)),
        limitations=['Static terrain and BModels; no runtime state, actors or decoration billboards.',
                     'North-up orthographic projection; Blender lighting approximates the terrain appearance.']))
    print('Prepared New Sorpigal:', len(payload['bmodels']), 'models;', len(materials), 'model materials')


if __name__ == '__main__':
    main()
