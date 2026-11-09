"""Reuse the reviewed sprite restoration and its native palette masks for Meshy references."""
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

stage = Path(__file__).resolve().parent
repo = stage.parents[3]
source = repo / 'level_generation/creatures/mm6_dmn/whole_sheet_review_v1/redo_2x'
spec = importlib.util.spec_from_file_location('demon_materials', source / 'materials.py')
materials = importlib.util.module_from_spec(spec)
spec.loader.exec_module(materials)
vectors = {p: np.fromfile(repo / f'assets_dev/engine/sprites_new/mm6_dmn/atlas/palette_{p}.rgba32f',
                         dtype='<f4').reshape(4, 256, 4)[:, :, :3] for p in (687, 686)}
records = {}
frames = json.loads((source / 'manifest.json').read_text())['frames']
for variant, palette in [('demon_a', 688), ('demon_b', 687), ('demon_c', 686)]:
    directory = stage / 'references' / variant
    directory.mkdir(parents=True, exist_ok=True)
    records[variant] = {'palette': palette, 'views': {}}
    for view, index, mirror in [('front', 0, False), ('left', 2, False), ('back', 4, False), ('right', 2, True)]:
        name = f'dmnstda{index}.png'
        image = Image.open(source / 'trimmed_2x' / name).convert('RGBA')
        mask = Image.open(source / 'masks_2x' / name).convert('RGBA')
        mask = mask.crop(frames[name[:-4]]['crop_in_aligned_px'])
        assert mask.size == image.size
        image = materials.recolor(image, mask, palette, {}, vectors)
        if mirror:
            image = ImageOps.mirror(image)
        # These are the existing material-mask palette variants, not generated 3D texture atlases.
        # Preserve restored pixels; only pad on a neutral background for the service input.
        canvas = Image.new('RGBA', (768, 768), (64, 70, 76, 255))
        canvas.alpha_composite(image, ((768 - image.width) // 2, (768 - image.height) // 2))
        output = directory / f'{view}.png'
        canvas.convert('RGB').save(output)
        records[variant]['views'][view] = {'path': str(output.relative_to(stage)), 'mirrored': mirror,
            'restored_source': str((source / 'trimmed_2x' / name).relative_to(repo)),
            'sha256': hashlib.sha256(output.read_bytes()).hexdigest()}
    request = {'model_url': '@file:variants_20261006/demon_neutral_upload.glb', 'ai_model': 'meshy-7',
               'enable_original_uv': True, 'enable_pbr': True, 'texture_resolution': '2k',
               'target_formats': ['glb'], 'multiview_image_urls':
                   [f'@file:variants_20261006/references/{variant}/{v}.png' for v in ('front', 'left', 'back', 'right')]}
    (stage / f'{variant}_request.json').write_text(json.dumps(request, indent=2) + '\n')
(stage / 'references.json').write_text(json.dumps(records, indent=2) + '\n')
print('Prepared four restored appearance views for each native palette; no new image generation.')
