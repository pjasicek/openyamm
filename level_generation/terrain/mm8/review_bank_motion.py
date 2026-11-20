"""Measure captured flat-bank cycles and produce comparison sheets for actual visual review."""
import argparse
import json
from PIL import ImageDraw
from common import P, Image, np, sha


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--require-complete', action='store_true')
    parser.add_argument('--extra-banks', action='store_true')
    args = parser.parse_args()
    stage_path = P / ('reports/bank_extra_fixture_stage.json' if args.extra_banks
                      else 'reports/bank_fixture_stage.json')
    stage = json.loads(stage_path.read_text())
    fixture = P / ('fixtures/banks_extra_v1' if args.extra_banks else 'fixtures/banks_v2')
    folder = fixture / 'captures'
    output = fixture / 'review'
    output.mkdir(exist_ok=True)
    results, pending = {}, []
    for name in stage['poses']:
        # This native patch has water only along its southern edge. Keep the same
        # visible shoreline crop for original/enhanced and exclude the HUD at x>=1200.
        roi = ((750, 720, 1200, 960) if args.extra_banks and 'shore_grey_patch1' in name
               else (400, 300, 1200, 920))
        meta_path = folder / ('mm8_' + name + '.json')
        burst_path = folder / ('mm8_' + name + '_cycle_frames.json')
        if not meta_path.exists() or not burst_path.exists():
            pending.append(name)
            continue
        meta, burst = json.loads(meta_path.read_text()), json.loads(burst_path.read_text())
        if 'fixture_stage_sha256' not in meta:
            pending.append(name)
            continue
        assert meta['fixture_stage_sha256'] == sha(stage_path)
        assert len(burst['screenshots']) == 40
        times = np.asarray(burst['captureElapsedSeconds'])
        assert times[-1] - times[0] > 3.5
        frames = [Image.open(folder / n).convert('RGB').crop(roi) for n in burst['screenshots']]
        pixels = np.asarray([np.asarray(im.resize((200, 155)), float) for im in frames])
        lags = [dict(lag=i, seconds=float(np.mean(times[i:] - times[:-i])),
                     mae=float(np.mean(abs(pixels[i:] - pixels[:-i])))) for i in range(1, 21)]
        best = min(lags[12:19], key=lambda r: r['mae'])
        ratio = best['mae'] / max(float(np.mean([r['mae'] for r in lags[3:12]])), 1e-6)
        temporal_std = float(pixels.std(0).mean())
        passed = temporal_std > .1 and abs(best['seconds'] - 14 * 15 / 128) < .12 and ratio < .4
        results[name] = dict(best_cycle=best, recurrence_ratio=ratio, temporal_std=temporal_std,
                             temporal_screen_passed=passed, lags=lags, roi=roi,
                             metadata_sha256=sha(meta_path), burst_sha256=sha(burst_path),
                             frames={n: sha(folder / n) for n in burst['screenshots']})
        durations = [max(1, round((times[i + 1] - times[i]) * 1000)) for i in range(39)] + [100]
        frames[0].save(output / (name + '.webp'), save_all=True, append_images=frames[1:],
                       duration=durations, loop=0, lossless=True)
        sheet = Image.new('RGB', (1200, 672), '#202933')
        draw = ImageDraw.Draw(sheet)
        for k, i in enumerate((0, 6, 13, 20, 27, 33)):
            x, y = k % 3 * 400, k // 3 * 336
            draw.text((x + 3, y + 3), 'frame %d %.2fs' % (i, times[i]), fill='white')
            sheet.paste(frames[i].resize((400, 310)), (x, y + 26))
        sheet.save(output / (name + '_samples.png'))
        print(name, 'cycle %.3fs ratio %.3f pass %s' % (best['seconds'], ratio, passed), flush=True)
    report = dict(scope='Stationary empty flat bank cycles; numerical temporal screen, visual review separate',
                  results=results, pending=pending, stage_sha256=sha(stage_path),
                  script_sha256=sha(P / 'review_bank_motion.py'))
    (output / 'motion.json').write_text(json.dumps(report, indent=2) + '\n')
    if args.require_complete:
        assert not pending, pending
        assert all(r['temporal_screen_passed'] for r in results.values())


if __name__ == '__main__':
    main()
