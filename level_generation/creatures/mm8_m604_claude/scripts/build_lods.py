from pathlib import Path
import sys
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p.parents[2]/'tools'))
import build_actor_lods
build_actor_lods.generate(p/'export/mm8_m604_runtime_lod0.glb',p/'export/mm8_m604_lods.glb','EtherKnight',ratios=(.5,.25,.125),max_influences=4)
