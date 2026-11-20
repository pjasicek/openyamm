"""Reproducible native minimap model comparison; never writes accepted/runtime assets."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = HERE.parent
PAD = 16
TRIALS = {
    'mm7/out09', 'mm7/out14', 'mm7/7out02', 'mm7/7out06',
    'mm8/out02', 'mm8/out05', 'mm8/out04', 'mm8/elemw',
}
MODELS = {
    'video2': ('Anime-video v3, direct 2x', 'realesr-animevideov3', 2, False),
    'video4': ('Anime-video v3, 4x to 2x', 'realesr-animevideov3', 4, False),
    'general4': ('General x4plus, 4x to 2x', 'realesrgan-x4plus', 4, False),
    'anime4': ('Anime x4plus, 4x to 2x', 'realesrgan-x4plus-anime', 4, False),
    'video2_tta': ('Anime-video v3, 2x + TTA', 'realesr-animevideov3', 2, True),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_json(path, data):
    path.write_text(json.dumps(data, indent=2) + '\n')


def prepare():
    rows = json.loads((BASE / 'scope.json').read_text())['records']
    accepted = json.loads((ROOT / 'level_generation/ui/hud_inventory/accepted_icons.json').read_text())['records']
    if not (HERE / 'runtime_before.json').exists():
        runtime = {}
        for row in rows:
            path = ROOT / accepted[row['target']]['runtime_output_path']
            runtime[str(path.relative_to(ROOT))] = sha(path)
        save_json(HERE / 'runtime_before.json', runtime)
    records = []
    input_dir = HERE / 'input'
    input_dir.mkdir(exist_ok=True)
    for row in rows:
        if row['world'] == 'mm6':
            continue
        stem = Path(row['map']).stem
        key = f"{row['world']}/{stem}"
        directory = HERE / 'maps' / key
        directory.mkdir(parents=True, exist_ok=True)
        native = ROOT / 'assets_legacy/icons_20260926/worlds' / row['world'] / 'icons' / f'{stem}.bmp'
        original = Image.open(native).convert('RGB')
        assert np.array_equal(np.array(original), np.array(Image.open(BASE / row['directory'] / 'original.png')))
        original.save(directory / 'original.png')
        size = tuple(v * 2 for v in original.size)
        assert list(size) == row['x2_size']
        original.resize(size, Image.Resampling.NEAREST).save(directory / 'nearest.png')
        original.resize(size, Image.Resampling.LANCZOS).save(directory / 'lanczos.png')
        record = dict(row, key=key, id=key.replace('/', '_'), trial=key in TRIALS,
                      source=str(native.relative_to(ROOT)), source_sha256=sha(native),
                      original_sha256=sha(directory / 'original.png'))
        records.append(record)
        if key in TRIALS:
            padded = np.pad(np.array(original), ((PAD, PAD), (PAD, PAD), (0, 0)), mode='reflect')
            Image.fromarray(padded).save(input_dir / f"{record['id']}.png")
    save_json(HERE / 'scope.json', {'records': records, 'count': len(records), 'trial_count': len(TRIALS)})
    for model in MODELS:
        (HERE / 'raw' / model).mkdir(parents=True, exist_ok=True)
    commands = []
    for key, (_, name, scale, tta) in MODELS.items():
        command = (
            'tools/upscaling/realesrgan-ncnn-vulkan '
            f'-i {input_dir.relative_to(ROOT)} -o {(HERE / "raw" / key).relative_to(ROOT)} '
            f'-n {name} -s {scale} -m tools/upscaling/models -g 0 -j 1:1:1 -t 0'
        )
        commands.append(command + (' -x' if tta else ''))
    (HERE / 'commands.txt').write_text('\n'.join(commands) + '\n')
    print(f'Prepared {len(TRIALS)} trials; all {len(records)} native sources retained.')


def translation(original, candidate):
    left = gaussian_filter(np.array(original).mean(2), 2)
    right = gaussian_filter(np.array(candidate).mean(2), 2)
    left -= left.mean()
    right -= right.mean()
    cross = np.fft.fft2(left) * np.conj(np.fft.fft2(right))
    correlation = np.fft.ifft2(cross / np.maximum(np.abs(cross), 1e-10)).real
    y, x = np.unravel_index(np.argmax(correlation), correlation.shape)
    return [int(x if x <= left.shape[1] // 2 else x - left.shape[1]),
            int(y if y <= left.shape[0] // 2 else y - left.shape[0])]


def finish():
    scope = json.loads((HERE / 'scope.json').read_text())
    previous = {}
    if (HERE / 'exports.json').exists():
        previous = {r['id']: r['variants'] for r in json.loads((HERE / 'exports.json').read_text())['records']}
    exports = []
    for row in scope['records']:
        directory = HERE / 'maps' / row['key']
        original = Image.open(directory / 'original.png').convert('RGB')
        lanczos = Image.open(directory / 'lanczos.png').convert('RGB')
        variants = {}
        for key, (label, model, scale, tta) in MODELS.items():
            raw_path = HERE / 'raw' / key / f"{row['id']}.png"
            if not raw_path.exists():
                continue
            cached = previous.get(row['id'], {}).get(key, {})
            if (cached.get('raw_sha256') == sha(raw_path) and
                    cached.get('master_sha256') == sha(directory / f'{key}_master.png') and
                    cached.get('x2_sha256') == sha(directory / f'{key}.png')):
                variants[key] = cached
                continue
            raw = Image.open(raw_path).convert('RGB')
            assert raw.size == ((original.width + PAD * 2) * scale, (original.height + PAD * 2) * scale)
            master = raw.crop((PAD * scale, PAD * scale,
                               (original.width + PAD) * scale, (original.height + PAD) * scale))
            master.save(directory / f'{key}_master.png')
            candidate = master.resize(lanczos.size, Image.Resampling.LANCZOS)
            candidate.save(directory / f'{key}.png')
            variant = {
                'label': label, 'model': model, 'scale': scale, 'tta': tta,
                'raw_sha256': sha(raw_path), 'master_sha256': sha(directory / f'{key}_master.png'),
                'x2_sha256': sha(directory / f'{key}.png'),
                'whole_frame_translation_x2_px': translation(lanczos, candidate),
                'mean_rgb_difference_255': np.round(np.array(candidate).mean((0, 1)) -
                                                    np.array(lanczos).mean((0, 1)), 3).tolist(),
            }
            model_stem = f'{model}-x{scale}' if model == 'realesr-animevideov3' else model
            variant['model_sha256'] = {
                ext: sha(ROOT / 'tools/upscaling/models' / f'{model_stem}.{ext}') for ext in ['bin', 'param']
            }
            variants[key] = variant
        if variants:
            exports.append(dict(row, variants=variants))
    unchanged = all(sha(ROOT / path) == digest for path, digest in
                    json.loads((HERE / 'runtime_before.json').read_text()).items())
    assert unchanged, 'Runtime changed during evaluation; inspect before reporting unchanged.'
    save_json(HERE / 'exports.json', {
        'status': 'model_comparison_only', 'runtime_42_unchanged': unchanged,
        'binary_sha256': sha(ROOT / 'tools/upscaling/realesrgan-ncnn-vulkan'),
        'records': exports, 'pad_native_px': PAD,
        'registration_limit': 'Whole-frame translation does not prove absence of local neural shape changes.',
    })
    print(f'Exported {sum(len(r["variants"]) for r in exports)} candidates on {len(exports)} maps.')


def blend():
    data = json.loads((HERE / 'exports.json').read_text())
    for row in data['records']:
        directory = HERE / 'maps' / row['key']
        lanczos = Image.open(directory / 'lanczos.png').convert('RGB')
        neural = Image.open(directory / 'video2.png').convert('RGB')
        for strength in [50, 75]:
            key = f'video2_mix{strength}'
            result = Image.blend(lanczos, neural, strength / 100)
            result.save(directory / f'{key}.png')
            row['variants'][key] = {
                'label': f'Anime-video 2x / {strength}% neural + {100 - strength}% original',
                'neural_fraction': strength / 100, 'neural_source': 'video2',
                'baseline': 'lanczos', 'x2_sha256': sha(directory / f'{key}.png'),
                'whole_frame_translation_x2_px': translation(lanczos, result),
            }
    save_json(HERE / 'exports.json', data)
    print('Added 50% and 75% neural-strength comparisons.')


def expand():
    records = json.loads((HERE / 'scope.json').read_text())['records']
    directory = HERE / 'remaining_input'
    directory.mkdir(exist_ok=True)
    for row in records:
        if row['trial']:
            continue
        original = np.array(Image.open(HERE / 'maps' / row['key'] / 'original.png').convert('RGB'))
        padded = np.pad(original, ((PAD, PAD), (PAD, PAD), (0, 0)), mode='reflect')
        Image.fromarray(padded).save(directory / f"{row['id']}.png")
    print('Prepared remaining 19 inputs for the shortlisted direct-2x model.')


def select():
    data = json.loads((HERE / 'exports.json').read_text())
    assert len(data['records']) == 27
    chosen = 'video2'
    recipe = {
        'status': 'explicit_user_selected_for_mm7_mm8_batch',
        'model': 'realesr-animevideov3', 'scale': 2, 'tta': False,
        'tile_size': 0, 'gpu_id': 0, 'threads': '1:1:1', 'reflection_pad_native_px': PAD,
        'pre_denoise': False, 'post_sharpen': False, 'colour_grade': False,
        'blend': {'esrgan': 1.0, 'original_lanczos_x2': 0.0},
        'model_sha256': data['records'][0]['variants']['video2']['model_sha256'],
        'binary_sha256': data['binary_sha256'],
        'native_source': 'Archived original BMP decoded to RGB; never an earlier generated replacement.',
        'canvas': 'Exactly 2x native width and height; no repositioning, warping or trimming.',
    }
    save_json(HERE / 'approved_recipe.json', recipe)
    registration = []
    for row in data['records']:
        directory = HERE / 'maps' / row['key']
        assert sha(ROOT / row['source']) == row['source_sha256']
        for key, variant in row['variants'].items():
            path = directory / f'{key}.png'
            assert sha(path) == variant['x2_sha256']
            assert list(Image.open(path).size) == row['x2_size']
        reference = gaussian_filter(np.asarray(Image.open(directory / 'lanczos.png')).mean(2), 2)
        candidate = gaussian_filter(np.asarray(Image.open(directory / f'{chosen}.png')).mean(2), 2)
        errors = []
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                shifted = np.roll(candidate, (dy, dx), (0, 1))
                error = float(np.mean((reference[4:-4, 4:-4] - shifted[4:-4, 4:-4]) ** 2))
                errors.append((error, dx, dy))
        errors.sort()
        assert errors[0][1:] == (0, 0), row['key']
        registration.append({
            'map': row['key'], 'minimum_error_shift_x2_px': list(errors[0][1:]),
            'phase_correlation_shift_x2_px': row['variants'][chosen]['whole_frame_translation_x2_px'],
            'zero_shift_smoothed_luma_mse': errors[0][0], 'next_best_shift_mse': errors[1][0],
        })
        destination = HERE / 'recommended' / row['world'] / (Path(row['map']).stem + '.png')
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(directory / f'{chosen}.png', destination)
        destination.chmod(0o644)
        row['recommended'] = str(destination.relative_to(HERE))
    before = json.loads((HERE / 'runtime_before.json').read_text())
    assert all(sha(ROOT / path) == digest for path, digest in before.items())
    data['recommended'] = chosen
    data['recommendation'] = (
        'User selected: anime-video v3, direct 2× at full strength. '
        'All 27 MM7/MM8 maps use the original paintings; MM6 retains its approved Blender treatment.'
    )
    save_json(HERE / 'exports.json', data)
    save_json(HERE / 'validation.json', {
        'result': 'PASS', 'native_sources_checked': 27, 'recommended_candidates': 27,
        'exports_sha256': sha(HERE / 'exports.json'),
        'candidate_canvases_and_hashes_checked': sum(len(r['variants']) for r in data['records']),
        'original_runtime_files_unchanged': len(before),
        'minimum_error_registration': registration,
        'phase_outliers': [r for r in registration if r['phase_correlation_shift_x2_px'] != [0, 0]],
        'limitation': 'Global registration and exact canvases do not guarantee unchanged local neural contours.',
    })
    print('27 recommended candidates checked and retained. All 42 installed minimaps unchanged.')


def contacts():
    rows = json.loads((HERE / 'exports.json').read_text())['records']
    (HERE / 'contacts').mkdir(exist_ok=True)
    for row in rows:
        directory = HERE / 'maps' / row['key']
        keys = ['nearest', 'lanczos'] + list(row['variants'])
        width, height = 384, 408
        sheet = Image.new('RGB', (width * 3, height * ((len(keys) + 2) // 3)), '#20242a')
        draw = ImageDraw.Draw(sheet)
        for i, key in enumerate(keys):
            image = Image.open(directory / f'{key}.png')
            image.thumbnail((width, width), Image.Resampling.LANCZOS)
            x, y = (i % 3) * width, (i // 3) * height
            sheet.paste(image, (x, y + 24))
            draw.text((x + 6, y + 5), f"{row['name']} / {key}", fill='white')
        sheet.save(HERE / 'contacts' / f"{row['id']}.jpg", quality=94)
    print('Contact sheets written.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'finish', 'blend', 'expand', 'select', 'contacts'])
    action = parser.parse_args().action
    if (HERE / 'accepted.json').exists() and action != 'contacts':
        raise SystemExit('Published revision is immutable. Make a new dated workspace for another revision.')
    globals()[action]()
