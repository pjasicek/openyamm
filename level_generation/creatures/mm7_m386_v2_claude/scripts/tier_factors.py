"""Tier materials after region_variants.py (compose_v2.py contract): Robot_B / Robot_C take the original descriptor
TintColor multiply as baseColorFactor (linear, textures/robot_ramps.json "tint_factors"); their region ramps only keep
the glows' colour. Robot_A is the plain shared skin: its region mask and ramps are dropped. Rewrites the GLB in place.
Usage: tier_factors.py <glb> [...]"""
import json, sys
from pathlib import Path
P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402
factors = json.loads((P / 'textures/robot_ramps.json').read_text())['tint_factors']
for path in sys.argv[1:]:
    doc, binary = read_glb(Path(path))
    seen = []
    for m in doc['materials']:
        name = m.get('name', '')
        for variant, factor in factors.items():
            if name == 'Robot_' + variant[-1].upper():
                pbr = m.setdefault('pbrMetallicRoughness', {})
                if variant.endswith('a'):
                    pbr.pop('baseColorFactor', None)
                    for k in ('openyamm_region_mask', 'openyamm_region_ramps'):
                        m.get('extras', {}).pop(k, None)
                else:
                    pbr['baseColorFactor'] = factor
                seen.append(name)
    assert sorted(seen) == ['Robot_A', 'Robot_B', 'Robot_C'], seen
    write_glb(Path(path), doc, binary)
    print('TIERS', path, seen)
