import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];E=P/'export';sys.path.insert(0,str(Path('level_generation/creatures/claude_shared').resolve()))
import region_variants as rv
sys.argv=['shrink_shadow_lods.py',str(E/'mm8_m536_lods.glb'),str(E/'mm8_m536_shadow.glb')]
runpy.run_path(str(P.parent/'mm6_djn_claude/scripts/shrink_shadow_lods.py'),run_name='__main__')
rv.apply_variants(E/'mm8_m536_shadow.glb',E/'mm8_m536.glb',P/'textures/m536_ramps.json',[(prefix,key,value) for prefix in ['Efreeti_','EfreetiHead_'] for key,value in [('openyamm_specular',1.0),('openyamm_specular_mask',True)]])
sys.argv=['merge_head_material.py',str(E/'mm8_m536.glb'),str(E/'mm8_m536.glb')]
runpy.run_path('tools/merge_head_material.py',run_name='__main__')
sys.argv=['model_hide_collapsed_meshes.py',str(E/'mm8_m536.glb'),'--write',str(E/'mm8_m536.glb')]
runpy.run_path('tools/model_hide_collapsed_meshes.py',run_name='__main__')
