"""Apply the inspected local blade correction, retaining geometry and original masters."""
import json
import shutil
import numpy as np
from PIL import Image
from process import ROOT, queue, save
from process_compact import grade, variants
import materials

settings = json.loads((ROOT / 'blade_color_settings.json').read_text())
tone = json.loads((ROOT / 'tone_settings.json').read_text())['multiplier']
archive = ROOT / 'checkpoints/before_blade_color'
archive.mkdir(exist_ok=True)
checks = {}
for name, item in settings['frames'].items():
    destination = ROOT / 'toned_2x' / (name + '.png')
    if not (archive / (name + '.png')).exists():
        shutil.copy2(destination, archive / (name + '.png'))
    before = np.array(Image.open(archive / (name + '.png')))
    final = grade(Image.open(ROOT / 'registered_2x' / (name + '.png')), tone, name)
    a = np.asarray(final)
    mask = np.asarray(Image.open(ROOT / item['mask']))
    assert np.array_equal(a[:, :, 3], before[:, :, 3])
    assert np.array_equal(a[mask == 0], before[mask == 0])
    final.save(destination)
    variants(name, final, materials.settings())
    checks[name] = {'master_sha256': queue.sha(destination), 'alpha_exact': True,
                    'unmasked_pixels_exact': True, 'settings': item}
save(ROOT / 'review/blade_color_checks.json', {'status': 'passed', 'mask_review': 'review/blade_color_masks.png',
    'frames': checks})
print('Corrected', len(checks), 'exposed blades; geometry, alpha and unmasked materials exact.')
