"""work/r75_lod0.glb -> work/r75_lods.glb with LOD1-3 and shadow LODs, the creature's own ratios and influence budget
(mm8_m400/3d_20261006/claude_20261015/scripts/build_runtime.py: 0.5 / 0.25 / 0.125, 8 influences), except LOD2 at
0.33: Blender's collapse stalls at about 2,360 triangles on this fragmented atlas (the installed LOD3 stalled at 2,417),
so 0.25 and 0.125 both land on that floor and the counts would not decrease. The head fin tips (candidate vertices
above 1.64 m, rest pose, Blender Z-up) are protected contacts: unprotected, LOD3 lost 5.5 cm of height (1.644 m), and
picking bounds use the coarsest level.
Usage: blender -b -P build_lods.py [-- <in.glb> <out.glb>]"""
from pathlib import Path
import sys
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
import numpy as np  # noqa: E402
a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['work/r75_lod0.glb', 'work/r75_lods.glb']
v = np.load(P / 'work/mesh_r75.npz')['verts']; tips = [tuple(map(float, p)) for p in v[v[:, 2] > 1.64]]
print('PROTECTED fin tips', len(tips))
generate(P / a[0], P / a[1], 'Lizardman_Body', ratios=(.5, .33, .125), max_influences=8, protected_points=tips)
