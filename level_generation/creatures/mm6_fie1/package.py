"""Pack Fire Elemental art and declare its one-mask nonlinear recolor contract."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
subprocess.run([sys.executable, str(ROOT.parent / 'mm6_peasants/package_family.py'), 'fie1'], check=True)
path = ROOT / 'manifest.json'
manifest = json.loads(path.read_text())
manifest['recolor_model'] = 'masked_luminance_lut_v1'
manifest['recolor'] = {
    'model': 'masked_luminance_lut_v1',
    'space': 'sRGB encoded RGB; linear R8 material coverage',
    'operation': 'i=round(255*dot(base.rgb,[.2126,.7152,.0722])); out=lerp(base.rgb,lut[i],mask.r); preserve alpha; exact base bypass',
    'fitting': 'Native-used changed core indices; Gaussian luminance interpolation, sigma=4; fixed 1.17 input-luma calibration and shadow extrapolation baked into LUTs; materials.py',
    'runtime': 'Staged only; requires LUT-aware loader/shader or deterministic variant baking before installation'
}
manifest['regions'] = {'mask_r': 'Inner red elemental core; protect outer yellow/orange flames'}
for variant in manifest['variants'].values():
    if 'luminance_vector' in variant:
        variant['luminance_lut'] = variant.pop('luminance_vector')
memory = manifest['memory_bytes']
memory['variant_luts_float32'] = 2 * 256 * 3 * 4
memory['enhanced_shared_base_mask_and_luts'] = (
    memory['enhanced_shared_base_and_mask'] + memory['variant_luts_float32'])
manifest['limitations'][0] = 'Flame ribbons and inner core details are reconstructed; native animation poses are retained.'
assert manifest['animations']['corpse']['no_image']
path.write_text(json.dumps(manifest, indent=2) + '\n')
validation_path = ROOT / 'validation.json'
validation = json.loads(validation_path.read_text())
validation['memory_bytes'] = memory
validation['native_null_corpse_preserved'] = True
validation['shipping_bytes'] = path.stat().st_size + sum(
    (ROOT / page[key]).stat().st_size for page in manifest['pages'] for key in ('base', 'mask'))
validation_path.write_text(json.dumps(validation, indent=2) + '\n')
