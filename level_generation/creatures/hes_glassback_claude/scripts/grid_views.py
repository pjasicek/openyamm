"""Orthographic views of the normalised body with a labelled 10 cm grid (side from +X, front from -Y, top, below).
Args: -- <blend or glb> <out prefix> [x-section]  Model: forward -Y, up +Z, metres."""
import bpy, sys, os, math
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
args = sys.argv[sys.argv.index('--') + 1:]
src, out = args[:2]
if src.endswith('.blend'):
    bpy.ops.wm.open_mainfile(filepath=C.path(src))
W, H = 1500, 900
S = 3.4
views = {'side': ((5, 0, 0.6), (0, 0, 0.6)), 'front': ((0, -5, 0.6), (0, 0, 0.6)), 'top': ((0, 0, 5), (0, 0, 0)),
         'below': ((0, 0, -5), (0, 0, 0))}
for name, (loc, tgt) in views.items():
    C.render_ortho(loc, tgt, S, f'{out}_{name}.png', show=[C.MESH], res=(W, H), xray=True)
