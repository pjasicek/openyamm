#!/usr/bin/env python3
"""The keep props' MM9 skins x4 with Real-ESRGAN, through the isle props project's textures.upscale (wrapped padding,
colour bleed under transparent texels, light unsharp mask) -> textures/<prop>_basecolor.png.
Usage: textures.py [prop ...]"""
import sys

import props_table

sys.path.insert(0, str(props_table.ISLE / 'scripts'))
import textures as isle_textures  # noqa: E402


def main():
    props = sys.argv[1:] or sorted(set(props_table.MODELS.values()))
    (props_table.HERE / 'textures').mkdir(exist_ok=True)
    for prop in props:
        out = props_table.HERE / f'textures/{prop}_basecolor.png'
        if out.exists() and '--force' not in sys.argv:
            continue
        isle_textures.upscale(props_table.HERE / f'work/raw/{prop}/skins/{prop}.png', out)


if __name__ == '__main__':
    main()
