#!/usr/bin/env python3
"""Download the Poly Haven (CC0) texture sets the dead trees use into trees/source/<asset>/ (2k PNG: diff, nor_gl,
rough, ao, disp), skipping files already present. Usage: dead_fetch.py"""
import json, os, urllib.request
import dead_common as dc

HEADERS = {'User-Agent': 'OpenYAMM-asset-fetch/1.0'}


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS))


MAPS = {'Diffuse': 'diff', 'nor_gl': 'nor_gl', 'Rough': 'rough', 'AO': 'ao', 'Displacement': 'disp'}
for asset in dc.TEXTURE_SETS:
    folder = os.path.join(dc.SOURCE, asset)
    os.makedirs(folder, exist_ok=True)
    files = json.load(get(f'https://api.polyhaven.com/files/{asset}'))
    for key, short in MAPS.items():
        if key not in files:
            continue
        path = os.path.join(folder, f'{asset}_{short}_2k.png')
        if not os.path.exists(path):
            open(path, 'wb').write(get(files[key]['2k']['png']['url']).read())
        print('FETCH', path, os.path.getsize(path))
