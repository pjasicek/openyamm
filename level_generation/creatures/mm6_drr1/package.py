"""Package land dragon artwork and declare its native nonlinear recolor contract."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
subprocess.run([sys.executable, str(ROOT.parent / 'mm6_peasants/package_family.py'), 'drr1'], check=True)
path = ROOT / 'manifest.json'
manifest = json.loads(path.read_text())
manifest['recolor_model'] = 'multi_mask_luminance_lut_v1'
manifest['recolor'] = {
    'model': 'multi_mask_luminance_lut_v1',
    'space': 'sRGB encoded RGB; four linear material coverage channels',
    'operation': 'i=round(255*dot(base.rgb,[.2126,.7152,.0722])); out=base.rgb*(1-sum(mask))+sum(mask[k]*lut[k][i]); preserve sprite alpha; exact base bypass',
    'fitting': 'Native-used material indices, usage-weighted Gaussian luminance interpolation with sigma=4 levels; see materials.py',
    'runtime': 'Staged asset contract; requires LUT-aware loader/shader or deterministic variant baking before gameplay installation'
}
for variant in manifest['variants'].values():
    if 'region_luminance_vectors' in variant:
        variant['region_luminance_luts'] = variant.pop('region_luminance_vectors')
path.write_text(json.dumps(manifest, indent=2) + '\n')

validation_path = ROOT / "validation.json"
validation = json.loads(validation_path.read_text())
validation["shipping_bytes"] = path.stat().st_size + sum(
    (ROOT / page[key]).stat().st_size for page in manifest["pages"] for key in ("base", "mask"))
validation_path.write_text(json.dumps(validation, indent=2) + "\n")
