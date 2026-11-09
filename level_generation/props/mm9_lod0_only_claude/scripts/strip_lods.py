#!/usr/bin/env python3
"""Strip the LOD chain from MM9's simple decoration models (2026-11-09): every installed
assets_source/worlds/mm9/models/mm9_deco_*.glb whose LOD0 has fewer than LOD0_MAX triangles keeps LOD0 only.

Their LOD levels saved next to nothing (draw calls and fill are the same at every level) and the collapse-decimated
ones broke hard-surface shapes: the raised coffin's LOD2 caved in its lid and tore its sides (Thousand Terrors). The
props builds now make no LODs below 1000 triangles (LOD_MIN in each mm9_*_claude/scripts/build.py); this script
brings the installed models in line without rebuilding them. The posed figures and corpses (4,400+ triangles) keep
their LODs.

For each model: remove the openyamm_lods meshes, drop the accessors, buffer views and bytes only they used, check
that every remaining primitive's data is byte-identical to the original LOD0's, write work/<name>.glb and, with
--install, install it with tools/install_model.py --world mm9 (which cooks the runtime copy).
Usage: strip_lods.py [--install] [name.glb ...]   (no names: every model below LOD0_MAX that still has LODs)"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
REPO = HERE.parent.parent.parent
sys.path.insert(0, str(REPO / 'tools'))
from link_static_model_lods import read_glb, write_glb  # noqa: E402

SOURCES = REPO / 'assets_source' / 'worlds' / 'mm9' / 'models'
WORK = HERE / 'work'
LOD0_MAX = 4000


def triangles(doc, mesh):
    return sum(doc['accessors'][p['indices']]['count'] // 3 for p in mesh['primitives'] if 'indices' in p)


def lod_meshes(doc):
    return {i for mesh in doc['meshes'] for i in (mesh.get('extras') or {}).get('openyamm_lods', [])}


def accessor_bytes(doc, binary, index):
    accessor = doc['accessors'][index]
    view = doc['bufferViews'][accessor['bufferView']]
    start = view.get('byteOffset', 0)
    return accessor['componentType'], accessor['type'], accessor['count'], binary[start:start + view['byteLength']]


def primitive_data(doc, binary, mesh):
    rows = []
    for primitive in mesh['primitives']:
        attributes = {k: accessor_bytes(doc, binary, v) for k, v in sorted(primitive['attributes'].items())}
        indices = accessor_bytes(doc, binary, primitive['indices']) if 'indices' in primitive else None
        rows.append((attributes, indices, primitive.get('material'), primitive.get('mode')))
    return rows


def strip(doc, binary):
    for key in ('animations', 'skins'):
        if doc.get(key):
            raise SystemExit(f'unexpected {key}: extend the accessor remap first')
    if any(p.get('targets') for m in doc['meshes'] for p in m['primitives']):
        raise SystemExit('unexpected morph targets: extend the accessor remap first')
    used_meshes = sorted({node['mesh'] for node in doc['nodes'] if 'mesh' in node})
    if set(used_meshes) & lod_meshes(doc):
        raise SystemExit('a node references an LOD mesh')
    mesh_map = {old: new for new, old in enumerate(used_meshes)}
    doc['meshes'] = [doc['meshes'][old] for old in used_meshes]
    for node in doc['nodes']:
        if 'mesh' in node:
            node['mesh'] = mesh_map[node['mesh']]
    for mesh in doc['meshes']:
        extras = mesh.get('extras', {})
        extras.pop('openyamm_lods', None)
        if not extras:
            mesh.pop('extras', None)
    used_accessors = sorted({a for mesh in doc['meshes'] for p in mesh['primitives']
                             for a in list(p['attributes'].values()) + ([p['indices']] if 'indices' in p else [])})
    accessor_map = {old: new for new, old in enumerate(used_accessors)}
    doc['accessors'] = [doc['accessors'][old] for old in used_accessors]
    for mesh in doc['meshes']:
        for primitive in mesh['primitives']:
            primitive['attributes'] = {k: accessor_map[v] for k, v in primitive['attributes'].items()}
            if 'indices' in primitive:
                primitive['indices'] = accessor_map[primitive['indices']]
    used_views = sorted({a['bufferView'] for a in doc['accessors'] if 'bufferView' in a}
                        | {image['bufferView'] for image in doc.get('images', []) if 'bufferView' in image})
    view_map, views, packed = {}, [], bytearray()
    for old in used_views:
        view = dict(doc['bufferViews'][old])
        start = view.get('byteOffset', 0)
        while len(packed) % 4:
            packed.append(0)
        chunk = binary[start:start + view['byteLength']]
        view['byteOffset'] = len(packed)
        packed += chunk
        view_map[old] = len(views)
        views.append(view)
    doc['bufferViews'] = views
    for item in doc['accessors'] + doc.get('images', []):
        if 'bufferView' in item:
            item['bufferView'] = view_map[item['bufferView']]
    while len(packed) % 4:
        packed.append(0)
    doc['buffers'] = [{'byteLength': len(packed)}]
    return doc, bytes(packed)


def candidates():
    for path in sorted(SOURCES.glob('mm9_deco_*.glb')):
        doc, _ = read_glb(path)
        lods = lod_meshes(doc)
        if lods and sum(triangles(doc, m) for i, m in enumerate(doc['meshes']) if i not in lods) < LOD0_MAX:
            yield path.name


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--install', action='store_true')
    parser.add_argument('names', nargs='*')
    args = parser.parse_args()
    names = args.names or list(candidates())
    WORK.mkdir(exist_ok=True)
    for name in names:
        source = SOURCES / name
        doc, binary = read_glb(source)
        lods = lod_meshes(doc)
        if not lods:
            print(f'{name}: no LODs, skipped')
            continue
        before = [primitive_data(doc, binary, m) for i, m in enumerate(doc['meshes']) if i not in lods]
        chain = [triangles(doc, doc['meshes'][0])] + [triangles(doc, doc['meshes'][i]) for i in sorted(lods)]
        doc, binary = strip(doc, binary)
        if [primitive_data(doc, binary, m) for m in doc['meshes']] != before:
            raise SystemExit(f'{name}: LOD0 data changed')
        out = WORK / name
        write_glb(out, doc, binary)
        os.chmod(out, 0o644)
        print(f'{name}: {"/".join(map(str, chain))} -> {chain[0]}, {source.stat().st_size} -> {out.stat().st_size} B')
        if args.install:
            subprocess.run([sys.executable, str(REPO / 'tools' / 'install_model.py'), str(out), '--world', 'mm9'],
                           check=True)


if __name__ == '__main__':
    main()
