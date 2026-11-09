"""Run after export_runtime.py; run build_lods.py between prepare and final."""
import subprocess,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1];root=p.parents[2]
def run(script,*a):subprocess.run([sys.executable,'-B',str(script),*map(str,a)],check=True)
if sys.argv[1]=='prepare':
 run(p/'scripts/pack_orm.py');run(root/'tools/prepare_actor_glb.py',p/'export/mm6_mnk1_lod0.glb',p/'export/mm6_mnk1_runtime_lod0.glb')
else:
 run(p/'scripts/shrink_shadow_lods.py',p/'export/mm6_mnk1_lods.glb',p/'export/mm6_mnk1_lods_shadowfix.glb')
 run(p.parent/'claude_shared/region_variants.py',p/'export/mm6_mnk1_lods_shadowfix.glb',p/'export/mm6_mnk1.glb',p/'textures/mnk1_ramps.json','--extra','Monk','openyamm_specular=0','--extra','Monk','pbr.metallicFactor=0')
 run(p/'scripts/viewer_tiers.py')
