from pathlib import Path
import subprocess,sys
P=Path('level_generation/creatures/mm8_m484_claude').resolve();repo=P.parents[2];E=P/'export'
def run(script,*args):subprocess.run([sys.executable,str(script),*map(str,args)],check=True)
run(P/'scripts/shrink_shadow_lods.py',E/'mm8_m484_lods.glb',E/'mm8_m484_shadowfix.glb')
run(P.parent/'claude_shared/region_variants.py',E/'mm8_m484_shadowfix.glb',E/'mm8_m484.glb',P/'textures/m484_ramps.json','--extra','M484','openyamm_specular=1','--extra','M484','openyamm_specular_mask=true','--extra','M484','pbr.metallicFactor=0','--extra','Axe','openyamm_specular=1','--extra','Axe','openyamm_specular_mask=true','--extra','Axe','pbr.metallicFactor=0')
run(repo/'tools/split_attachment.py',E/'mm8_m484.glb','--joint','Axe','--body',E/'mm8_m484.glb','--attachment',E/'mm8_m484_axe.glb')
run(repo/'tools/merge_head_material.py',E/'mm8_m484.glb',E/'mm8_m484.glb')

# The unchanged axe has no recolour regions; empty ramp extras are invalid in the runtime contract.
sys.path.insert(0,str(repo/'tools'));import normal_map_convention as G
path=E/'mm8_m484_axe.glb';document,binary=G.read_glb(path.read_bytes())
for material in document['materials']:
 extras=material['extras'];assert extras['openyamm_region_ramps']==[]
 del extras['openyamm_region_ramps'];del extras['openyamm_region_mask']
views=[binary[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']] for v in document['bufferViews']]
path.write_bytes(G.write_glb(document,views))
