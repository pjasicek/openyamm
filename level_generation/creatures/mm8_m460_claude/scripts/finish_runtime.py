from pathlib import Path
import subprocess
p=Path(__file__).resolve().parents[1];e=p/'export'
def run(*args):subprocess.run([str(x) for x in args],check=True)
run('python3',p.parent/'claude_shared/region_variants.py',e/'mm8_m460_lods.glb',e/'mm8_m460.glb',p/'textures/m460_ramps.json','--extra','Cleric','openyamm_specular=1','--extra','Cleric','openyamm_specular_mask=true','--extra','Cleric','pbr.metallicFactor=0')
run('python3','tools/split_attachment.py',e/'mm8_m460.glb','--joint','Staff','--body',e/'mm8_m460.glb','--attachment',e/'mm8_m460_staff.glb')
run('python3','tools/merge_head_material.py',e/'mm8_m460.glb',e/'mm8_m460.glb')
