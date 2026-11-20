from pathlib import Path
import sys
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
from build_actor_lods import generate
generate(P/'export/mm8_m572_prepared.glb',P/'export/mm8_m572_lods.glb','Body',ratios=(.5,.25,.125),max_influences=4)
