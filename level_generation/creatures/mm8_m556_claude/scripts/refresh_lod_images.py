"""Refresh maps after a material-only revision; assert every LOD0 accessor is unchanged."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path('tools').resolve()))
from build_actor_lods import read_glb,write_glb,accessor_bytes
P=Path(__file__).resolve().parents[1]/'export'
source,payload=read_glb(P/'mm8_m556_runtime_lod0.glb');doc,binary=read_glb(P/'mm8_m556_lods.glb');binary=bytearray(binary)
for i in range(len(source['accessors'])):assert accessor_bytes(source,payload,i)==accessor_bytes(doc,binary,i),(i,'Geometry or animation changed: rebuild LODs')
for img in source['images']:
 dest=next(i for i in doc['images'] if i['name']==img['name']);view=source['bufferViews'][img['bufferView']];offset=view.get('byteOffset',0);data=payload[offset:offset+view['byteLength']];binary.extend(b'\0'*(-len(binary)%4));doc['bufferViews'][dest['bufferView']]={'buffer':0,'byteOffset':len(binary),'byteLength':len(data)};binary.extend(data)
write_glb(P/'mm8_m556_lods.glb',doc,binary)
