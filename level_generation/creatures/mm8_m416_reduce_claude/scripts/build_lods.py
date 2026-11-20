"""work/c75_lod0.glb -> work/c75_lods.glb (or the paths after --) with LOD1-3 and shadow LODs, the same builder and
ratios as the creature (../mm8_m416_claude/scripts/build_lods.py: 0.5 / 0.25 / 0.125, 4 influences), with the sole
vertices (rest height below 6 cm) protected in every LOD: the shared gate's foot-yaw rows use the sole patches, and
the unprotected LOD2 shadow turned its left foot 40 degrees in Walking.
Usage: blender -b -P build_lods.py [-- <in.glb> <out.glb>]"""
from pathlib import Path
import sys
import numpy as np
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
src, out = (Path(a[0]), Path(a[1])) if len(a) > 1 else (P / 'work/c75_lod0.glb', P / 'work/c75_lods.glb')
v = np.load(P / 'work/mesh_in.npz')['verts']; soles = [tuple(p) for p in v[v[:, 2] < .06]]
print('PROTECTED sole points', len(soles))
generate(src, out, 'PirateCrossbowwoman', ratios=(float(__import__('os').environ.get('REA_LOD1', '.5')), .25, .125), max_influences=4, protected_points=soles)
