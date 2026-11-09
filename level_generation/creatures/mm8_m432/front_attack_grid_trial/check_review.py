"""Check the real file:// viewer and preserve a compact edge contact for this unaccepted trial."""
from pathlib import Path
import html
import json
import re
import subprocess
import tempfile
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from foot_alignment import feet, translate

T = Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='dark-elf-grid-review-', dir='/tmp') as work:
    result = subprocess.run(['google-chrome', '--headless', '--no-sandbox', '--disable-gpu',
        '--disable-dev-shm-usage', '--allow-file-access-from-files', '--disable-background-networking',
        '--user-data-dir='+work, '--virtual-time-budget=30000', '--dump-dom', (T/'viewer.html').as_uri()],
        capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr[-1500:]
    found = re.search(r'data-checks="([^"]+)"', result.stdout)
    assert found, re.findall(r'<body[^>]*>', result.stdout)
    checks = json.loads(html.unescape(found.group(1)))
    assert checks == {'decoded': 56, 'timing_boundaries': 16, 'hold_last': True}, checks
    (T/'review/browser_checks.json').write_text(json.dumps(checks, indent=2)+'\n')

manifest = json.loads((T/'manifest.json').read_text())
if 'foot_alignment' in manifest:
    report = {}
    for name, rec in manifest['foot_alignment']['frames'].items():
        offset = rec['translation_2x_px']
        paths = ['runtime_aligned_2x/'+name+'.png', 'masks_2x/'+name+'.png']
        paths += ['previews/'+name+'_'+str(p)+'.png' for p in [433, 434, 435]]
        for path in paths:
            expected = translate(Image.open(T/'before_alignment'/path), offset)
            assert np.array_equal(expected, Image.open(T/path)), path
        after = feet(Image.open(T/'runtime_aligned_2x'/(name+'.png')))
        assert after == rec['after']
        assert after['sole_y'] == rec['native']['sole_y']
        assert abs(after['stance_center_x']-rec['native']['stance_center_x']) <= .5
        report[name] = {'offset': offset, 'ground_error': 0,
                        'stance_center_error': after['stance_center_x']-rec['native']['stance_center_x'],
                        'base_mask_all_variants_exact_translation': True}
    (T/'review/foot_alignment_checks.json').write_text(json.dumps(report, indent=2)+'\n')
sheet = Image.new('RGB', (8*192, 2*216), (40, 40, 40))
draw = ImageDraw.Draw(sheet)
for i, name in enumerate(manifest['frames']):
    im = Image.open(T/'runtime_aligned_2x'/(name+'.png')).convert('RGBA')
    a = np.asarray(im); c = a[:, :, :3].astype(float)
    band = (a[:, :, 3]>0)&(ndi.distance_transform_edt(a[:, :, 3]>=250)<=4)
    # Inspect the strongest residual matte-colored contour even when below native allowances.
    score = np.maximum(0, np.minimum(c[:, :, 0], c[:, :, 2])-c[:, :, 1])*a[:, :, 3]/255*band
    y, x = np.unravel_index(np.argmax(score), score.shape)
    crop = im.crop((x-24, y-24, x+24, y+24)).resize((192, 192), Image.Resampling.NEAREST)
    for row, bg_color in enumerate([(35, 35, 35, 255), (225, 225, 225, 255)]):
        bg = Image.new('RGBA', crop.size, bg_color); bg.alpha_composite(crop)
        sheet.paste(bg.convert('RGB'), (i*192, row*216+24))
        draw.text((i*192+4, row*216+4), name+' edge', fill='white')
sheet.save(T/'review/edges_light_dark.png')
print(checks)
