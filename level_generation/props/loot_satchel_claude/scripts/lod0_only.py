#!/usr/bin/env python3
"""Strip the LOD chain from an installed satchel: satchels are drawn at full detail only (2026-10-09, the user saw the
collapsed LODs change shape while walking up to one; 400-1,800 triangles cost little). Usage: lod0_only.py <tier>...
Removes the openyamm_lods / openyamm_shadow_lods meshes, then drops every accessor, buffer view and byte they alone
used, and rewrites assets_dev/engine/models/loot_satchel_t<N>.glb in place (0644)."""
import os, sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tiers import REPO
sys.path.insert(0, os.path.join(REPO, 'tools'))
from link_static_model_lods import read_glb, write_glb


def strip(path):
    doc, binary = read_glb(path)
    used_meshes = sorted({node['mesh'] for node in doc['nodes'] if 'mesh' in node})
    mesh_map = {old: new for new, old in enumerate(used_meshes)}
    doc['meshes'] = [doc['meshes'][old] for old in used_meshes]
    for node in doc['nodes']:
        if 'mesh' in node:
            node['mesh'] = mesh_map[node['mesh']]
    for mesh in doc['meshes']:
        extras = mesh.get('extras', {})
        extras.pop('openyamm_lods', None)
        extras.pop('openyamm_shadow_lods', None)
        if not extras:
            mesh.pop('extras', None)
    # Accessors still referenced, then the buffer views they and the images use.
    used_accessors = set()
    for mesh in doc['meshes']:
        for primitive in mesh['primitives']:
            used_accessors.update(primitive['attributes'].values())
            if 'indices' in primitive:
                used_accessors.add(primitive['indices'])
            for target in primitive.get('targets', []):
                used_accessors.update(target.values())
    accessor_map = {old: new for new, old in enumerate(sorted(used_accessors))}
    doc['accessors'] = [doc['accessors'][old] for old in sorted(used_accessors)]
    for mesh in doc['meshes']:
        for primitive in mesh['primitives']:
            primitive['attributes'] = {k: accessor_map[v] for k, v in primitive['attributes'].items()}
            if 'indices' in primitive:
                primitive['indices'] = accessor_map[primitive['indices']]
            primitive['targets'] = [{k: accessor_map[v] for k, v in t.items()} for t in primitive.get('targets', [])]
            if not primitive['targets']:
                primitive.pop('targets')
    used_views = sorted({a['bufferView'] for a in doc['accessors'] if 'bufferView' in a}
                        | {image['bufferView'] for image in doc.get('images', []) if 'bufferView' in image})
    view_map, packed = {}, bytearray()
    views = []
    for old in used_views:
        view = dict(doc['bufferViews'][old])
        start = view.get('byteOffset', 0)
        chunk = binary[start:start + view['byteLength']]
        while len(packed) % 4:
            packed.append(0)
        view['byteOffset'] = len(packed)
        packed += chunk
        view_map[old] = len(views)
        views.append(view)
    doc['bufferViews'] = views
    for accessor in doc['accessors']:
        if 'bufferView' in accessor:
            accessor['bufferView'] = view_map[accessor['bufferView']]
    for image in doc.get('images', []):
        if 'bufferView' in image:
            image['bufferView'] = view_map[image['bufferView']]
    while len(packed) % 4:
        packed.append(0)
    doc['buffers'] = [{'byteLength': len(packed)}]
    write_glb(path, doc, bytes(packed))
    os.chmod(path, 0o644)
    triangles = sum(doc['accessors'][p['indices']]['count'] // 3 for m in doc['meshes'] for p in m['primitives'])
    print(path.name, 'meshes', len(doc['meshes']), 'triangles', triangles, 'bytes', path.stat().st_size)


for tier in sys.argv[1:]:
    strip(Path(REPO) / 'assets_dev' / 'engine' / 'models' / f'loot_satchel_t{int(tier)}.glb')
