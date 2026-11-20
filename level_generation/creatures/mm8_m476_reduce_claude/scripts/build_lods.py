"""work/r75_lod0.glb -> export/mm8_m476.glb with colour and shadow LOD1-3: the ratios and influence budget of
mm8_m476_claude's own build (tools/build_actor_lods.py defaults 0.5 / 0.18 / 0.06, 8 influences)."""
from pathlib import Path
import sys
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
generate(P / 'work/r75_lod0.glb', P / 'export/mm8_m476.glb', 'Troll', ratios=(.5, .18, .06), max_influences=8)
