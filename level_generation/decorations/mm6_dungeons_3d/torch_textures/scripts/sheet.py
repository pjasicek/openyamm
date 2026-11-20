#!/usr/bin/env python3
"""The torch batch's review sheet and band means (../../torches/scripts/sheet.py) on torch_textures/review/<prop>/.
Usage: sheet.py <prop> <native texture> [z0:z1 ...]"""
import os

source = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'torches', 'scripts', 'sheet.py')
exec(compile(open(source).read(), source, 'exec'), {'__file__': os.path.abspath(__file__), '__name__': '__main__'})
