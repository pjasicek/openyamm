#!/usr/bin/env python3
"""Download the CC0 Poly Haven texture sets of the heaps and small props (1k PNG: diffuse, OpenGL normal,
roughness) into textures/source/<asset>/ with each asset's files.json, skipping files already present.
Usage: small_fetch.py [asset ...]"""
import json
import sys
import urllib.request
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / 'textures' / 'source'
HEADERS = {'User-Agent': 'OpenYAMM-asset-fetch/1.0'}
MAPS = {'Diffuse': 'diff', 'nor_gl': 'nor_gl', 'Rough': 'rough'}
ASSETS = ['rusty_metal_02', 'metal_plate_02', 'rough_wood', 'gravelly_sand', 'brown_mud_rocks_01', 'brown_mud_dry',
          'wooden_barrel', 'weathered_planks', 'rusty_metal_05', 'green_metal_rust', 'dirty_carpet', 'bark_platanus',
          'rock_boulder_dry', 'rock_pitted_mossy']


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=60)


def main():
    for asset in sys.argv[1:] or ASSETS:
        folder = SOURCE / asset
        folder.mkdir(parents=True, exist_ok=True)
        info = folder / 'files.json'
        if not info.exists():
            info.write_bytes(get(f'https://api.polyhaven.com/files/{asset}').read())
        files = json.loads(info.read_text())
        for key, short in MAPS.items():
            if key not in files:
                print('MISSING', asset, key)
                continue
            path = folder / f'{asset}_{short}_1k.png'
            if not path.exists():
                path.write_bytes(get(files[key]['1k']['png']['url']).read())
            print('FETCH', path.name, path.stat().st_size)


if __name__ == '__main__':
    main()
