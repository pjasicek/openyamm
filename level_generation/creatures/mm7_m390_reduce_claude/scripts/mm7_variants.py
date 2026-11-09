"""export/mm7_m390.glb: the reduced Thunderbird (work/r54_shadow.glb: LOD0-3, shadow LODs, clips, variants carried)
with the MM7 Roc variants of mm7_m390_claude (scripts/build_glb.py there): variant names m390_a/b/c, materials
Roc_A/B/C, region ramps from mm7_m390_claude/textures/m390_ramps.json. Geometry, skin, clips and images unchanged."""
import hashlib, json, sys
from pathlib import Path
P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P.parent / 'claude_shared'))
import region_variants as RV  # noqa: E402
config = json.loads((P.parent / 'mm7_m390_claude/textures/m390_ramps.json').read_text())
doc, binary = RV.read_glb(P / 'work/r54_shadow.glb')
assert [v['name'] for v in doc['extensions']['KHR_materials_variants']['variants']] == ['m552_a', 'm552_b', 'm552_c']
doc['extensions']['KHR_materials_variants']['variants'] = [{'name': n} for n in config['variants']]
ramps = config['materials'][0]['ramps']
for m in doc['materials']:
    tier = m['name'].split('_')[-1].lower(); assert m['name'].startswith('Thunderbird_') and tier in 'abc'
    m['name'] = f'Roc_{tier.upper()}'; m['extras']['openyamm_region_ramps'] = ramps[f'm390_{tier}']
out = P / 'export/mm7_m390.glb'; RV.write_glb(out, doc, binary)
imgs = []
for im in doc['images']:
    bv = doc['bufferViews'][im['bufferView']]; o = bv.get('byteOffset', 0)
    imgs.append((im.get('name'), hashlib.sha256(bytes(binary[o:o + bv['byteLength']])).hexdigest()[:16]))
print('BUILT', out.name, hashlib.sha256(out.read_bytes()).hexdigest(), out.stat().st_size, imgs)
