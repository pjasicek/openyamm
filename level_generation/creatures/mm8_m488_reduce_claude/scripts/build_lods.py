"""work/r70_lod0.glb -> export/mm8_m488_lods.glb (or argv[1]) with LOD1-3 and shadow LODs: the creature's own ratios
(../mm8_m488_claude/scripts/build_lods.py: 0.5 / 0.25 / 0.125, 4 influences), horn and ear tips protected
(work/horn_tips.npy; the coarsest LOD sets the picking height). Usage: blender -b -P build_lods.py [-- <out.glb>]"""
import sys
from pathlib import Path
import numpy as np
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
out = Path(sys.argv[sys.argv.index('--') + 1]) if '--' in sys.argv else P / 'export/mm8_m488_lods.glb'
extra = [tuple(p) for p in np.load(P / 'work/lod_protect.npy')] if (P / 'work/lod_protect.npy').exists() else []
generate(P / 'work/r70_lod0.glb', out, 'Minotaur', ratios=(.5, .25, .125), max_influences=4,
         protected_points=[tuple(p) for p in np.load(P / 'work/horn_tips.npy')] + extra)
