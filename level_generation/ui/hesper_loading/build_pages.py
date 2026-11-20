#!/usr/bin/env python3
"""Export the four chosen paintings with the native frame and a 50% loadprog fit review."""
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
SIZE = (1280, 960)
FILL = (346, 918, 944, 946)
CROP = (322, 896, 962, 960)
FEATHER = 8


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def progress_preview(page, fill):
    preview = page.convert('RGBA')
    preview.alpha_composite(fill.crop((0, 0, 299, 28)), FILL[:2])
    return preview.convert('RGB')


def main():
    manifest_path = PROJECT / 'generation_runs.json'
    manifest = json.loads(manifest_path.read_text())
    jobs = manifest['jobs']
    assert len(jobs) == 8
    native_path = ROOT / 'assets_dev/engine/icons_x2/loading2.png'
    fill_path = ROOT / 'assets_dev/engine/icons_x2/loadprog.png'
    with Image.open(native_path) as source:
        assert source.size == SIZE
        native = source.convert('RGB')
    with Image.open(fill_path) as source:
        assert source.size == (598, 28) and source.mode == 'RGBA'
        fill = source.copy()
    frame = native.crop(CROP)
    width, height = frame.size
    mask = Image.new('L', frame.size)
    # Feather only the crop's outside; every pixel of the gold frame and fill well stays native.
    mask.putdata([round(255 * min(1, min(x, y, width - 1 - x, height - 1 - y) / FEATHER))
                  for y in range(height) for x in range(width)])
    mask.save(PROJECT / 'review/frame_mask.png')
    native_frame = frame.convert('RGBA')
    native_frame.putalpha(mask)
    native_frame.save(PROJECT / 'review/native_frame.png')

    selected_sheet = Image.new('RGB', (1280, 1024), (20, 20, 25))
    candidate_sheet = Image.new('RGB', (1280, 2048), (20, 20, 25))
    selected_draw = ImageDraw.Draw(selected_sheet)
    candidate_draw = ImageDraw.Draw(candidate_sheet)
    for number in range(1, 5):
        output = f'selected/hes_loading{number}.png'
        candidates = [job for job in jobs if job['output'] == output]
        assert {job['candidate'] for job in candidates} == {1, 2}
        chosen = [job for job in candidates if job['selected']]
        assert len(chosen) == 1, output
        for job in candidates:
            path = PROJECT / job['file']
            assert job['status'] == 'generated' and digest(path) == job['sha256'], path
            assert job['selection_reason']
            with Image.open(path) as raw:
                assert list(raw.size) == job['size'] and raw.mode == job['mode']
                page = raw.convert('RGB').resize(SIZE, Image.Resampling.LANCZOS)
            x, y = (job['candidate'] - 1) * 640, (number - 1) * 512
            label = f"{job['id']} / {'SELECTED' if job['selected'] else 'alternate'}"
            candidate_draw.text((x + 12, y + 10), label, fill='white')
            candidate_sheet.paste(page.resize((640, 480), Image.Resampling.LANCZOS), (x, y + 32))
            if not job['selected']:
                continue
            original = page.copy()
            page.paste(frame, CROP[:2], mask)
            assert page.mode == 'RGB' and page.size == SIZE
            # The frame's protected centre matches the native page byte for byte, including its empty well.
            protected = (CROP[0] + FEATHER, CROP[1] + FEATHER, CROP[2] - FEATHER, CROP[3] - FEATHER)
            assert page.crop(protected).tobytes() == native.crop(protected).tobytes()
            assert page.crop((0, 0, 1280, CROP[1])).tobytes() == original.crop((0, 0, 1280, CROP[1])).tobytes()
            destination = PROJECT / output
            page.save(destination)
            destination.chmod(0o644)
            preview = progress_preview(page, fill)
            changed = ImageChops.difference(page, preview).getbbox()
            assert changed and FILL[0] <= changed[0] < changed[2] <= FILL[0] + 299
            assert FILL[1] <= changed[1] < changed[3] <= FILL[3]
            assert preview.crop((645, 918, 944, 946)).tobytes() == page.crop((645, 918, 944, 946)).tobytes()
            preview_path = PROJECT / f'review/hes_loading{number}_50.png'
            preview.save(preview_path)
            x, y = ((number - 1) % 2) * 640, ((number - 1) // 2) * 512
            selected_draw.text((x + 12, y + 10), f"hes_loading{number} / {job['key']} / 50%", fill='white')
            selected_sheet.paste(preview.resize((640, 480), Image.Resampling.LANCZOS), (x, y + 32))
            job['exports'] = {output: digest(destination), str(preview_path.relative_to(PROJECT)): digest(preview_path)}

    selected_sheet.save(PROJECT / 'review/selected_50_sheet.jpg', quality=95)
    candidate_sheet.save(PROJECT / 'review/candidates_sheet.jpg', quality=95)
    manifest['export'] = {'size': list(SIZE), 'mode': 'RGB', 'resampling': 'Pillow Lanczos, full frame',
                          'bar_crop': list(CROP), 'feather_pixels': FEATHER,
                          'bar_source_sha256': digest(native_path), 'loadprog_sha256': digest(fill_path),
                          'review_fill_rect': [346, 918, 299, 28], 'review_progress_percent': 50}
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    print('PASS: eight raw hashes, four RGB pages, native frame pixels, 50% fill bounds and review sheets')


if __name__ == '__main__':
    main()
