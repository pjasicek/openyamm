import sys
from pathlib import Path
P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate
a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['work/source_runtime_lod0.glb', 'work/source_lods.glb']
generate(P / a[0], P / a[1], 'Robot', ratios=(.5, .25, .125),
         max_influences=4)
