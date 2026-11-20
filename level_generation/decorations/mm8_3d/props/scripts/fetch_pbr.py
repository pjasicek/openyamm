#!/usr/bin/env python3
"""Download the CC0 Poly Haven sources of the MM8 props into props/source/<asset>/, skipping files already present.
Texture sets: 2k PNG diff, nor_gl, rough, ao, disp (make_textures.py grades them into props/textures/).
Models: the 1k glTF with its textures (fruit for the fruit bowl). All CC0, https://polyhaven.com/license.
Usage: python3 -I fetch_pbr.py"""
import json
import os
import urllib.request

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(HERE, 'source')
HEADERS = {'User-Agent': 'OpenYAMM-asset-fetch/1.0'}
TEXTURES = {
    'lichen_rock': 'rune posts (grey weathered stone with cracks)',
    'mossy_rock': 'elf statue (weathered green-grey stone)',
    'weathered_planks': 'barrel staves (vertical planks with gaps)',
    'metal_plate_02': 'barrel hoops, metal plates and bowls (worn dark steel, graded to pewter)',
    'rosewood_veneer1': 'wooden plates (orange-brown grain)',
    'fine_grained_wood': 'fruit bowl',
    'pine_bark': 'trash heap flakes (bark plates)',
    'brown_mud_leaves_01': 'trash heap core (mud, leaves and moss)',
    'rust_coarse_01': 'cauldron iron',
    'rock_boulder_dry': 'cauldron coal stones',
    'bark_willow': 'cauldron logs (charred bark)',
    'leather_white': 'meat (wet glossy surface detail under the procedural fibres)',
}
MODELS = {
    'food_apple_01': 'fruit bowl apples',
    'bananas': 'fruit bowl bananas',
    'food_lime_01': 'fruit bowl orange (recoloured) and grapes',
}
MAPS = {'Diffuse': 'diff', 'nor_gl': 'nor_gl', 'Rough': 'rough', 'AO': 'ao', 'Displacement': 'disp'}


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=180)


def fetch(url, path):
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        data = get(url).read()
        with open(path, 'wb') as out:
            out.write(data)
    print('FETCH', path, os.path.getsize(path))


for asset in TEXTURES:
    files = None
    for key, short in MAPS.items():
        path = os.path.join(SOURCE, asset, f'{asset}_{short}_2k.png')
        if os.path.exists(path):
            continue
        files = files or json.load(get(f'https://api.polyhaven.com/files/{asset}'))
        if key not in files:
            print('MISSING', asset, key)
            continue
        fetch(files[key]['2k']['png']['url'], path)

for asset in MODELS:
    files = json.load(get(f'https://api.polyhaven.com/files/{asset}'))
    entry = files['gltf']['1k']['gltf']
    folder = os.path.join(SOURCE, asset)
    fetch(entry['url'], os.path.join(folder, f'{asset}_1k.gltf'))
    for relative, info in entry.get('include', {}).items():
        fetch(info['url'], os.path.join(folder, relative))
