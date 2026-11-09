import sys
from pathlib import Path
P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate
generate(P / 'export/mm7_m386_runtime_lod0.glb', P / 'export/mm7_m386_lods.glb', 'Robot', ratios=(.5, .25, .125),
         max_influences=4)
