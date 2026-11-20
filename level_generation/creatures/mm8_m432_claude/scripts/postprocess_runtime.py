from pathlib import Path
import subprocess,sys
P=Path('level_generation/creatures/mm8_m432_claude').resolve();repo=P.parents[2];E=P/'export'
def run(script,*args):subprocess.run([sys.executable,str(script),*map(str,args)],check=True)
run(P/'scripts/shrink_shadow_lods.py',E/'mm8_m432_lods.glb',E/'mm8_m432_shadowfix.glb')
run(P.parent/'claude_shared/region_variants.py',E/'mm8_m432_shadowfix.glb',E/'mm8_m432.glb',P/'textures/m432_ramps.json','--extra','M432','openyamm_specular=1','--extra','M432','openyamm_specular_mask=true','--extra','M432','pbr.metallicFactor=0','--extra','Sword','openyamm_specular=1','--extra','Sword','openyamm_specular_mask=true','--extra','Sword','pbr.metallicFactor=0')
run(repo/'tools/split_attachment.py',E/'mm8_m432.glb','--joint','Socket_Sword','--body',E/'mm8_m432.glb','--attachment',E/'mm8_m432_sword.glb')
run(repo/'tools/merge_head_material.py',E/'mm8_m432.glb',E/'mm8_m432.glb')

# The unchanged sword has no recolour regions; empty ramp extras are invalid in the runtime contract.
sys.path.insert(0,str(repo/'tools'));import normal_map_convention as G
path=E/'mm8_m432_sword.glb';document,binary=G.read_glb(path.read_bytes())
for material in document['materials']:
 extras=material['extras'];assert extras['openyamm_region_ramps']==[]
 del extras['openyamm_region_ramps'];del extras['openyamm_region_mask']
views=[binary[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']] for v in document['bufferViews']]
path.write_bytes(G.write_glb(document,views))
