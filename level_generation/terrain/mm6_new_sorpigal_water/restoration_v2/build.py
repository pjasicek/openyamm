"""Conservative native-frame water restoration; retain the reviewed land and shore pack."""
import hashlib
import json
import shutil
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter

P = Path(__file__).resolve().parent
T = P.parents[1]
BASE = T / 'seam_repair'
SOURCE = T / 'mm6_new_sorpigal/water_animation/png'
sys.path.insert(0, str(BASE))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def byte(a):
    return np.uint8(np.clip(np.rint(a), 0, 255))


def detail(a):
    hi = a - gaussian_filter(a, (1, 1, 0), mode='wrap')
    mask = np.zeros(a.shape[:2], bool)
    mask[:4] = mask[-4:] = True
    mask[:, :4] = mask[:, -4:] = True
    return float(np.sqrt(np.mean(hi[mask] ** 2)) / np.sqrt(np.mean(hi[16:-16, 16:-16] ** 2)))


def periodic_residual(a):
    """Remove the smooth boundary-discontinuity component without averaging detail strips."""
    boundary = np.zeros_like(a)
    boundary[0] = a[-1] - a[0]
    boundary[-1] = a[0] - a[-1]
    boundary[:, 0] += a[:, -1] - a[:, 0]
    boundary[:, -1] += a[:, 0] - a[:, -1]
    fy = 2 * np.pi * np.arange(a.shape[0]) / a.shape[0]
    fx = 2 * np.pi * np.arange(a.shape[1]) / a.shape[1]
    denominator = 2 * np.cos(fy[:, None]) + 2 * np.cos(fx[None, :]) - 4
    denominator[0, 0] = 1
    spectrum = np.fft.fft2(boundary, axes=(0, 1)) / denominator[:, :, None]
    spectrum[0, 0] = 0
    return a - np.fft.ifft2(spectrum, axes=(0, 1)).real


def main():
    out = P / 'runtime_x2/worlds/mm6/terrain_x2'
    out.mkdir(parents=True, exist_ok=True)
    (P / 'authoring').mkdir(exist_ok=True)
    for source in (BASE / 'runtime_x2/worlds/mm6/terrain_x2').glob('*.png'):
        shutil.copy2(source, out / source.name)
    for source in (BASE / 'authoring').glob('6wtrdr*.png'):
        shutil.copy2(source, P / 'authoring' / source.name)
    atlas = Image.open(P / 'restored_atlas_raw.png').convert('RGB')
    original, restored, checks = [], [], []
    yy, xx = np.mgrid[:256, :256].astype(np.float32)
    for i in range(14):
        name = f'6hdwtr{i:03}'
        source = SOURCE / (name + '.png')
        native = np.asarray(Image.open(source).convert('RGB'), dtype=float)
        x, y = i % 4, i // 4
        ai = np.asarray(atlas.crop((round(x * atlas.width / 4), round(y * atlas.height / 4),
                                   round((x + 1) * atlas.width / 4), round((y + 1) * atlas.height / 4)))
                        .resize((256, 256), Image.Resampling.LANCZOS), dtype=float)
        # Register small generated offsets to the actual native wave locations.
        flow = cv2.calcOpticalFlowFarneback(cv2.cvtColor(byte(native), cv2.COLOR_RGB2GRAY),
                                           cv2.cvtColor(byte(ai), cv2.COLOR_RGB2GRAY), None,
                                           0.5, 3, 21, 5, 7, 1.5, 0)
        ai = cv2.remap(ai.astype(np.float32), xx + flow[:, :, 0], yy + flow[:, :, 1],
                       cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP).astype(float)
        # Preserve native colour and broad forms. Only the bounded fine-detail residual is added.
        delta = ai - native
        delta -= gaussian_filter(delta, (3, 3, 0), mode='wrap')
        delta = periodic_residual(np.clip(delta * 0.65, -22, 22))
        a = byte(native + delta)
        Image.fromarray(a).save(out / (name + '.png'))
        Image.fromarray(a).save(P / 'authoring' / (name + '.png'))
        original.append(native)
        restored.append(a.astype(float))
        correlation = float(np.corrcoef(gaussian_filter(native, (3, 3, 0)).ravel(),
                                        gaussian_filter(a.astype(float), (3, 3, 0)).ravel())[0, 1])
        checks.append({'frame': name, 'native_sha256': digest(source), 'broad_colour_correlation': correlation,
                       'mean_rgb_shift': (a.mean(axis=(0, 1)) - native.mean(axis=(0, 1))).tolist(),
                       'border_detail_ratio': detail(a.astype(float))})
    shutil.copy2(out / '6hdwtr000.png', out / '6wtrtyl.png')
    steps = [float(np.abs(restored[(i + 1) % 14] - restored[i]).mean()) for i in range(14)]
    native_steps = [float(np.abs(original[(i + 1) % 14] - original[i]).mean()) for i in range(14)]
    assert min(c['broad_colour_correlation'] for c in checks) > 0.995
    assert max(abs(v) for c in checks for v in c['mean_rgb_shift']) < 1
    assert all(0.85 < a / b < 1.15 for a, b in zip(steps, native_steps))
    for name, frames in [('native_loop', original), ('restored_loop', restored)]:
        images = [Image.fromarray(np.tile(byte(a), (2, 2, 1))) for a in frames]
        images[0].save(P / (name + '.webp'), save_all=True, append_images=images[1:], duration=117, loop=0, lossless=True)
    sheet = Image.new('RGB', (1024, 550), '#202933')
    draw = ImageDraw.Draw(sheet)
    for x, a, label in [(0, original[0], 'Original native frame'), (512, restored[0], 'Conservative restoration')]:
        sheet.paste(Image.fromarray(np.tile(byte(a), (2, 2, 1))), (x, 30))
        draw.text((x + 10, 7), label, fill='white')
    sheet.save(P / 'comparison.png')
    files = {p.name: digest(p) for p in sorted(out.glob('*.png'))}
    report = {'runtime_size': 256, 'method': 'Native frames plus registered, bounded AI fine-detail residual; no synthetic deformation',
              'ai_tool': 'built-in imagegen', 'prompt': 'prompt.txt', 'raw_atlas_sha256': digest(P / 'restored_atlas_raw.png'),
              'files': files, 'frame_checks': checks, 'animation_steps': steps, 'native_animation_steps': native_steps,
              'loop_step_ratio': steps[-1] / np.mean(steps),
              'detail': {'water': {'after_border_detail_ratio': float(np.mean([c['border_detail_ratio'] for c in checks]))}},
              'land_and_shore_unchanged': True, 'frame_ticks': 15, 'ticks_per_second': 128}
    (P / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    manifest = json.loads((BASE / 'runtime_x2/manifest.json').read_text())
    manifest.update(iteration='native_water_v2', water=report['method'],
                    files={'worlds/mm6/terrain_x2/' + n: h for n, h in files.items()})
    (P / 'runtime_x2/manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'mean_border_detail': report['detail'], 'loop_ratio': report['loop_step_ratio'],
                      'min_colour_correlation': min(c['broad_colour_correlation'] for c in checks)}, indent=2))


if __name__ == '__main__':
    main()
