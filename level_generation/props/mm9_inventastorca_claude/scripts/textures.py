#!/usr/bin/env python3
"""Inventa Storca props' MM9 skins x4 with Real-ESRGAN, through the isle props project's textures.upscale (wrapped padding,
colour bleed under transparent texels, light unsharp mask): work/raw/<prop>/skins/<id>.png ->
textures/<id>_basecolor.png (id <prop>, or <prop>_<k> for a model's second skin).
Usage: textures.py [prop ...] [--force]"""
import sys

import props_table

sys.path.insert(0, str(props_table.ISLE / 'scripts'))
import textures as isle_textures  # noqa: E402


def main():
    props = [a for a in sys.argv[1:] if not a.startswith('--')] or props_table.built_props()
    (props_table.HERE / 'textures').mkdir(exist_ok=True)
    for prop in props:
        for skin in sorted((props_table.HERE / f'work/raw/{prop}/skins').glob('*.png')):
            out = props_table.HERE / f'textures/{skin.stem}_basecolor.png'
            if out.exists() and '--force' not in sys.argv:
                continue
            isle_textures.upscale(skin, out)
            print('UPSCALED', skin.stem)


if __name__ == '__main__':
    main()
