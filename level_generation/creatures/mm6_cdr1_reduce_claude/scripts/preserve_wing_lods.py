"""mm6_cdr1_claude/scripts/preserve_wing_lods.py with paths: every LOD takes the LOD0 wing primitive (decimating the
thin membranes made holes) and the merged shadow meshes are regenerated. Usage: preserve_wing_lods.py <glb> (in place)"""
import copy, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools')); import build_actor_lods as L  # noqa: E402
f = Path(sys.argv[1]); d, b = L.read_glb(f); b = bytearray(b)
node = next(n for n in d['nodes'] if n.get('name') == 'Body'); base = d['meshes'][node['mesh']]
wing = next(p for p in base['primitives'] if d['materials'][p['material']]['name'] == 'DragonWings_A')
for index in base['extras']['openyamm_lods']:
    m = d['meshes'][index]
    for i, p in enumerate(m['primitives']):
        if d['materials'][p['material']]['name'] == 'DragonWings_A':
            m['primitives'][i] = copy.deepcopy(wing)
for level, index in enumerate([node['mesh']] + base['extras']['openyamm_lods']):
    d['meshes'][base['extras']['openyamm_shadow_lods'][level]] = L.merge_shadow(d, b, d['meshes'][index])
L.write_glb(f, d, b); print('WINGS intact wing membranes retained in every LOD')
