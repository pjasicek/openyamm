"""Writes review/viewer/manifest.json for the model viewer: one entry per installed design (ledger.json) with its
title, family, route, bound items (names from the bindings' comments), the installed source GLB and the icon and
HD painting it was made from. Paths are relative to the repository root, which the viewer is served from:

    python3 -I scripts/viewer_manifest.py
    python3 -m http.server 8912 --bind 127.0.0.1 --directory <repository>
    http://127.0.0.1:8912/level_generation/props/items_mm9_claude/review/viewer/"""
import json
import os
import re

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
DESIGNS = json.load(open(os.path.join(HERE, 'designs.json')))
LEDGER = json.load(open(os.path.join(HERE, 'ledger.json')))
BINDING = re.compile(r'icon: mm9_item_(\d+),.*#\s*(.+)$')


def relative(path):
    return os.path.relpath(path, ROOT) if path and os.path.exists(path) else None


def main():
    names = {}
    for line in open(os.path.join(ROOT, 'assets_dev', 'worlds', 'mm9', 'world_items', 'items.yml')):
        match = BINDING.search(line)
        if match:
            names[int(match.group(1))] = match.group(2).strip()
    entries = []
    for design, record in sorted(LEDGER.items()):
        info = DESIGNS[design]
        model = os.path.join(ROOT, 'assets_source', record['model'])
        painting = os.path.join(HERE, 'meshy', design, 'references_hd', 'design_painting.png')
        generator = os.path.join(HERE, 'codex_tex', design, 'generation_paint.json')
        fallback = os.path.exists(generator) and 'icon_paint' in open(generator).read()
        entries.append({
            'design': design,
            'title': info['title'],
            'family': info['family'],
            'route': record['route'],
            'length': record['length'],
            'items': [{'id': item, 'name': names.get(item, '')} for item in record['items']],
            'model': relative(model),
            'bytes': os.path.getsize(model),
            'icon': relative(info.get('icon_path')),
            'painting': relative(painting) or relative(info.get('painting')),
            'icon_paint': fallback,
        })
    output = os.path.join(HERE, 'review', 'viewer', 'manifest.json')
    with open(output, 'w') as handle:
        json.dump({'designs': entries}, handle, indent=1)
        handle.write('\n')
    print('MANIFEST', len(entries), output)


if __name__ == '__main__':
    main()
