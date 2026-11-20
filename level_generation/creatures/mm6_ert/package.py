"""Pack the Earth elemental and declare the one-mask native palette LUTs."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
subprocess.run([sys.executable, str(ROOT.parent / 'mm6_peasants/package_family.py'), 'ert'], check=True)
path = ROOT / 'manifest.json'
manifest = json.loads(path.read_text())
manifest['recolor_model'] = 'masked_luminance_lut_v1'
manifest['recolor'] = {
    'model': 'masked_luminance_lut_v1',
    'space': 'sRGB encoded RGB; linear R8 material coverage',
    'operation': 'i=round(255*dot(base.rgb,[.2126,.7152,.0722])); out=lerp(base.rgb,lut[i],mask.r); preserve alpha; exact base bypass',
    'fitting': 'Native-used stone indices; usage-weighted Gaussian luminance interpolation, sigma=4; shadow extrapolation toward black; materials.py',
    'runtime': 'Staged only; requires LUT-aware loader/shader or deterministic variant baking before installation'
}
manifest['regions'] = {'mask_r': 'Earthen stone surface; preserve black fissures'}
for variant in manifest['variants'].values():
    if 'luminance_vector' in variant:
        variant['luminance_lut'] = variant.pop('luminance_vector')
memory = manifest['memory_bytes']
memory['variant_luts_float32'] = 2 * 256 * 3 * 4
memory['enhanced_shared_base_mask_and_luts'] = (
    memory['enhanced_shared_base_and_mask'] + memory['variant_luts_float32'])
manifest['limitations'][0] = 'Stone facets and fissures are reconstructed and can vary slightly between poses.'
path.write_text(json.dumps(manifest, indent=2) + '\n')
validation_path = ROOT / 'validation.json'
validation = json.loads(validation_path.read_text())
validation['memory_bytes'] = memory
validation['shipping_bytes'] = path.stat().st_size + sum(
    (ROOT / page[key]).stat().st_size for page in manifest['pages'] for key in ('base', 'mask'))
validation_path.write_text(json.dumps(validation, indent=2) + '\n')
