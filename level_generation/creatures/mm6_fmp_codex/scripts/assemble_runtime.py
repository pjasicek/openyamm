"""Use the shared actor post-processors, retaining separate authoring maps and one runtime draw per tier."""
import json,struct,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];E=P/'export'
def run(*args):subprocess.run([sys.executable,*map(str,args)],check=True)
run(P/'scripts/shrink_shadow_lods.py',E/'mm6_fmp_lods.glb',E/'mm6_fmp_lods_shadow.glb')
run(P.parent/'claude_shared/region_variants.py',E/'mm6_fmp_lods_shadow.glb',E/'mm6_fmp_regions.glb',P/'textures/fmp_ramps.json','--extra','PeasantF2','openyamm_specular=1','--extra','PeasantF2','openyamm_specular_mask=true','--extra','PeasantF2','pbr.metallicFactor=0')
run('tools/merge_head_material.py',E/'mm6_fmp_regions.glb',E/'mm6_fmp.glb')
for path in [E/'mm6_fmp_runtime_lod0.glb',E/'mm6_fmp.glb']:
 raw=path.read_bytes();n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);binary=raw[28+n:]
 for m in doc['materials']:
  ext=m.get('extensions',{});ext.pop('KHR_materials_specular',None)
  if not ext:m.pop('extensions',None)
 for k in ['extensionsUsed','extensionsRequired']:
  if k in doc:doc[k]=[s for s in doc[k] if s!='KHR_materials_specular']
 enc=json.dumps(doc,separators=(',',':')).encode();enc+=b' '*(-len(enc)%4)
 path.write_bytes(struct.pack('<III',0x46546c67,2,28+len(enc)+len(binary))+struct.pack('<II',len(enc),0x4e4f534a)+enc+struct.pack('<II',len(binary),0x004e4942)+binary)
(P/'review/viewer').mkdir(parents=True,exist_ok=True)
run(P/'scripts/viewer_tiers.py');run(P/'scripts/setup_viewer.py')
