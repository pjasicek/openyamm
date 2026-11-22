#!/usr/bin/env python3
"""Decision D-3.1 (devdocs/xeen/DECISIONS.md, 2026-11-20): the royal kit's arms follow the source's castle wall sets.

    derive_d3.py newcastle    Codex edits of the first Burlock art (a white tower on blue under a crown, kept in
                              work/d3_before/) with the crown taken off: xkncscrst, xkncsban (raw/<name>_v1.png)
    derive_d3.py finish       raw -> finished/<name>.png (4x), _x2, _x1 for the two Newcastle textures
    derive_d3.py kalindra     recolour xkkalcrst and xkkalban from crimson to Kalindra's purple (no new art)

Burlock's own arms (a gold griffin rampant on red) are regenerated through xtex.py (specs.yml, xkburcrst/xkburban).
Sources: reference/mm4_5_world_of_xeen/unpacked/sprites/xeen/fcstl2.fwl/frame_0006.png (Burlock: a red shield with
a gold griffin), sprites/dark/fcstl2.fwl/frame_0006.png (Kalindra: a purple banner).
"""
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
BEFORE = HERE / 'work' / 'd3_before'

WORKER = """You are an image-generation worker. Do exactly this and nothing else:
1. Call the built-in image_gen tool ONCE using the attached image as the reference image and the IMAGE PROMPT below.
   Output size: 1024x1536 (portrait).
2. Copy the generated PNG file unchanged to {target}.
3. Reply with only the absolute path of the copied file.
Do not read other files, do not inspect, edit, resize or retry the result.

IMAGE PROMPT:
{prompt}
"""

EDIT = """Asset: a flat surface texture for a Might and Magic VI-VIII style game (a single-picture wall texture seen
straight on, no perspective, even lighting). This is an edit of Reference 1, a finished texture: reproduce it exactly
- same framing, the same stones, the same frame, colours, lighting and painted style - with one change only:
{change}
The picture fills the whole portrait canvas edge to edge; Reference 1's central content stays centred at the same
relative size. No text, no letters, no border added."""

JOBS = {
    'xkncscrst': ('xkburcrst.png', "remove every crown: the golden crown above the tower on the shield is gone (the "
                  "blue field shows there, the white tower with three battlements stays), and the small carved stone "
                  "crown finial above the shield becomes a plain rounded carved stone cap in the same orange-tan stone. "
                  "It is the arms of a new castle, a white tower on blue, not a king's."),
    'xkncsban': ('xkburban.png', "remove the golden crown above the white tower on the banner; the blue cloth shows "
                 "there and the tower moves up a little to sit in the middle of the banner. Everything else (the pole, "
                 "the gold fringe, the swallow-tailed end, the marble wall and knotwork band) is unchanged."),
}


def newcastle():
    (HERE / 'raw').mkdir(exist_ok=True)
    for name, (base, change) in JOBS.items():
        target = HERE / 'raw' / f'{name}_v1.png'
        prompt = EDIT.format(change=change)
        (HERE / 'prompts' / f'{name}_v1.txt').write_text(prompt + '\n')
        command = ['codex', 'exec', '--json', '-s', 'workspace-write', '-C', str(HERE), '--skip-git-repo-check',
                   '-i', str(BEFORE / base)]
        started = time.time()
        with open(HERE / 'raw' / f'{name}_v1.log', 'w') as stream:
            result = subprocess.run(command, input=WORKER.format(prompt=prompt, target=target), text=True,
                                    stdout=stream, stderr=subprocess.STDOUT, timeout=1200)
        print(name, 'ok' if result.returncode == 0 and target.exists() else 'FAILED', round(time.time() - started), 's')


def lin(v):
    v = np.asarray(v, float) / 255
    return np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)


def srgb(v):
    v = np.clip(v, 0, 1)
    return np.where(v <= 0.0031308, v * 12.92, 1.055 * v ** (1 / 2.4) - 0.055) * 255


def save_set(name, rgb):
    image = Image.fromarray(np.clip(np.rint(rgb), 0, 255).astype(np.uint8))
    image.save(HERE / 'finished' / f'{name}.png')
    image.resize((image.width // 2, image.height // 2), Image.LANCZOS).save(HERE / 'finished' / f'{name}_x2.png')
    image.resize((image.width // 4, image.height // 4), Image.LANCZOS).save(HERE / 'finished' / f'{name}_x1.png')


def finish():
    """Scale the edit to the 512 x 1024 master and match the wall round the motif to its base."""
    for name, (base, _) in JOBS.items():
        raw = Image.open(HERE / 'raw' / f'{name}_v1.png').convert('RGB')
        # Codex returns the 1:2 reference stretched to its 2:3 canvas: squeeze the whole frame back.
        rgb = np.asarray(raw.resize((512, 1024), Image.LANCZOS), float)
        ref_image = Image.open(BEFORE / base).convert('RGB')
        ref = np.asarray(ref_image, float)
        # Match the wall round the motif (low saturation, light), not the whole picture: the cloth may change area.
        calm = lambda img, arr: (np.asarray(img.convert('HSV'), float)[..., 1] < 60) & (arr.mean(-1) > 110)
        raw_img = Image.fromarray(rgb.astype(np.uint8))
        m_ref, m_raw = calm(ref_image, ref), calm(raw_img, rgb)
        gains = lin(ref)[m_ref].mean(0) / np.maximum(lin(rgb)[m_raw].mean(0), 1e-6)
        save_set(name, srgb(lin(rgb) * gains))
        print(name, 'gains', np.round(gains, 3))


def kalindra():
    """Crimson field and cloth to Kalindra's purple (the source's dark-side banner): a hue turn of the saturated reds
    only, so the stone frame, the marble, the silver charges and fringe keep their colours."""
    for name in ('xkkalcrst', 'xkkalban'):
        image = Image.open(BEFORE / f'{name}.png').convert('RGB')
        hsv = np.asarray(image.convert('HSV'), float)
        h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
        red = np.minimum(np.abs(h - 0), np.abs(h - 255))           # distance from red on PIL's 0-255 hue circle
        weight = np.clip((14 - red) / 6, 0, 1) * np.clip((s - 70) / 40, 0, 1)
        target_h = 200.0                                             # about 282 degrees: violet purple
        new_h = np.where(weight > 0, target_h, h)
        out = np.stack([new_h, np.minimum(255, s * 0.92), np.minimum(255, v * 1.04)], -1)
        purple = np.asarray(Image.fromarray(out.astype(np.uint8), 'HSV').convert('RGB'), float)
        rgb = np.asarray(image, float)
        mixed = rgb * (1 - weight[..., None]) + purple * weight[..., None]
        save_set(name, mixed)
        print(name, 'recoloured share', round(float((weight > 0.5).mean()), 3))


if __name__ == '__main__':
    {'newcastle': newcastle, 'finish': finish, 'kalindra': kalindra}[sys.argv[1]]()
