"""Remove Blender-only specular metadata at the final export boundary, without touching binary data."""
import sys,json,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,write_glb
receipt={}
for path in sorted((P/'export').glob('*.glb'))+sorted((P/'review/viewer').glob('*.glb')):
 before=hashlib.sha256(path.read_bytes()).hexdigest();doc,binary=read_glb(path);removed=0
 for material in doc.get('materials',[]):
  extensions=material.get('extensions',{})
  if 'KHR_materials_specular' in extensions:
   del extensions['KHR_materials_specular'];removed+=1
  if not extensions:material.pop('extensions',None)
 for key in ('extensionsUsed','extensionsRequired'):
  if key in doc:
   doc[key]=[e for e in doc[key] if e!='KHR_materials_specular']
   if not doc[key]:del doc[key]
 write_glb(path,doc,binary)
 verified,verified_binary=read_glb(path)
 assert verified==doc and verified_binary==binary, path
 assert all(set(m.get('extensions',{}))<={'KHR_materials_variants','KHR_materials_emissive_strength','KHR_texture_transform'} for m in verified.get('materials',[])),path
 receipt[str(path.relative_to(P))]={'before_sha256':before,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size,'removed_specular_materials':removed,'binary_payload_unchanged':True,'binary_sha256':hashlib.sha256(binary).hexdigest(),'triangles_per_mesh':[sum(doc['accessors'][q['indices']]['count']//3 for q in mesh['primitives']) for mesh in doc['meshes']]}
V=P/'review/viewer';manifest=json.loads((V/'manifest.json').read_text())
for m in manifest['models']:
 name=f"mm6_{m['id']}.glb";m['sha256']=hashlib.sha256((V/name).read_bytes()).hexdigest();m['url']=name+'?v='+m['sha256'][:12]
manifest['model_sha256']=manifest['models'][0]['sha256'];(V/'manifest.json').write_text(json.dumps(manifest,indent=2))
(P/'review/material_extensions.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
