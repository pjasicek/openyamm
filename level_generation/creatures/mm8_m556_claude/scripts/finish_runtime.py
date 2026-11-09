import sys,runpy,shutil
from pathlib import Path
P=Path(__file__).resolve().parents[1];E=P/'export';sys.path.insert(0,str(P.parent/'claude_shared'))
import region_variants as rv
sys.argv=['shrink_shadow_lods.py',str(E/'mm8_m556_lods.glb'),str(E/'mm8_m556_shadow.glb')];runpy.run_path(str(P/'scripts/shrink_shadow_lods.py'),run_name='__main__')
rv.apply_variants(E/'mm8_m556_shadow.glb',E/'mm8_m556.glb',P/'textures/m556_ramps.json',[('Wasp','openyamm_specular',1.),('Wasp','openyamm_specular_mask',True)])
for bone in ['Sword','Shield']:
 sys.argv=['split_attachment.py',str(E/'mm8_m556.glb'),'--joint',bone,'--body',str(E/'mm8_m556.glb'),'--attachment',str(E/f'mm8_m556_{bone.lower()}.glb')];runpy.run_path('tools/split_attachment.py',run_name='__main__')
sys.argv=['merge_head_material.py',str(E/'mm8_m556.glb'),str(E/'mm8_m556.glb')];runpy.run_path('tools/merge_head_material.py',run_name='__main__')
shutil.copy2(E/'mm8_m556_runtime_lod0.glb',E/'mm8_m556_portable.glb')
