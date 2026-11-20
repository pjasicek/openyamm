import subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];E=P/'export';S=P/'scripts'
def run(*a):subprocess.run([str(x) for x in a],check=True)
run('python3',S/'preserve_lod_contacts.py')
run('python3',S/'shrink_shadow_lods.py',E/'mm8_m440_lods_contacts.glb',E/'mm8_m440_lods_shadowfix.glb')
run('python3',P.parent/'claude_shared/region_variants.py',E/'mm8_m440_lods_shadowfix.glb',E/'mm8_m440.glb',P/'textures/m440_ramps.json','--extra','M440','openyamm_specular=1','--extra','M440','openyamm_specular_mask=true','--extra','M440','pbr.metallicFactor=0','--extra','Club','openyamm_specular=1','--extra','Club','openyamm_specular_mask=true')
run('python3','tools/split_attachment.py',E/'mm8_m440.glb','--joint','Club','--body',E/'mm8_m440.glb','--attachment',E/'mm8_m440_club.glb')
run('python3','tools/merge_head_material.py',E/'mm8_m440.glb',E/'mm8_m440.glb')
