"""LOD1 for the texture-quality pass (2026-10-31): tools/build_actor_lods.py on the re-UV'd LOD0 with the ratios and
influence budget of the installed build (mm8_m616_reduce_claude/scripts/build_lods.py: 0.5 / 0.25 / 0.125, 4
influences); patch_glb.py --lod1 takes only its LOD1. Args: <lod0-only glb> <out glb>"""
from pathlib import Path
import sys
P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
argv = sys.argv[sys.argv.index('--') + 1:]
generate(Path(argv[0]), Path(argv[1]), 'BoneDragon', ratios=(.5, .25, .125), max_influences=4)
