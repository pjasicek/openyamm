#!/usr/bin/env python3
"""Viewer only (2026-11-05): put the installed elf-ear attachment (before/mm9_peasantboy_elfears.glb, LOD0, unchanged by the
reduction) on the joint node `Bip01 ElfEars` of a tier-e viewer GLB, as the game draws body + attachment for row 73. The ears
take the body file's head material (the head image carries the ear islands in boy e's skin, as the attachment's own image).
Usage: viewer_ears.py <viewer glb> (in place)"""
import json
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as RV  # noqa: E402

path = Path(sys.argv[1])
doc, binary = RV.read_glb(path); binary = bytearray(binary)
ed, eb = RV.read_glb(HERE / 'before' / 'mm9_peasantboy_elfears.glb')
prim = ed['meshes'][0]['primitives'][0]
newattr = {}


def copy_acc(i):
    a = dict(ed['accessors'][i]); v = ed['bufferViews'][a['bufferView']]; o = v.get('byteOffset', 0)
    data = eb[o:o + v['byteLength']]
    binary.extend(b'\0' * (-len(binary) % 4))
    bv = {'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)}
    if 'byteStride' in v:
        bv['byteStride'] = v['byteStride']
    doc['bufferViews'].append(bv); binary.extend(data)
    a['bufferView'] = len(doc['bufferViews']) - 1
    doc['accessors'].append(a); return len(doc['accessors']) - 1


for sem, i in prim['attributes'].items():
    newattr[sem] = copy_acc(i)
mat = next(i for i, m in enumerate(doc['materials']) if m['name'].startswith('PeasantBoyHead'))
doc['meshes'].append({'name': 'ElfEars', 'primitives': [{'attributes': newattr, 'indices': copy_acc(prim['indices']), 'material': mat}]})
node = next(n for n in doc['nodes'] if n.get('name') == 'Bip01 ElfEars')
node['mesh'] = len(doc['meshes']) - 1
d2, b2 = RV._compact(doc, bytes(binary)); RV.write_glb(path, d2, b2)
print('EARS on', path.name, json.dumps({'faces': ed['accessors'][prim['indices']]['count'] // 3, 'material': doc['materials'][mat]['name']}))
