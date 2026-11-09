"""tools/build_actor_lods.py with fitted ratios (its CLI has the defaults .5/.18/.06 only): the shell's plate
outline and the wings need denser far levels (the guidelines: fit the LODs, not fixed ratios).
Usage (Blender): lods.py <in.glb> <out.glb> <mesh node> [ratios=0.55,0.3,0.15]"""
import sys
from pathlib import Path
args = sys.argv[sys.argv.index('--') + 1:]
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
import build_actor_lods
ratios = tuple(float(x) for x in (args[3] if len(args) > 3 else '0.55,0.3,0.15').split(','))
build_actor_lods.generate(Path(args[0]).resolve(), Path(args[1]).resolve(), args[2], ratios=ratios)
