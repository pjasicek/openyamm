import runpy,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(p.parents[2]/'tools'))
from build_actor_lods import generate
# Reserve LOD1's triangle budget for the bend rows restored after planar reduction.
generate(p/'export/mm8_m412_prepared.glb',p/'export/mm8_m412_lods.glb','Pirate',ratios=(.46,.18,.06))
runpy.run_path(str(p/'scripts/refine_knee_lods.py'),run_name='__main__')
