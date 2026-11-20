from pathlib import Path
import sys
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p.parents[2]/'tools'))
from build_actor_lods import generate
generate(p/'export/mm8_m456_prepared.glb',p/'export/mm8_m456_lods.glb','DragonHunter',ratios=(.46,.21,.075),max_influences=4)
