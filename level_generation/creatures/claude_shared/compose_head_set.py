#!/usr/bin/env python3
"""Head texture set, step 2 (CLAUDE_CREATURE_TEXTURES.md "Head-only retexture") for characters whose skin does not
change between tiers (peasants, mages): 1K head maps from the head-only Meshy retexture, graded like the body and
brightness-matched to the body across the neck seam (head_seam_gain.py, measured on the master's boundary faces).

Writes <textures>/<prefix>_head_basecolor_graded.png, _head_normal_1k.png, _head_metal_rough_1k.png (R 1,
G roughness, B metallic) and <prefix>_head_seam.json. The project export assigns them to the head material.
Usage: compose_head_set.py <project> <prefix> <master.blend> <mesh> <body base colour png> [--textures <dir>]
                           [grade options...]
--textures is the project's texture folder (default textures/). --seam-gain <value> replaces the measured seam gain:
use it when the head/body boundary runs between different materials (cockatrice: pale ruff feathers on the body side,
pink neck skin on the head side measured 1.84, which brightened the head). Grade options are passed to
grade_basecolor.py (AO is not used: --ao-strength 0)."""
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import region_variants as R

SIZE = 1024
BLENDER = '/snap/bin/blender'


def save(array, path, mode='RGB'):
    Image.fromarray(np.clip(array * 255 + 0.5, 0, 255).astype(np.uint8), mode).save(path, optimize=True)


def main():
    project, prefix, master, mesh, body = Path(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
    grade = sys.argv[6:]
    T = project / 'textures'
    if grade[:1] == ['--textures']:
        T, grade = project / grade[1], grade[2:]
    forced_gain = None
    if grade[:1] == ['--seam-gain']:
        forced_gain, grade = float(grade[1]), grade[2:]
    # HEAD_RETEX_JOB picks a later head retexture of the project (default the first one)
    source = project / 'meshy' / os.environ.get('HEAD_RETEX_JOB', 'head_retexture_v1') / 'texture_urls_0'
    raw = T / f'{prefix}_head_basecolor.png'
    save(R.load_srgb(str(source) + '_base_color.png', SIZE), raw)
    white = T / f'{prefix}_head_no_ao.png'
    Image.new('L', (SIZE, SIZE), 255).save(white)
    subprocess.run([sys.executable, str(HERE / 'grade_basecolor.py'), '--ao', str(white), '--ao-strength', '0',
                    *grade, str(raw)], check=True)
    white.unlink()
    graded = T / f'{prefix}_head_basecolor_graded.png'

    seam_path = T / f'{prefix}_head_seam.json'
    subprocess.run([BLENDER, '--background', str(project / master), '--python', str(HERE / 'head_seam_gain.py'),
                    '--', '--mesh', mesh, '--body', str(Path(body).resolve()), '--head', str(graded.resolve()),
                    '--out', str(seam_path)], check=True, capture_output=True)
    seam = json.loads(seam_path.read_text())
    gain = forced_gain if forced_gain is not None else float(np.clip(seam['luminance_gain'], 0.6, 1.6))
    linear = R.srgb_to_linear(R.load_srgb(graded)) * gain
    encode = lambda v: np.where(v <= 0.0031308, v * 12.92, 1.055 * np.maximum(v, 0) ** (1 / 2.4) - 0.055)
    save(encode(np.clip(linear, 0, 1)), graded)

    save(R.load_srgb(str(source) + '_normal.png', SIZE), T / f'{prefix}_head_normal_1k.png')
    channel = lambda name: np.asarray(Image.open(f'{source}_{name}.png').convert('L').resize(
        (SIZE, SIZE), Image.LANCZOS), np.float64) / 255
    rough, metal = channel('roughness'), channel('metallic')
    save(np.stack([np.ones_like(rough), rough, metal], -1), T / f'{prefix}_head_metal_rough_1k.png')
    print(json.dumps({'seam_edges': seam['edges'], 'luminance_gain': round(gain, 3)}))


if __name__ == '__main__':
    main()
