import json,copy,sys,subprocess
from pathlib import Path
p=Path(__file__).resolve().parents[1];root=p.parents[2];sys.path.insert(0,str(root/'tools'))
from build_actor_lods import read_glb,write_glb
out=p/'export';ramps=json.loads((p/'textures/mep_ramps.json').read_text())
def run(*args):subprocess.run([sys.executable,*map(str,args)],check=True)
for level in range(4):
 raw=out/f'mm6_mep_raw_lod{level}.glb';doc,data=read_glb(raw);buf=bytearray(data)
 for mat in doc['materials']:
  name=mat['name'];base=name.replace(f'_L{level}','') if level else name
  prefix={'Mep_A':'mep','MepHead_A':'mep_head','MepStaff_A':'mep_staff'}[base]
  tid=mat['pbrMetallicRoughness']['metallicRoughnessTexture']['index'];im=doc['images'][doc['textures'][tid]['source']]
  png=(p/f'textures/lod{level}/{prefix}_orm.png').read_bytes();buf.extend(b'\0'*(-len(buf)%4));im.update(bufferView=len(doc['bufferViews']),mimeType='image/png')
  doc['bufferViews'].append({'buffer':0,'byteOffset':len(buf),'byteLength':len(png)});buf.extend(png)
 node=next(n for n in doc['nodes'] if n.get('name')=='Mep');doc['meshes'][node['mesh']].setdefault('extras',{})['openyamm_lods']=[]
 write_glb(raw,doc,buf)
 runtime=out/f'mm6_mep_runtime_lod{level}.glb';run(root/'tools/prepare_actor_glb.py',raw,runtime)
 cfg=copy.deepcopy(ramps)
 for entry in cfg['materials']:
  if level:entry['base']=entry['base'].replace('_A',f'_L{level}_A');entry['prefix']+=f'_L{level}'
  entry['mask']=entry['mask'].replace('_region_mask.png','_region_mask.png')
 config=p/f'textures/lod{level}/ramps.json';config.write_text(json.dumps(cfg,indent=2))
 tier=out/f'mm6_mep_tiered_lod{level}.glb'
 run(p.parent/'claude_shared/region_variants.py',runtime,tier,config,'--extra','Mep','openyamm_specular=0','--extra','Mep','pbr.metallicFactor=0')
 body=out/f'mm6_mep_body_lod{level}.glb';staff=out/f'mm6_mep_staff_lod{level}.glb'
 run(root/'tools/split_attachment.py',tier,'--joint','Staff','--body',body,'--attachment',staff)
 run(root/'tools/merge_head_material.py',body,body)
run(p/'scripts/pack_lods.py')
run(p/'scripts/shrink_shadow_lods.py',out/'mm6_mep_body_packed.glb',out/'mm6_mep.glb')
for path in out.glob('*.glb'):path.chmod(0o644)
print('FINAL_RUNTIME',out/'mm6_mep.glb',out/'mm6_mep_staff.glb')
