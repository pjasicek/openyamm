"""Package skeleton artwork and declare its native nonlinear recolor contract."""
import json
import shutil
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
if '--redo' in sys.argv:
    sys.path.insert(0, str(ROOT.parent / 'mm6_remaining/redo_2x'))
    from export_run import export
    shutil.copy2(ROOT/'materials.py', ROOT/'redo_2x/materials.py')
    export(str(ROOT), with_viewer=False)
    ROOT = ROOT / 'redo_2x'
else:
    subprocess.run([sys.executable, str(ROOT.parent / 'mm6_peasants/package_family.py'), 'ske'], check=True)
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
if '--redo' in sys.argv:
    manifest['limitations'] = [
        'AI-reconstructed bone shapes and blade foreshortening vary slightly from native art.',
        'Annotated static sequence review; no gameplay playback performed for this staged package.',
        '58 newly generated playback frames preserve supplied alpha; unused skefib0 retains its reviewed historical cutout.'
    ]
path.write_text(json.dumps(manifest, indent=2) + '\n')

validation_path = ROOT / "validation.json"
validation = json.loads(validation_path.read_text())
validation["shipping_bytes"] = path.stat().st_size + sum(
    (ROOT / page[key]).stat().st_size for page in manifest["pages"] for key in ("base", "mask"))
validation_path.write_text(json.dumps(validation, indent=2) + "\n")
