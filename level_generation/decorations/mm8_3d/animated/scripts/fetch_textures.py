#!/usr/bin/env python3
"""Gather the CC0 Poly Haven scans of this batch into source/polyhaven/<asset>/ (1k PNG: diffuse, OpenGL normal,
roughness). Scans already downloaded by the MM6 projects are copied from there (read only); the others are fetched
from https://api.polyhaven.com/files/<asset> (no account needed). Poly Haven assets are CC0 1.0
(https://polyhaven.com/license). Usage: fetch_textures.py"""
import json
import shutil
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
OUT = HERE / 'source' / 'polyhaven'
DECORATIONS = HERE.parents[1]
LOCAL = [DECORATIONS / 'mm6_dungeons_3d' / 'fire' / 'source' / 'polyhaven',
         DECORATIONS / 'mm6_dungeons_3d' / 'torch_textures' / 'source']
# asset -> what it becomes here (make_textures.py)
ASSETS = {
    'rusty_metal_04': 'dark wrought iron (lantern, chandelier dec27)',
    'rusty_metal_02': 'grey wrought iron (chandelier dec08)',
    'blue_metal_plate': 'scratched copper / brass (candlestick, buoy cage, bell and dome)',
    'leather_white': 'candle wax grain',
    'rough_wood': 'torch stick, chandelier posts',
    'hessian_380': 'torch head wrap',
    'bark_brown_02': 'campfire logs',
    'marble_rock_01': 'ember beds (through a fire ramp)',
    'brown_planks_03': 'buoy barrel staves',
}
KINDS = ('diff', 'nor_gl', 'rough')
AGENT = {'User-Agent': 'OpenYAMM-asset-fetch/1.0'}


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=AGENT), timeout=120) as response:
        return response.read()


def fetch(asset):
    folder = OUT / asset
    folder.mkdir(parents=True, exist_ok=True)
    for kind in KINDS:
        target = folder / f'{asset}_{kind}_1k.png'
        if target.exists():
            continue
        for root in LOCAL:
            source = root / asset / target.name
            if source.exists():
                shutil.copyfile(source, target)
                print('copied', source.relative_to(DECORATIONS))
                break
        else:
            files = json.loads(get(f'https://api.polyhaven.com/files/{asset}'))
            (folder / 'files.json').write_text(json.dumps(files, indent=1))
            key = {'diff': 'Diffuse', 'nor_gl': 'nor_gl', 'rough': 'Rough'}[kind]
            url = files[key]['1k']['png']['url']
            target.write_bytes(get(url))
            print('fetched', url)


def main():
    for asset in ASSETS:
        fetch(asset)


if __name__ == '__main__':
    main()
