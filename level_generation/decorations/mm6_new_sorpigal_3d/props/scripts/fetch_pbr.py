#!/usr/bin/env python3
"""Download the CC0 Poly Haven texture sets of the fire props (cauldron, campfire, burning rock, log-pile fire) into
props/textures_pbr/source/<asset>/ (2k PNG: diff, nor_gl, rough, ao, disp), skipping files already present.
make_pbr_textures.py grades them into props/textures_pbr/. Usage: fetch_pbr.py"""
import json, os, urllib.request

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(HERE, 'textures_pbr', 'source')
HEADERS = {'User-Agent': 'OpenYAMM-asset-fetch/1.0'}
# Poly Haven asset -> role (all CC0, https://polyhaven.com/license)
ASSETS = {
    'japanese_cedar_bark': 'tripod poles (fine vertical fibres)',
    'rust_coarse_01': 'cast-iron kettle (greyed, partly metallic)',
    'rock_boulder_dry': 'fire-ring stones',
    'bark_willow': 'charred log bark',
    'pine_bark': 'glowing split-log faces and ember bed (alligatored char)',
    'dark_rock': 'burning rock basalt and its lava pools',
    'rough_wood': 'log-pile fire (dec04): the lighter, less burnt logs and planks',
}
MAPS = {'Diffuse': 'diff', 'nor_gl': 'nor_gl', 'Rough': 'rough', 'AO': 'ao', 'Displacement': 'disp'}


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=120)


for asset in ASSETS:
    folder = os.path.join(SOURCE, asset)
    os.makedirs(folder, exist_ok=True)
    if all(os.path.exists(os.path.join(folder, f'{asset}_{short}_2k.png')) for short in MAPS.values()):
        print('PRESENT', asset)
        continue
    files = json.load(get(f'https://api.polyhaven.com/files/{asset}'))
    for key, short in MAPS.items():
        if key not in files:
            print('MISSING', asset, key)
            continue
        path = os.path.join(folder, f'{asset}_{short}_2k.png')
        if not os.path.exists(path):
            data = get(files[key]['2k']['png']['url']).read()
            with open(path, 'wb') as out:
                out.write(data)
        print('FETCH', path, os.path.getsize(path))
