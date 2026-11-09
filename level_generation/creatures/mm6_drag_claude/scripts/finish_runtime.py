import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];E=P/'export';sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as rv
sys.argv=['shrink_shadow_lods.py',str(E/'mm6_drag_lods.glb'),str(E/'mm6_drag_shadow.glb')];runpy.run_path(str(P/'scripts/shrink_shadow_lods.py'),run_name='__main__')
rv.apply_variants(E/'mm6_drag_shadow.glb',E/'mm6_drag_unmerged.glb',P/'textures/drag_ramps.json',[(prefix,key,value) for prefix in ['LizardBody','LizardHead'] for key,value in [('openyamm_specular',1.0),('openyamm_specular_mask',True)]])
sys.argv=['merge_head_material.py',str(E/'mm6_drag_unmerged.glb'),str(E/'mm6_drag.glb')];runpy.run_path(str(P.parents[2]/'tools/merge_head_material.py'),run_name='__main__')
