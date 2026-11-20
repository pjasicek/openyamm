from pathlib import Path
import json,struct
p=Path('level_generation/creatures/mm6_ert_codex')
# The renderer's explicit specular mask carries the intended matte response.
# Blender's portable KHR specular extension is unsupported by this runtime.
for path in [p/'export/mm6_ert_runtime_lod0.glb',p/'export/mm6_ert.glb',Path('assets_dev/worlds/mm6/models/mm6_ert.glb')]:
 raw=path.read_bytes(); n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);binary=raw[28+n:]
 for m in doc['materials']:
  ext=m.get('extensions',{});ext.pop('KHR_materials_specular',None)
  if not ext:m.pop('extensions',None)
 for k in ['extensionsUsed','extensionsRequired']:
  if k in doc:doc[k]=[s for s in doc[k] if s!='KHR_materials_specular']
 enc=json.dumps(doc,separators=(',',':')).encode();enc+=b' '*(-len(enc)%4)
 path.write_bytes(struct.pack('<III',0x46546c67,2,28+len(enc)+len(binary))+struct.pack('<II',len(enc),0x4e4f534a)+enc+struct.pack('<II',len(binary),0x004e4942)+binary)
 print('Runtime specular extension removed:',path)
