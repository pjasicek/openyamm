import sys,struct,json
from pathlib import Path
p=Path(__file__).resolve().parents[1];f=p/'export/mm6_mnk1_lod0.glb';raw=f.read_bytes();n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);buf=bytearray(raw[28+n:]);png=(p/'textures/mnk1_orm_1k.png').read_bytes()
mat=doc['materials'][0];tid=mat['pbrMetallicRoughness']['metallicRoughnessTexture']['index'];im=doc['images'][doc['textures'][tid]['source']]
buf.extend(b'\0'*(-len(buf)%4));im['bufferView']=len(doc['bufferViews']);im['mimeType']='image/png';doc['bufferViews'].append({'buffer':0,'byteOffset':len(buf),'byteLength':len(png)});buf.extend(png)
buf.extend(b'\0'*(-len(buf)%4));doc['buffers'][0]['byteLength']=len(buf);enc=json.dumps(doc,separators=(',',':')).encode();enc+=b' '*(-len(enc)%4)
f.write_bytes(struct.pack('<III',0x46546c67,2,28+len(enc)+len(buf))+struct.pack('<II',len(enc),0x4e4f534a)+enc+struct.pack('<II',len(buf),0x004e4942)+buf)
print('Packed baked AO in ORM R; no occlusionTexture enabled.')
