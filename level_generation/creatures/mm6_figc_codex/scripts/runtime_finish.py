from pathlib import Path
import subprocess
P=Path(__file__).resolve().parents[1];E=P/'export';S=P/'scripts';R=P.parents[2]
def run(*a):subprocess.run(['python3',*map(str,a)],check=True)
run(S/'shrink_shadow_lods.py',E/'mm6_figc_lods.glb',E/'mm6_figc_shadow.glb')
run(P.parent/'claude_shared/region_variants.py',E/'mm6_figc_shadow.glb',E/'mm6_figc.glb',P/'textures/figc_round3_ramps.json','--extra','FighterChain','openyamm_specular=1','--extra','FighterChain','openyamm_specular_mask=true','--extra','FighterChain','pbr.metallicFactor=0','--extra','FighterChainGear','openyamm_specular=1','--extra','FighterChainGear','openyamm_specular_mask=true','--extra','FighterChainGear','pbr.metallicFactor=0')
for prop in ['Axe','Shield']:run(R/'tools/split_attachment.py',E/'mm6_figc.glb','--joint',prop,'--body',E/'mm6_figc.glb','--attachment',E/f'mm6_figc_{prop.lower()}.glb')
run(S/'merge_lod_heads.py')
run(S/'viewer_tiers.py')

import json,hashlib,shutil
V=P/'review/viewer';mp=V/'manifest.json';d=json.loads(mp.read_text())
for m in d['models']:
 f=V/('mm6_'+m['id']+'.glb');m['sha256']=hashlib.sha256(f.read_bytes()).hexdigest();m['url']=f.name+'?v='+m['sha256'][:12]
d['model_sha256']=d['models'][0]['sha256'];mp.write_text(json.dumps(d,indent=2));shutil.copy2(V/'mm6_figc_a.glb',E/'mm6_figc_portable.glb')
