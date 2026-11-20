#!/usr/bin/env python3
"""Burn gate (the engine refuses a burning binding otherwise): every material a skinned primitive can draw (its own and
every KHR_materials_variants mapping, on every mesh of a skinned node and every mesh listed as its LOD or shadow LOD)
carries extras.openyamm_burn_map pointing at a burn image (by name: a compaction that drops or reorders
textures without remapping extras leaves the index on another image). Usage: check_burn.py <glb> (exit 1 on a miss)"""
import json, struct, sys
r = open(sys.argv[1], 'rb').read(); n = struct.unpack_from('<I', r, 12)[0]; d = json.loads(r[20:20 + n])
meshes = set()
for node in d['nodes']:
    if 'mesh' in node and 'skin' in node:
        m = d['meshes'][node['mesh']]; meshes.add(node['mesh'])
        ex = m.get('extras', {}); meshes.update(ex.get('openyamm_lods', [])); meshes.update(ex.get('openyamm_shadow_lods', []))
missing = set()
for mi in meshes:
    for p in d['meshes'][mi]['primitives']:
        mats = [p['material']] + [x['material'] for x in p.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', [])]
        for k in mats:
            b = d['materials'][k].get('extras', {}).get('openyamm_burn_map')
            ok = b is not None and b['index'] < len(d['textures']) and \
                'burn' in d['images'][d['textures'][b['index']]['source']].get('name', '')
            if not ok: missing.add(d['materials'][k].get('name', k))
print('BURN', 'ok' if not missing else 'MISSING ' + ', '.join(sorted(missing)), '(%d meshes)' % len(meshes))
sys.exit(1 if missing else 0)
