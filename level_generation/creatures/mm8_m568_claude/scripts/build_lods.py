import sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'))
from build_actor_lods import generate
p=Path(__file__).resolve().parents[1]
generate(p/'export/mm8_m568_runtime_lod0.glb',p/'export/mm8_m568_lods.glb','Body',ratios=(.5,.25,.125),max_influences=4)
