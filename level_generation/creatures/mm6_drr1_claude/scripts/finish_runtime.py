import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];E=P/'export';sys.path.insert(0,str(P.parent/'claude_shared'))
import region_variants as rv,burn_maps
sys.argv=['shrink_shadow_lods.py',str(E/'mm6_wyrm_lods.glb'),str(E/'mm6_wyrm_shadow.glb')];runpy.run_path(str(P/'scripts/shrink_shadow_lods.py'),run_name='__main__')
burn_maps.add_burn_maps(E/'mm6_wyrm_shadow.glb',E/'mm6_wyrm_shadow.glb',{'Wyrm':P/'textures/wyrm_body_burn.png','WyrmHead':P/'textures/wyrm_head_burn.png'})
rv.apply_variants(E/'mm6_wyrm_shadow.glb',E/'mm6_wyrm.glb',P/'textures/wyrm_ramps.json',[(prefix,key,value) for prefix in ['Wyrm','WyrmHead'] for key,value in [('openyamm_specular',1.0),('openyamm_specular_mask',True)]])
