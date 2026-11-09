import sys,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P.parents[2]
sys.path.insert(0,str(R/'tools'))
from build_actor_lods import generate
generate(P/'export/mm8_m436_runtime_lod0.glb',P/'export/mm8_m436_lods.glb',node_name='M436',ratios=(.5,.24,.10),max_influences=4,protected_points=json.loads((P/'work/lod_protected_points.json').read_text()))
