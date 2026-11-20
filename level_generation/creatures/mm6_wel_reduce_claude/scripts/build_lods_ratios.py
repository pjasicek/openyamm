"""tools/build_actor_lods.py with custom LOD ratios (LOD_RATIOS, default 0.5,0.25,0.13). The default 6 % LOD3 of the
reduced water elemental (349 tris) lost the crown prongs: 8 cm lower, and the native-height regression measures the
far LOD. Usage: blender -b -P build_lods_ratios.py -- <src.glb> <dst.glb> <mesh node>"""
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
import build_actor_lods as L  # noqa: E402
src, dst, node = sys.argv[sys.argv.index('--') + 1:][:3]
ratios = tuple(float(x) for x in os.environ.get('LOD_RATIOS', '0.5,0.25,0.13').split(','))
L.generate(Path(src).resolve(), Path(dst).resolve(), node, ratios=ratios)
