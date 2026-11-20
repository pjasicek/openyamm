from pathlib import Path
import subprocess
P=Path(__file__).resolve().parents[1];E=P/'export';repo=P.parents[2]
def run(*a):subprocess.run(['python3',*map(str,a)],check=True)
run(P/'scripts/shrink_shadow_lods.py',E/'mm8_m656_lods_raw.glb',E/'mm8_m656_lods.glb')
run(P.parent/'claude_shared/region_variants.py',E/'mm8_m656_lods.glb',E/'mm8_m656.glb',P/'textures/mercenary_ramps.json','--extra','Mercenary','openyamm_specular=1','--extra','Mercenary','openyamm_specular_mask=true','--extra','Mercenary','pbr.metallicFactor=0')
for bone,name in [('Sword','sword'),('Scabbard','scabbard')]:run(repo/'tools/split_attachment.py',E/'mm8_m656.glb','--joint',bone,'--body',E/'mm8_m656.glb','--attachment',E/f'mm8_m656_{name}.glb')
run(repo/'tools/merge_head_material.py',E/'mm8_m656.glb',E/'mm8_m656.glb')

# Further collapse makes the thin sword blade vanish edge-on; keep its verified 68-triangle distant silhouette.
import sys
sys.path.insert(0,str(P.parent/'claude_shared'))
import region_variants as R
path=E/'mm8_m656_sword.glb';doc,binary=R.read_glb(path)
doc['meshes']=doc['meshes'][:2];doc['meshes'][0]['extras']['openyamm_lods']=[1]
R.write_glb(path,doc,binary)
