"""Refresh colour only in prepared exports; preserve every mesh/skin/animation buffer verbatim."""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'claude_shared'))
from region_variants import read_glb,write_glb
p=Path(__file__).resolve().parents[1]
image=(p/'textures/fgt_basecolor_1k.png').read_bytes()
report={}
for name in ['mm6_fgt_lod0.glb','mm6_fgt_runtime_lod0.glb','mm6_fgt_lods.glb']:
 path=p/'export'/name;doc,binary=read_glb(path)
 changed=next(i['bufferView'] for i in doc['images'] if i.get('name')=='fgt_basecolor_1k')
 packed=bytearray();original_views=[]
 for index,view in enumerate(doc['bufferViews']):
  start=view.get('byteOffset',0);data=binary[start:start+view['byteLength']];original_views.append(data)
  if index==changed:data=image
  packed+=b'\0'*(-len(packed)%4);view['byteOffset']=len(packed);view['byteLength']=len(data);packed+=data
 write_glb(path,doc,packed)
 check,new=read_glb(path)
 for index,view in enumerate(check['bufferViews']):
  start=view.get('byteOffset',0);data=new[start:start+view['byteLength']]
  assert data==(image if index==changed else original_views[index]),(name,index)
 report[name]={'preserved_non_colour_buffers':len(original_views)-1,'replaced_images':1}
(p/'review/revision3/source_buffer_preservation.json').write_text(json.dumps(report,indent=2)+'\n')
print(report)
