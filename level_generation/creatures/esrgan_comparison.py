"""Build review-only Real-ESRGAN frames from an existing creature manifest."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt
import torch
from torchvision.transforms import functional

sys.modules['torchvision.transforms.functional_tensor'] = functional

from basicsr.archs.rrdbnet_arch import RRDBNet
from realesrgan import RealESRGANer


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def union_crops(manifest: dict, native_dir: Path, palette: str) -> dict[str, tuple[int, int, int, int]]:
    crops = {}
    for action in manifest['animations'].values():
        for sequence in action['views'].values():
            names = [step['frame'] for step in sequence]
            boxes = []
            for name in names:
                with Image.open(native_dir / f'{name}_{palette}.png') as image:
                    box = image.getchannel('A').getbbox()
                if box:
                    boxes.append(box)
            if not boxes:
                continue
            width, height = manifest['logical_canvas']
            box = (max(0, min(b[0] for b in boxes) - 12),
                   max(0, min(b[1] for b in boxes) - 12),
                   min(width, max(b[2] for b in boxes) + 12),
                   min(height, max(b[3] for b in boxes) + 12))
            for name in names:
                crops.setdefault(name, box)
    return crops


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('package', type=Path, help='Existing creature package containing manifest.json and native_variants')
    parser.add_argument('--palette', default='745')
    parser.add_argument('--weights', type=Path, default=Path('/tmp/RealESRGAN_x4plus.pth'))
    parser.add_argument('--limit', type=int, default=0, help='Generate first N frames for a smoke check')
    args = parser.parse_args()

    package = args.package.resolve()
    manifest = json.loads((package / 'manifest.json').read_text())
    native_dir = package / 'native_variants'
    output = package / 'esrgan_comparison'
    frames_dir = output / 'frames'
    frames_dir.mkdir(parents=True, exist_ok=True)
    crops = union_crops(manifest, native_dir, args.palette)
    names = sorted(manifest['frames'])
    if args.limit:
        names = names[:args.limit]

    model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
    torch.set_num_threads(8)
    upsampler = RealESRGANer(scale=4, model_path=str(args.weights), model=model,
                            tile=128, tile_pad=10, pre_pad=0, half=False, device='cpu')
    records = []
    width, height = manifest['logical_canvas']
    for index, name in enumerate(names, 1):
        native_path = native_dir / f'{name}_{args.palette}.png'
        candidate_path = frames_dir / f'{name}.png'
        box = crops[name]
        if not candidate_path.exists():
            with Image.open(native_path) as image:
                cropped = image.convert('RGBA').crop(box)
            pixels = np.asarray(cropped)
            opaque = pixels[:, :, 3] > 0
            if not opaque.any():
                raise ValueError(f'Empty native frame: {name}')
            _, nearest = distance_transform_edt(~opaque, return_indices=True)
            rgb = pixels[nearest[0], nearest[1], :3].copy()
            enhanced, _ = upsampler.enhance(rgb[:, :, ::-1].copy(), outscale=2)
            candidate = Image.fromarray(enhanced[:, :, ::-1], 'RGB').convert('RGBA')
            candidate.putalpha(cropped.getchannel('A').resize(candidate.size, Image.Resampling.LANCZOS))
            canvas = Image.new('RGBA', (width * 2, height * 2))
            canvas.paste(candidate, (box[0] * 2, box[1] * 2))
            canvas.save(candidate_path)
        with Image.open(candidate_path) as candidate:
            if candidate.size != (width * 2, height * 2):
                raise ValueError(f'Unexpected size: {candidate_path}')
        records.append({'name': name, 'native_sha256': sha256(native_path),
                        'esrgan_sha256': sha256(candidate_path), 'union_crop': box})
        print(f'{index}/{len(names)} {name}', flush=True)

    sources_path = package / 'sources.json'
    if sources_path.is_file():
        aliases = json.loads(sources_path.read_text()).get('pixel_aliases', {})
        by_name = {record['name']: record for record in records}
        for name, target in aliases.items():
            if name not in by_name or target not in by_name:
                continue
            shutil.copyfile(frames_dir / f'{target}.png', frames_dir / f'{name}.png')
            by_name[name]['esrgan_sha256'] = sha256(frames_dir / f'{name}.png')
            by_name[name]['pixel_alias_of'] = target
            by_name[name]['union_crop'] = by_name[target]['union_crop']

    (output / 'manifest.json').write_text(json.dumps({
        'schema': 'openyamm.creature_esrgan_comparison.v1',
        'status': 'review_only',
        'source_package': str(package),
        'source_manifest_sha256': sha256(package / 'manifest.json'),
        'palette': args.palette,
        'model': 'RealESRGAN_x4plus',
        'weights_sha256': sha256(args.weights),
        'method': '4x RGB model output downsampled to 2x; native alpha resampled to 2x; action/view union crop retained at original canvas coordinates',
        'frames': records,
    }, indent=2) + '\n')
    if not args.limit:
        template = (Path(__file__).resolve().parent / 'esrgan_comparison_viewer.html').read_text()
        if template.count('/* MANIFEST */') != 1:
            raise ValueError('Viewer template must have exactly one manifest marker')
        viewer_data = {'package': manifest, 'palette': args.palette}
        (output / 'review.html').write_text(template.replace('/* MANIFEST */',
                                                           json.dumps(viewer_data, separators=(',', ':'))))


if __name__ == '__main__':
    main()
