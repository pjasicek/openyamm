import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];E=P/'export';sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as rv
runpy.run_path(str(P/'scripts/preserve_wing_lods.py'),run_name='__main__')
sys.argv=['shrink_shadow_lods.py',str(E/'mm6_cdr1_lods.glb'),str(E/'mm6_cdr1_shadow.glb')];runpy.run_path(str(P/'scripts/shrink_shadow_lods.py'),run_name='__main__')
import burn_maps
burn_maps.add_burn_maps(P/'export/mm6_cdr1_shadow.glb',P/'export/mm6_cdr1_shadow.glb',{f'Dragon{label.title()}_A':P/f'textures/cdr1_{label}_burn.png' for label in ['body','head','wings']})
rv.apply_variants(E/'mm6_cdr1_shadow.glb',E/'mm6_cdr1.glb',P/'textures/cdr1_ramps.json',[(prefix,key,value) for prefix in ['DragonBody','DragonHead','DragonWings'] for key,value in [('openyamm_specular',1.0),('openyamm_specular_mask',True)]])
