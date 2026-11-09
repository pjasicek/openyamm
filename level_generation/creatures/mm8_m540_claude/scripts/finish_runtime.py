from pathlib import Path
import subprocess
p=Path(__file__).resolve().parents[1];e=p/'export'
def run(*args):subprocess.run([str(x) for x in args],check=True)
run('python3',p.parent/'claude_shared/region_variants.py',e/'mm8_m540_lods.glb',e/'mm8_m540.glb',p/'textures/m540_ramps.json','--extra','OgreMage','openyamm_specular=1','--extra','OgreMage','openyamm_specular_mask=true','--extra','OgreMage','pbr.metallicFactor=0')
run('python3','tools/split_attachment.py',e/'mm8_m540.glb','--joint','Wand','--body',e/'mm8_m540.glb','--attachment',e/'mm8_m540_wand.glb')
run('python3','tools/merge_head_material.py',e/'mm8_m540.glb',e/'mm8_m540.glb')
