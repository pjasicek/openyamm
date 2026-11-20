from pathlib import Path
import subprocess
P=Path(__file__).resolve().parents[1];E=P/'export';repo=P.parents[2]
def run(*a):subprocess.run(['python3',*map(str,a)],check=True)
run(P/'scripts/preserve_peg_lods.py')
run(P/'scripts/shrink_shadow_lods.py',E/'mm8_m420_lods_preserved.glb',E/'mm8_m420_lods.glb')
run(P.parent/'claude_shared/region_variants.py',E/'mm8_m420_lods.glb',E/'mm8_m420.glb',P/'textures/pirate_mage_ramps.json','--extra','PirateMage','openyamm_specular=1','--extra','PirateMage','openyamm_specular_mask=true','--extra','PirateMage','pbr.metallicFactor=0')
for bone,name in [('Staff','staff')]:run(repo/'tools/split_attachment.py',E/'mm8_m420.glb','--joint',bone,'--body',E/'mm8_m420.glb','--attachment',E/f'mm8_m420_{name}.glb')
run(repo/'tools/merge_head_material.py',E/'mm8_m420.glb',E/'mm8_m420.glb')

