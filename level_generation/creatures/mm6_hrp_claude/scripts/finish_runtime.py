"""Keep body, head and wing materials separate, as requested by the user."""
import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];E=P/'export';sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as rv
sys.argv=['shrink_shadow_lods.py',str(E/'mm6_hrp_lods.glb'),str(E/'mm6_hrp_shadow.glb')];runpy.run_path(str(P/'scripts/shrink_shadow_lods.py'),run_name='__main__')
rv.apply_variants(E/'mm6_hrp_shadow.glb',E/'mm6_hrp.glb',P/'textures/hrp_ramps.json',[('Harpy','openyamm_specular',1.0),('Harpy','openyamm_specular_mask',True)])
