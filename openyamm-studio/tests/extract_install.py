#!/usr/bin/env python3
"""A player's install as a development tree, for the native reference builds of S5c (tests/hosted_checks.sh).

The hosted page reads an install's content packs by byte range and shows the core the tree they mount
(web/src/hosted/install.ts). The native core reads only development trees, so the native side of the comparison
reads the same packs extracted into a folder: every non-language pack of the current release's index, each under its
mount, in the index's order (a later file at the same path would win, as in the hosted page; the script reports any).

    python3 tests/extract_install.py <install folder> <target folder>
"""
import json
import os
import sys
import zipfile


def main():
    install, target = sys.argv[1], sys.argv[2]
    release = open(os.path.join(install, 'app', 'current')).read().strip()
    index_path = os.path.join(install, 'app', release, 'index.json')
    index = json.load(open(index_path))
    store = os.path.normpath(os.path.join(os.path.dirname(index_path), index['store']))
    seen = {}
    files = 0
    for pack in index['packs']:
        if pack.get('language'):
            continue
        mount = pack['mount'].strip('/')
        with zipfile.ZipFile(os.path.join(store, pack['file'])) as archive:
            for info in archive.infolist():
                if info.filename.endswith('/'):
                    continue
                path = os.path.join(target, mount, info.filename)
                if path in seen:
                    print(f'overlap: {mount}/{info.filename} in {seen[path]} and {pack["id"]}')
                seen[path] = pack['id']
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with archive.open(info) as source, open(path, 'wb') as output:
                    while True:
                        chunk = source.read(1 << 20)
                        if not chunk:
                            break
                        output.write(chunk)
                files += 1
    print(f'release {release}: {files} files into {target}')


if __name__ == '__main__':
    main()
