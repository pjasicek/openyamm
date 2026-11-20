import json,copy,sys,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2];sys.path.insert(0,str(ROOT/'tools'));from build_actor_lods import read_glb,write_glb
out=P/'export';info=json.loads((out/'export_info.json').read_text());ramps=json.loads((P/'textures/natf_ramps.json').read_text())
def run(*args):subprocess.run([sys.executable,*map(str,args)],check=True)
for level in range(4):
 raw=out/f'mm6_natf_raw_lod{level}.glb';doc,data=read_glb(raw);buf=bytearray(data);maps={r['name']:r for r in info['lods'][level]['maps']}
 for mat in doc['materials']:
  base=mat['name'].replace(f'_L{level}','')if level else mat['name'];row=maps[base];tid=mat['pbrMetallicRoughness']['metallicRoughnessTexture']['index'];im=doc['images'][doc['textures'][tid]['source']];png=(P/row['maps']['metal_rough']).read_bytes();buf.extend(b'\0'*(-len(buf)%4));im.update(bufferView=len(doc['bufferViews']),mimeType='image/png');doc['bufferViews'].append({'buffer':0,'byteOffset':len(buf),'byteLength':len(png)});buf.extend(png)
 node=next(n for n in doc['nodes']if n.get('name')=='Natf');doc['meshes'][node['mesh']].setdefault('extras',{})['openyamm_lods']=[];write_glb(raw,doc,buf);runtime=out/f'mm6_natf_runtime_lod{level}.glb';run(ROOT/'tools/prepare_actor_glb.py',raw,runtime)
 cfg=copy.deepcopy(ramps)
 for entry in cfg['materials']:
  entry['mask']=str((P/maps[entry['base']]['maps']['region_mask']).resolve())
  if level:entry['base']=entry['base'].replace('_A',f'_L{level}_A');entry['prefix']+=f'_L{level}'
 config=P/f'textures/ramps_lod{level}.json';config.write_text(json.dumps(cfg,indent=2));tier=out/f'mm6_natf_tiered_lod{level}.glb';run(P.parent/'claude_shared/region_variants.py',runtime,tier,config,'--extra','Natf','openyamm_specular=0','--extra','Natf','pbr.metallicFactor=0','--extra','LeafShield','openyamm_specular=0','--extra','LeafShield','pbr.metallicFactor=0','--extra','ForearmBlade','openyamm_specular=0.1')
 bladebody=out/f'mm6_natf_with_shield_lod{level}.glb';body=out/f'mm6_natf_body_lod{level}.glb';run(ROOT/'tools/split_attachment.py',tier,'--joint','ForearmBlade','--body',bladebody,'--attachment',out/f'mm6_natf_blade_lod{level}.glb');run(ROOT/'tools/split_attachment.py',bladebody,'--joint','LeafShield','--body',body,'--attachment',out/f'mm6_natf_shield_lod{level}.glb');run(ROOT/'tools/merge_head_material.py',body,body)
run(P/'scripts/pack_lods.py')
for file in out.glob('*.glb'):file.chmod(0o644)
