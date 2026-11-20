"""Replace authored maps while preserving audited geometry, skin and clip bytes."""
from pathlib import Path
import sys
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'));from link_static_model_lods import read_glb,write_glb
for name in ['mm8_m516_lod0.glb','mm8_m516_runtime_lod0.glb','mm8_m516_lods.glb']:
 path=P/'export'/name;d,b=read_glb(path);b=bytearray(b)
 for im in d['images']:
  raw=(P/'textures'/(im['name']+'.png')).read_bytes();b+=b'\0'*(-len(b)%4);im['bufferView']=len(d['bufferViews']);d['bufferViews'].append({'buffer':0,'byteOffset':len(b),'byteLength':len(raw)});b+=raw
 write_glb(path,d,b)
 print('MAPS',name)
