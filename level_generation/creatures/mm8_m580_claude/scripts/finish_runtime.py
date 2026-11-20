from pathlib import Path
import sys,runpy,shutil
P=Path(__file__).resolve().parents[1];E=P/'export';sys.path.insert(0,str(P.parent/'claude_shared'))
import region_variants as rv
sys.argv=['shrink_shadow_lods.py',str(E/'mm8_m580_lods.glb'),str(E/'mm8_m580_shadow.glb')];runpy.run_path(str(P/'scripts/shrink_shadow_lods.py'),run_name='__main__')
rv.apply_variants(E/'mm8_m580_shadow.glb',E/'mm8_m580.glb',P/'textures/m580_ramps.json',[('Turtle','openyamm_specular',0.),('Turtle','pbr.metallicFactor',0.)])
# Base A uses its painted colours directly; runtime rejects an empty ramp array.
sys.path.insert(0,str(Path('tools').resolve()))
from build_actor_lods import read_glb,write_glb
d,b=read_glb(E/'mm8_m580.glb')
for m in d['materials']:
 e=m.get('extras',{})
 if e.get('openyamm_region_ramps')==[]:
  e.pop('openyamm_region_ramps');e.pop('openyamm_region_mask')
write_glb(E/'mm8_m580.glb',d,b)
shutil.copy2(E/'mm8_m580_runtime_lod0.glb',E/'mm8_m580_portable.glb')
