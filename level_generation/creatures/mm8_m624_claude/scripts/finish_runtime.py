import sys,runpy,json,shutil
from pathlib import Path
P=Path(__file__).resolve().parents[1];E=P/'export'
sys.path.insert(0,str(Path('level_generation/creatures/claude_shared').resolve()));import region_variants as rv
sys.argv=['shrink_shadow_lods.py',str(E/'mm8_m624_lods.glb'),str(E/'mm8_m624_shadow.glb')];runpy.run_path(str(P/'scripts/shrink_shadow_lods.py'),run_name='__main__')
rv.apply_variants(E/'mm8_m624_shadow.glb',E/'mm8_m624.glb',P/'textures/naga_ramps.json',[('Naga','openyamm_specular',1.),('Naga','openyamm_specular_mask',True)])
for sd in ['L1','L2','L3','R1','R2','R3']:
 sys.argv=['split_attachment.py',str(E/'mm8_m624.glb'),'--joint',sd+'_Sword','--body',str(E/'mm8_m624.glb'),'--attachment',str(E/f'mm8_m624_{sd.lower()}.glb')];runpy.run_path('tools/split_attachment.py',run_name='__main__')
sys.argv=['merge_head_material.py',str(E/'mm8_m624.glb'),str(E/'mm8_m624.glb')];runpy.run_path('tools/merge_head_material.py',run_name='__main__')
