#!/usr/bin/env python3
"""The pentagram's five coloured flames (MM9 Fire objects PentaFire1-5, FireColor1 per fire; their order is the
puzzle's answer, letter 485): the shared CC0 flame flipbook (textures/flame02_basecolor.png, as the Anskram torch's)
recoloured by luminance into each FireColor1 with a hot pale core -> textures/flame_<colour>_basecolor.png."""
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parents[1]
COLOURS = {'red': (255, 0, 0), 'yellow': (255, 255, 0), 'blue': (43, 88, 244), 'green': (31, 224, 65),
           'orange': (255, 137, 81)}


def main():
    source = np.asarray(Image.open(HERE / 'textures/flame02_basecolor.png').convert('RGBA'), np.float32) / 255.0
    rgb, alpha = source[..., :3], source[..., 3:]
    luminance = (rgb @ np.array([0.299, 0.587, 0.114], np.float32))[..., None]
    for name, colour in COLOURS.items():
        target = np.array(colour, np.float32) / 255.0
        body = np.clip(target * np.minimum(1.0, luminance * 1.5), 0, 1)
        core = np.clip((luminance - 0.75) / 0.25, 0, 1) * 0.55
        out = body * (1 - core) + core
        image = np.concatenate([out, alpha], -1)
        Image.fromarray((image * 255 + 0.5).astype(np.uint8), 'RGBA').save(HERE / f'textures/flame_{name}_basecolor.png')
        print('WROTE', f'flame_{name}_basecolor.png')


if __name__ == '__main__':
    main()
