#!/usr/bin/env python3
"""Download Poly Haven (CC0) 2k glTF scans with their textures into ../source/<asset>/, md5-checked.
Usage: fetch_scans.py <asset>..."""
import hashlib, json, os, sys, urllib.request
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'openyamm-mm7-rocks'})
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


for asset in sys.argv[1:]:
    info = json.loads(get(f'https://api.polyhaven.com/files/{asset}'))['gltf']['2k']['gltf']
    folder = os.path.join(HERE, 'source', asset)
    files = {os.path.basename(info['url']): (info['url'], info.get('md5'))}
    files.update({k: (v['url'], v.get('md5')) for k, v in info['include'].items()})
    for rel, (url, md5) in files.items():
        path = os.path.join(folder, rel)
        if os.path.exists(path) and (md5 is None or hashlib.md5(open(path, 'rb').read()).hexdigest() == md5):
            continue
        data = get(url)
        if md5 and hashlib.md5(data).hexdigest() != md5:
            raise SystemExit(f'md5 mismatch {url}')
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, 'wb').write(data)
    print('FETCHED', asset, sorted(files))
