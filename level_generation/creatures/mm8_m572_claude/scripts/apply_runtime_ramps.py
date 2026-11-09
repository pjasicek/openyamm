from pathlib import Path
import sys
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'claude_shared'))
from region_variants import apply_variants
apply_variants(P/'export/mm8_m572_lods.glb',P/'export/mm8_m572.glb',P/'textures/phoenix_ramps.json',[(f'Phoenix_{tier}',key,value) for tier in 'ABC' for key,value in [('openyamm_specular',1.),('openyamm_specular_mask',True)]])
