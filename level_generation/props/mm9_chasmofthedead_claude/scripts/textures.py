#!/usr/bin/env python3
"""The Chasm of the Dead props' MM9 skins x4 with Real-ESRGAN, through the Anskram Keep's textures step (the isle's
textures.upscale: wrapped padding, colour bleed under transparent texels, light unsharp mask) ->
textures/<prop>_basecolor.png. Usage: textures.py [prop ...] [--force]"""
import sys

import anskram
import props_table

module = anskram.load('textures')


def main():
    props = [a for a in sys.argv[1:] if not a.startswith('--')] or props_table.built_props()
    sys.argv = [sys.argv[0]] + props + [a for a in sys.argv[1:] if a.startswith('--')]
    module.main()


if __name__ == '__main__':
    main()
