#!/usr/bin/env python3
"""Download the CC0 Poly Haven texture sets the dungeon wall torches use into torch_textures/source/<asset>/ (1k PNG:
diffuse, OpenGL normal, roughness, metal and ambient occlusion where the set has them), skipping files already present.
Usage: python3 -I fetch.py [asset ...] (default: ASSETS)"""
import json
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(HERE, 'source')
HEADERS = {'User-Agent': 'OpenYAMM-asset-fetch/1.0'}
ASSETS = ['rough_wood', 'hessian_380', 'rust_coarse_01', 'rusty_metal_04']
MAPS = {'Diffuse': 'diff', 'nor_gl': 'nor_gl', 'Rough': 'rough', 'Metal': 'metal', 'AO': 'ao'}
RESOLUTION = '1k'


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=60)


for asset in sys.argv[1:] or ASSETS:
    folder = os.path.join(SOURCE, asset)
    os.makedirs(folder, exist_ok=True)
    files = json.load(get(f'https://api.polyhaven.com/files/{asset}'))
    for key, short in MAPS.items():
        if key not in files or RESOLUTION not in files[key] or 'png' not in files[key][RESOLUTION]:
            continue
        path = os.path.join(folder, f'{asset}_{short}_{RESOLUTION}.png')
        if not os.path.exists(path):
            with open(path, 'wb') as handle:
                handle.write(get(files[key][RESOLUTION]['png']['url']).read())
        print('FETCH', path, os.path.getsize(path))
