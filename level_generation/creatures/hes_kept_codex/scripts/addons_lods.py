import sys,os
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'));import build_actor_lods as B
B.generate(P/'export/hes_kept_m_enforcer_lods.glb',P/'export/hes_kept_m_enforcer_lods_plate.glb','KeptPlate',ratios=(.5,.25,.125),max_influences=8)
sys.stdout.flush();sys.stderr.flush();os._exit(0)
