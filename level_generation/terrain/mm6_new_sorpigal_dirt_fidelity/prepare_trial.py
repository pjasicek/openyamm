"""Create an isolated dirt comparison; never update the peasants playtest or accepted terrain package."""
import argparse
import configparser
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess

import numpy as np
from PIL import Image

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
TRANSITIONS = PROJECT.parent / 'mm6_new_sorpigal_transitions'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def linear(image):
    a = np.asarray(image, dtype=float) / 255
    return np.where(a <= .04045, a / 12.92, ((a + .055) / 1.055) ** 2.4)


def pixels(a):
    return np.rint(np.clip(np.where(a <= .0031308, a * 12.92,
                                   1.055 * np.maximum(a, 0) ** (1 / 2.4) - .055), 0, 1) * 255).astype('uint8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=Path('/tmp/openyamm-sorpigal-dirt-fidelity'))
    parser.add_argument('--snapshot', type=Path, default=Path('/tmp/openyamm-sorpigal-peasants-playtest'))
    args = parser.parse_args()
    stage = args.directory.resolve()
    snapshot = args.snapshot.resolve(strict=True)
    if stage.exists():
        raise FileExistsError('Use a new --directory; existing trial saves must be preserved')
    report = json.loads((snapshot / 'playtest_snapshot.json').read_text())
    assert report['world'] == 'mm6' and report['map'] == 'oute3.odm'
    export = PROJECT / 'runtime/terrain_x2'
    export.mkdir(exist_ok=True)
    old = linear(Image.open(TRANSITIONS / 'composites/v5/6dirttyl.png').convert('RGB'))
    new_image = Image.open(PROJECT / 'generated/dirt_v2_512.png').convert('RGB')
    new = linear(new_image)
    assert old.shape == new.shape == (512, 512, 3)
    records = {}
    # Reuse the existing reviewed coverage and baked boundary appearance for this diagnostic only.
    # This replaces the dirt contribution, without regenerating foreground materials or masks.
    for entry in json.loads((TRANSITIONS / 'mask_inventory.json').read_text())['masks']:
        name = entry['tile']
        source = TRANSITIONS / 'composites/v5' / (name + '.png')
        mask_path = TRANSITIONS / 'masks/connected_v4' / (name + '.png')
        coverage = np.asarray(Image.open(mask_path).convert('L'), dtype=float)[:, :, None] / 255
        base = linear(Image.open(source).convert('RGB'))
        result = pixels(base + (new - old) * (1 - coverage))
        # Pixels owned entirely by the foreground must survive the material replacement unchanged.
        assert np.array_equal(result[coverage[:, :, 0] == 1], pixels(base)[coverage[:, :, 0] == 1])
        output = export / (name + '.png')
        Image.fromarray(result).resize((256, 256), Image.Resampling.LANCZOS).save(output)
        records[name] = {'sha256': digest(output), 'mask_sha256': digest(mask_path),
                         'base_sha256': digest(source)}
    shutil.copy2(PROJECT / 'runtime/6dirttyl.png', export / '6dirttyl.png')
    records['6dirttyl'] = {'sha256': digest(export / '6dirttyl.png')}
    (PROJECT / 'runtime/trial_composition.json').write_text(json.dumps({
        'scope': 'Diagnostic dirt replacement only; not an accepted transition pack',
        'method': 'linear-light replacement of dirt contribution using unchanged connected_v4 coverage',
        'boundary_appearance': 'retained v5 baked boundary edits; no new boundary generation',
        'master': 'generated/dirt_v2_512.png', 'files': records}, indent=2) + '\n')
    stage.mkdir(parents=True)
    shutil.copy2(snapshot / 'openyamm', stage / 'openyamm')
    helper = Path('/tmp/sorpigal-transition-capture-save')
    if not helper.exists():
        subprocess.run(['python3', str(TRANSITIONS / 'build_pose_helper.py')], cwd=ROOT, check=True)
    pose_save = PROJECT / 'references/Dirt_View.oysav'
    subprocess.run([str(helper), str(snapshot / 'seed/New_Sorpigal_Start.oysav'), str(pose_save),
                    '-9728', '-11319', '161', str(math.radians(89.227)), str(math.radians(-9.626))], check=True)
    for mode in ['original', 'current', 'candidate']:
        run = stage / mode
        shutil.copytree(snapshot / 'enhanced', run, symlinks=True, ignore=shutil.ignore_patterns('saves'))
        (run / 'saves').mkdir()
        shutil.copy2(pose_save, run / 'saves/Dirt_View.oysav')
        settings = configparser.ConfigParser(interpolation=None)
        settings.read(run / 'settings.ini')
        settings['assets']['root'] = str(run / 'assets_dev')
        settings['startup']['start_in_main_menu'] = 'true'
        settings['video_quality']['terrain'] = 'x1' if mode == 'original' else 'x2'
        with (run / 'settings.ini').open('w') as stream:
            settings.write(stream, space_around_delimiters=False)
        if mode == 'candidate':
            target = run / 'assets_dev/worlds/mm6/terrain_x2'
            assert not target.is_symlink()
            for source in export.glob('*.png'):
                assert not (target / source.name).is_symlink()
                shutil.copy2(source, target / source.name)
    (stage / 'dirt_trial.json').write_text(json.dumps({
        'source_snapshot': str(snapshot), 'binary_sha256': digest(stage / 'openyamm'),
        'pose_save_sha256': digest(pose_save), 'modes': ['original', 'current', 'candidate'],
        'other_visuals': 'identical enhanced snapshot settings and art in all three modes'}, indent=2) + '\n')
    print('Prepared independent original/current/candidate dirt comparison at', stage)


if __name__ == '__main__':
    main()
