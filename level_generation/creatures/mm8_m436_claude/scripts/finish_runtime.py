import subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];E=P/'export';S=P/'scripts'
def run(*a):subprocess.run([str(x) for x in a],check=True)
run('python3',S/'shrink_shadow_lods.py',E/'mm8_m436_lods.glb',E/'mm8_m436_lods_shadowfix.glb')
run('python3',P.parent/'claude_shared/region_variants.py',E/'mm8_m436_lods_shadowfix.glb',E/'mm8_m436.glb',P/'textures/m436_ramps.json','--extra','M436','openyamm_specular=1','--extra','M436','openyamm_specular_mask=true')
run('python3','tools/merge_head_material.py',E/'mm8_m436.glb',E/'mm8_m436.glb')
