"""Refresh embedded body maps without touching any mesh, rig or animation samples."""
import sys, json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parents[2]/'tools'))
import merge_head_material as G
import normal_map_convention as N
for name in ['mm8_m576_lod0.glb','mm8_m576_prepared.glb','mm8_m576_lods_raw.glb']:
    doc,binary=G.read_glb(P/'export'/name)
    before=[G.accessor_array(doc,binary,i).tobytes() for i in range(len(doc['accessors']))]
    found=set()
    for image in doc['images']:
        if image.get('name') not in ('body_basecolor','body_normal','body_orm'):
            continue
        payload=(P/'textures'/(image['name']+'.png')).read_bytes()
        binary.extend(b'\0'*(-len(binary)%4))
        image['bufferView']=len(doc['bufferViews']);image['mimeType']='image/png'
        doc['bufferViews'].append({'buffer':0,'byteOffset':len(binary),'byteLength':len(payload)})
        binary.extend(payload);found.add(image['name'])
    assert len(found)==3
    destination=P/'export'/name
    G.write_glb(destination,doc,binary)
    if name!='mm8_m576_lod0.glb':
        print(N.convert(destination,destination,threshold=.15))
    doc,binary=G.read_glb(destination)
    assert before==[G.accessor_array(doc,binary,i).tobytes() for i in range(len(doc['accessors']))]
    print(name,': all mesh, skin and animation accessor bytes unchanged')
