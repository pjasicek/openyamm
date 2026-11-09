"""Reproducible, translation-only registration of the reviewed planted-foot sequence."""
from pathlib import Path
import json
import shutil
import hashlib
import numpy as np
from PIL import Image

T = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def feet(im):
    alpha = np.asarray(im)[:, :, 3] >= 128
    bottom = int(np.where(alpha)[0].max())+1
    columns = np.any(alpha[bottom-20:bottom], axis=0)
    edges = np.diff(np.r_[False, columns, False].astype(int))
    runs = list(zip(np.where(edges == 1)[0], np.where(edges == -1)[0]))
    assert len(runs) == 2, ('Expected two visually verified planted feet', runs)
    centers = [float((left+right)/2) for left, right in runs]
    return {'sole_y': bottom, 'foot_centers_x': centers, 'stance_center_x': sum(centers)/2,
            'foot_runs_x': [[int(x), int(y)] for x, y in runs]}


def translate(im, offset):
    dx, dy = offset
    assert isinstance(dx, int) and isinstance(dy, int)
    out = Image.new(im.mode, im.size)
    out.paste(im, (dx, dy))
    # Exact inverse equality proves no foreground/mask pixels were clipped or changed.
    reverse = Image.new(im.mode, im.size)
    reverse.paste(out, (-dx, -dy))
    assert np.array_equal(np.asarray(im), np.asarray(reverse)), 'Translation clipped pixels'
    return out


def prepare():
    settings = T/'foot_alignment.json'
    if settings.exists():
        print('Reusing frozen foot landmarks and translations:', settings)
        return
    before = T/'before_alignment'
    before.mkdir(exist_ok=True)
    for folder in ['runtime_aligned_2x', 'masks_2x', 'previews', 'atlas', 'native_2x', 'previous_2x', 'review']:
        shutil.copytree(T/folder, before/folder, dirs_exist_ok=True)
    for name in ['manifest.json', 'viewer.html', 'registration.json', 'processing_settings.json']:
        shutil.copy2(T/name, before/name)
    manifest = json.loads((T/'manifest.json').read_text())
    registration = json.loads((T/'registration.json').read_text())
    records = {}
    for name in manifest['frames']:
        path = T/'runtime_aligned_2x'/(name+'.png')
        native_path = T/'native_2x'/(name+'.png')
        original, restored = feet(Image.open(native_path)), feet(Image.open(path))
        shift = [int(np.rint(original['stance_center_x']-restored['stance_center_x'])),
                 original['sole_y']-restored['sole_y']]
        corrected = feet(translate(Image.open(path), shift))
        assert corrected['sole_y'] == original['sole_y']
        assert abs(corrected['stance_center_x']-original['stance_center_x']) <= .5
        records[name] = {'native': original, 'before': restored, 'after': corrected,
                         'translation_2x_px': shift, 'source_sha256': sha(path),
                         'native_sha256': sha(native_path),
                         'selected_master_sha256': sha(T/registration['selected'][name]['image'])}
    data = {'method': 'Integer translation of entire frame, matching native sole baseline and mean of two foot centers.',
            'scope': 'Only the eight visually inspected front attack poses with both feet planted.',
            'landmarks': 'Alpha>=128; two occupied column runs in the bottom20 pixels. Foot center is each run midpoint.',
            'rounding': 'Nearest integer, ties to even; at most0.5 physical pixel stance-center residual.',
            'scale_change': 1, 'resampling': 'none', 'timing_change': 'none',
            'review_reference': 'before_alignment/review/feet_before.png', 'frames': records}
    settings.write_text(json.dumps(data, indent=2)+'\n')
    print({name: rec['translation_2x_px'] for name, rec in records.items()})


if __name__ == '__main__':
    prepare()
