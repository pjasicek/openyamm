"""Compare installed decoration canvases and opaque anchors with the archived original BMPs.

Flags need visual review: original empty margins, suspended props and effect motion are intentional.
This tool changes no artwork or placement and needs only Pillow, like the restoration tools.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def inspect_images(native, enhanced):
    if native.mode != 'P':
        raise ValueError('Expected an original indexed BMP; palette index zero supplies transparency')
    before = native.point([0] + [255] * 255, 'L').getbbox()
    after = enhanced.convert('RGBA').getchannel('A').point(lambda a: 255 if a >= 192 else 0).getbbox()
    after = [value / 2 for value in after] if after else None
    report = dict(native_solid_bounds=before, enhanced_solid_bounds=after)
    flags = []
    if enhanced.size != tuple(value * 2 for value in native.size):
        flags.append('installed_canvas_differs_from_native')
    if bool(before) != bool(after):
        flags.append('opaque_geometry_missing_or_added')
    if before and after:
        delta = [actual - expected for actual, expected in zip(after, before)]
        report['solid_bounds_delta'] = delta
        if max(abs(value) for value in delta) > max(2, max(native.size) * .02):
            flags.append('opaque_bounds_drift_review_supports_and_proportions')
        drift = (enhanced.height / 2 - after[3]) - (native.height - before[3])
        report['bottom_margin_delta'] = drift
        if abs(drift) > 2:
            flags.append('bottom_anchor_drift_review')
    return report, flags


def scan_installed(assets):
    directory = assets / 'engine/decorations_x2'
    manifest = json.loads((directory / 'manifest.json').read_text())
    if manifest['pixels_per_logical_pixel'] != 2:
        raise ValueError('Expected the installed 2x decoration pack')
    originals = {path.stem.lower(): path for path in (assets / '_legacy/sprites_original').glob('*.bmp')}
    frames = []
    for binding in manifest['bindings']:
        frame = dict(name=binding['name'], palette_id=binding['palette_id'], file=binding['file'], flags=[])
        try:
            native_path = originals[binding['name'].lower()]
            path = directory / binding['file']
            frame['native'] = str(native_path.relative_to(assets))
            frame['native_sha256'] = hashlib.sha256(native_path.read_bytes()).hexdigest()
            with Image.open(native_path) as native, Image.open(path) as enhanced:
                frame['placement'], frame['flags'] = inspect_images(native, enhanced)
                frame['logical_size'] = list(native.size)
                if list(native.size) != binding['logical_size']:
                    frame['flags'].append('manifest_canvas_differs_from_native')
            if hashlib.sha256(path.read_bytes()).hexdigest() != binding['sha256']:
                frame['flags'].append('installed_hash_differs_from_manifest')
        except (KeyError, OSError) as error:
            frame['flags'].append('cannot_read_original_or_installed_image: ' + str(error))
        frames.append(frame)
    return dict(purpose='Native-relative placement review; flags do not authorize automatic art changes.',
                summary=dict(bindings_scanned=len(frames), flagged_bindings=sum(bool(f['flags']) for f in frames),
                             flags=dict(Counter(flag for frame in frames for flag in frame['flags']))), frames=frames)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'output/decoration_placement/installed-review.json')
    args = parser.parse_args()
    result = scan_installed(ROOT / 'assets_dev')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(**result['summary'], file=str(args.output)), indent=2))


if __name__ == '__main__':
    main()
