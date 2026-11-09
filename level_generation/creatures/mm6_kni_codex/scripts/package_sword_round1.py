import sys,json,hashlib,copy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import assemble_sword_round1 as A
sys.path.insert(0,str(P.parents[2]/'tools'));from merge_head_material import read_glb,write_glb,compact,append_accessor
from split_attachment import split_primitive,compacted
path=P/'work/round1/sword_linked_canonical.glb';d,b=read_glb(path);mat=d['materials'][0];mat['pbrMetallicRoughness']['metallicFactor']=0;mat['extras']={'openyamm_specular':1,'openyamm_specular_mask':True};slot=mat['pbrMetallicRoughness']['metallicRoughnessTexture']['index'];im=d['images'][d['textures'][slot]['source']];data=(P/'textures/sword_round1/metal_rough_1k.png').read_bytes();b.extend(b'\0'*(-len(b)%4));im['bufferView']=len(d['bufferViews']);d['bufferViews'].append({'buffer':0,'byteOffset':len(b),'byteLength':len(data)});b.extend(data)
d['extensionsUsed']=list(dict.fromkeys(d.get('extensionsUsed',[])+['KHR_materials_variants']));d.setdefault('extensions',{})['KHR_materials_variants']={'variants':[{'name':'kni_'+v}for v in 'abc']}
for mesh in d['meshes']:
 for q in mesh['primitives']:q.setdefault('extensions',{})['KHR_materials_variants']={'mappings':[{'material':0,'variants':[0,1,2]}]}
write_glb(path,*compact(d,b));A.localize(path,P/'export/mm6_kni_sword.glb');A.attach(P/'export/mm6_kni.glb',P/'export/mm6_kni_sword.glb',P/'work/round1/runtime_combined.glb')
for tier in 'abc':
 d,b=read_glb(P/f'work/round1/baseline_viewer_{tier}.glb');joint=next(i for i,n in enumerate(d['nodes'])if n.get('name')=='Sword');js=d['skins'][0]['joints'].index(joint)
 for mesh in d['meshes']:
  for q in mesh['primitives']:
   body,item=split_primitive(d,b,q,js);values,indices=compacted(d,b,q,body,sorted(q['attributes']))
   q['attributes']={name:append_accessor(d,b,value,d['accessors'][q['attributes'][name]],34962)for name,value in values.items()};q['indices']=append_accessor(d,b,indices.reshape(-1,1),{'componentType':5125,'type':'SCALAR'},34963)
 temp=P/f'work/round1/viewer_body_{tier}.glb';write_glb(temp,*compact(d,b));A.attach(temp,P/'export/mm6_kni_sword.glb',P/f'review/viewer/mm6_kni_{tier}.glb')
m=json.loads((P/'review/viewer/manifest.json').read_text());m['revision']='mm6_kni_codex_sword_round1'
for model in m['models']:
 name=f"mm6_{model['id']}.glb";model['sha256']=hashlib.sha256((P/'review/viewer'/name).read_bytes()).hexdigest();model['url']=name+'?v='+model['sha256'][:12];model['revision']=m['revision']
m['model_sha256']=m['models'][0]['sha256']
(P/'review/viewer/manifest.json').write_text(json.dumps(m,indent=2)+'\n')
baseline=json.loads((P/'review/round1/baseline.json').read_text())
for path in ['export/mm6_kni.glb','integration/actors.yml','work/runtime_master.blend','work/textured_master.blend','work/production_body.blend']:assert hashlib.sha256((P/path).read_bytes()).hexdigest()==baseline[path]['sha256'],path
print('Packaged sword and three review models; accepted body, rig, source clips and bindings preserved byte-for-byte')
