#!/usr/bin/env python3
"""A repainted head without re-running the clips: the head image inside export/mm9_dwarf_lods_shadowfix.glb is replaced by textures/dwarf_head_a_final.png. Project folder."""
import sys
from pathlib import Path
sys.path.insert(0, '../claude_shared')
import region_variants as RV
p = Path('export/mm9_dwarf_lods_shadowfix.glb'); d, b = RV.read_glb(p); b = bytearray(b)
data = Path('textures/dwarf_head_a_final.png').read_bytes(); n = 0
for im in d['images']:
    if 'head_a_final' in im.get('name', ''):
        b.extend(b'\0' * (-len(b) % 4)); bv = d['bufferViews'][im['bufferView']]; bv['byteOffset'] = len(b); bv['byteLength'] = len(data); b.extend(data); im['mimeType'] = 'image/png'; n += 1
assert n, [i.get('name') for i in d['images']]
RV.write_glb(p, d, bytes(b)); print('SWAPPED', n)
