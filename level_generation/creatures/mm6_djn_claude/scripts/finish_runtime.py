import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];E=P/'export'
sys.path.insert(0,str(Path('level_generation/creatures/claude_shared').resolve()))
import region_variants as rv
sys.argv=['shrink_shadow_lods.py',str(E/'mm6_djn_lods.glb'),str(E/'mm6_djn_shadow.glb')]
runpy.run_path(str(P/'scripts/shrink_shadow_lods.py'),run_name='__main__')
rv.apply_variants(E/'mm6_djn_shadow.glb',E/'mm6_djn.glb',P/'textures/djn_ramps.json',[('Genie','openyamm_specular',1.0),('Genie','openyamm_specular_mask',True)])
sys.argv=['merge_head_material.py',str(E/'mm6_djn.glb'),str(E/'mm6_djn.glb')]
runpy.run_path('tools/merge_head_material.py',run_name='__main__')
