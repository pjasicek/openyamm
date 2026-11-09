"""Insert imagegen seam repairs and stabilize their detail across the native water loop."""
import hashlib
import importlib.util
import json
import shutil
from pathlib import Path

import numpy as np
import cv2
from PIL import Image, ImageDraw

P = Path(__file__).resolve().parent
PREVIOUS = P.parent / 'restoration_v2'
spec = importlib.util.spec_from_file_location('material_seams', P.parents[1] / 'seam_repair/build.py')
seams = importlib.util.module_from_spec(spec)
spec.loader.exec_module(seams)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def local_seams(frames):
    boundary, interior = [], []
    for frame in frames:
        for axis in (0, 1):
            a = frame.astype(float) if axis == 1 else frame.astype(float).transpose(1, 0, 2)
            for column in (0, *range(16, 241, 16)):
                b = np.roll(a, -column, axis=1)
                across = (b[:, -1] - b[:, 0]) ** 2
                nearby = np.concatenate([np.diff(b[:, -5:], axis=1), np.diff(b[:, :5], axis=1)], axis=1) ** 2
                target = boundary if column == 0 else interior
                for start in range(0, 241, 4):
                    target.append(float(np.sqrt(across[start:start + 16].mean())
                                        / max(1, np.sqrt(nearby[start:start + 16].mean()))))
    return {'boundary_p95': float(np.percentile(boundary, 95)), 'boundary_max': max(boundary),
            'interior_p95': float(np.percentile(interior, 95)),
            'interior_p999': float(np.percentile(interior, 99.9))}


def repair(frames):
    from scipy.sparse import lil_matrix
    from scipy.sparse.linalg import splu
    # Periodic Poisson insertion: preserve generated gradients inside the repaired cross,
    # retain accepted pixels outside, and avoid averaging two different wave patterns.
    yy, xx = np.mgrid[:256, :256]
    mask = (abs(xx - 127.5) < 24) | (abs(yy - 127.5) < 24)
    indices = np.full((256, 256), -1, dtype=int)
    indices[mask] = np.arange(mask.sum())
    rows, columns = np.where(mask)
    matrix = lil_matrix((mask.sum(), mask.sum()))
    matrix.setdiag(4)
    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        other = indices[(rows + dy) % 256, (columns + dx) % 256]
        valid = other >= 0
        matrix[np.arange(len(rows))[valid], other[valid]] = -1
    solve = splu(matrix.tocsc())
    atlas = Image.open(P / 'seam_repair_raw.png').convert('RGB')
    results = []
    for i, frame in enumerate(frames):
        original = np.roll(frame, (128, 128), (0, 1))
        x, y = i % 4, i // 4
        ai = np.asarray(atlas.crop((round(x * atlas.width / 4), round(y * atlas.height / 4),
                                   round((x + 1) * atlas.width / 4), round((y + 1) * atlas.height / 4)))
                        .resize((256, 256), Image.Resampling.LANCZOS), dtype=float)
        rhs = np.zeros_like(ai[mask])
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            sy, sx = (rows + dy) % 256, (columns + dx) % 256
            gradient = ai[mask] - ai[sy, sx]
            wraps = (rows + dy < 0) | (rows + dy >= 256) | (columns + dx < 0) | (columns + dx >= 256)
            # The imagegen atlas itself has independent cell edges. Do not import their
            # discontinuity as a new crease at the opposite ends of the repaired cross.
            continuation = 0.5 * (ai[(rows - dy) % 256, (columns - dx) % 256] - ai[mask]
                                  + ai[sy, sx] - ai[(sy + dy) % 256, (sx + dx) % 256])
            gradient[wraps] = continuation[wraps]
            rhs += gradient
            outside = ~mask[sy, sx]
            rhs[outside] += original[sy[outside], sx[outside]]
        result = original.copy()
        result[mask] = solve.solve(rhs)
        results.append(np.roll(result, (-128, -128), (0, 1)))
    return np.asarray(results)


def main():
    out = P / 'runtime_x2/worlds/mm6/terrain_x2'
    out.mkdir(parents=True, exist_ok=True)
    (P / 'authoring').mkdir(exist_ok=True)
    for f in (PREVIOUS / 'runtime_x2/worlds/mm6/terrain_x2').glob('*.png'):
        shutil.copy2(f, out / f.name)
    for f in (PREVIOUS / 'authoring').glob('6wtrdr*.png'):
        shutil.copy2(f, P / 'authoring' / f.name)
    before = np.array([np.asarray(Image.open(out / f'6hdwtr{i:03}.png').convert('RGB'), dtype=float) for i in range(14)])
    after = repair(before)
    # Remove frame-specific paint noise only in the repaired strips. Estimate motion on
    # repeated frames so the temporal filter also continues through the tile boundary.
    yy, xx = np.mgrid[:256, :256].astype(np.float32)
    distance = np.minimum.reduce([xx, yy, 255 - xx, 255 - yy])
    t = np.clip((24 - distance) / 8, 0, 1)
    weight = (t * t * (3 - 2 * t))[:, :, None]
    filtered = []
    for i, frame in enumerate(after):
        current_gray = cv2.cvtColor(np.uint8(np.clip(frame, 0, 255)), cv2.COLOR_RGB2GRAY)
        neighbours = []
        for j in ((i - 1) % 14, (i + 1) % 14):
            other_gray = cv2.cvtColor(np.uint8(np.clip(after[j], 0, 255)), cv2.COLOR_RGB2GRAY)
            flow = cv2.calcOpticalFlowFarneback(np.tile(current_gray, (3, 3)), np.tile(other_gray, (3, 3)),
                                               None, 0.5, 3, 21, 5, 7, 1.5, 0)[256:512, 256:512]
            neighbours.append(cv2.remap(after[j].astype(np.float32), xx + flow[:, :, 0], yy + flow[:, :, 1],
                                        cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP))
        filtered.append(frame + weight * (0.25 * neighbours[0] + 0.25 * neighbours[1] - 0.5 * frame))
    after = np.asarray(filtered)
    after = np.uint8(np.clip(np.rint(after), 0, 255))
    assert np.array_equal(after[:, 24:-24, 24:-24], before[:, 24:-24, 24:-24])
    for i, a in enumerate(after):
        name = f'6hdwtr{i:03}.png'
        Image.fromarray(a).save(out / name)
        Image.fromarray(a).save(P / 'authoring' / name)
    shutil.copy2(out / '6hdwtr000.png', out / '6wtrtyl.png')
    local = {'before': local_seams(before), 'after': local_seams(after)}
    assert local['after']['boundary_p95'] < 1.25 * local['after']['interior_p95']
    assert local['after']['boundary_max'] < 1.25 * local['after']['interior_p999']
    local['pass'] = True
    local['method'] = '16-pixel windows; boundary p95 and maximum must be within 1.25x interior p95 and p99.9.'
    (P / 'local_seams.json').write_text(json.dumps(local, indent=2) + '\n')
    sheet = Image.new('RGB', (7 * 256, 2 * 280), '#202933')
    draw = ImageDraw.Draw(sheet)
    for i, frame in enumerate(after):
        sheet.paste(Image.fromarray(np.roll(frame, (128, 128), (0, 1))), (i % 7 * 256, i // 7 * 280 + 24))
        draw.text((i % 7 * 256 + 6, i // 7 * 280 + 5), str(i), fill='white')
    sheet.save(P / 'all_frames_offset.png')
    for label, frames in [('before', before), ('after', after)]:
        views = [Image.fromarray(np.tile(a.astype('uint8'), (3, 3, 1))) for a in frames]
        views[0].save(P / (label + '_repeat.png'))
        views[0].save(P / (label + '_loop.webp'), save_all=True, append_images=views[1:], duration=117, loop=0, lossless=True)
        # Native edges in the centre, shown enlarged for local discontinuity inspection.
        Image.fromarray(np.roll(frames[0].astype('uint8'), (128, 128), (0, 1))).resize((1024, 1024)).save(P / (label + '_offset.png'))
    report = {'runtime_size': 256, 'method': 'Imagegen repairs offset seams across fourteen frames; periodic Poisson insertion preserves detailed gradients and unchanged interiors',
              'source_pack': '../restoration_v2', 'source_files': {f.name: sha(f) for f in (PREVIOUS / 'runtime_x2/worlds/mm6/terrain_x2').glob('*.png')},
              'files': {f.name: sha(f) for f in sorted(out.glob('*.png'))}, 'central_208_square_unchanged': True,
              'land_and_shore_unchanged': True, 'ai_tool': 'built-in imagegen', 'prompt': 'prompt.txt', 'repair_sha256': sha(P / 'seam_repair_raw.png'),
              'detail': {'water': {'after_border_detail_ratio': float(np.mean([seams.detail(a) for a in after]))}}}
    steps = [float(np.abs(after[(i + 1) % 14].astype(float) - after[i]).mean()) for i in range(14)]
    report['animation_steps'] = steps
    report['loop_step_ratio'] = steps[-1] / np.mean(steps)
    (P / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    manifest = json.loads((PREVIOUS / 'runtime_x2/manifest.json').read_text())
    manifest.update(iteration='native_water_v3', water=report['method'], files={'worlds/mm6/terrain_x2/' + n: h for n, h in report['files'].items()})
    (P / 'runtime_x2/manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'detail': report['detail'], 'loop_step_ratio': report['loop_step_ratio']}, indent=2))


if __name__ == '__main__':
    main()
