"""Copy measured geometry into the accepted document; preserve rig and animation sample bytes."""
import copy,struct,json,sys,hashlib
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];R=P/'review/triangle_reduction';E=P/'export'
sys.dont_write_bytecode=True;sys.path.insert(0,str(P.parents[2]/'tools'))
from build_actor_lods import read_glb,write_glb,accessor_bytes,append_accessor,merge_shadow
from merge_head_material import compact,accessor_array
original,payload=read_glb(R/'baseline/export/mm6_lch_runtime_lod0.glb')
doc=copy.deepcopy(original);binary=bytearray(payload)
node=next(n for n in doc['nodes'] if n.get('name')=='Lich');mi=node['mesh']
assert len(doc['meshes'])==1 and mi==0
skin=doc['skins'][node['skin']];names=[doc['nodes'][n]['name']for n in skin['joints']]
bind=accessor_array(doc,binary,skin['inverseBindMatrices'])
materials={m['name']:i for i,m in enumerate(doc['materials'])}
counts=[]
for level in range(4):
    source,data=read_glb(P/f'work/round1/lod{level}_geometry.glb')
    sn=next(n for n in source['nodes']if n.get('name')=='Lich');ss=source['skins'][sn['skin']]
    remap=[names.index(source['nodes'][n]['name'])for n in ss['joints']]
    sb=accessor_array(source,data,ss['inverseBindMatrices'])
    assert np.max(np.abs(sb-bind[remap]))<1e-4
    for key,default in [('translation',[0,0,0]),('rotation',[0,0,0,1]),('scale',[1,1,1])]:
        assert np.max(np.abs(np.array(node.get(key,default))-sn.get(key,default)))<1e-4
    mesh={'name':f'Lich_LOD{level}','primitives':[]}
    for primitive in source['meshes'][sn['mesh']]['primitives']:
        attrs={}
        for semantic,index in primitive['attributes'].items():
            accessor=source['accessors'][index];packed=accessor_bytes(source,data,index)
            if semantic.startswith('JOINTS_'):
                code={5121:'B',5123:'H'}[accessor['componentType']]
                values=[remap[v[0]]for v in struct.iter_unpack('<'+code,packed)]
                packed=struct.pack('<'+code*len(values),*values)
            attrs[semantic]=append_accessor(doc,binary,accessor,packed)
        index=primitive['indices']
        mesh['primitives'].append({'attributes':attrs,'indices':append_accessor(doc,binary,source['accessors'][index],accessor_bytes(source,data,index)),
            'material':materials[source['materials'][primitive['material']]['name'].split('.')[0]]})
    count=sum(doc['accessors'][p['indices']]['count']//3 for p in mesh['primitives']);counts.append(count)
    if level==0:
        doc['meshes'][0]=mesh
        single,packed=compact(copy.deepcopy(doc),binary)
        write_glb(E/'mm6_lch_runtime_lod0.glb',single,packed)
    else:doc['meshes'].append(mesh)
assert all(a>b for a,b in zip(counts,counts[1:])),counts
for level in range(4):doc['meshes'].append(merge_shadow(doc,binary,doc['meshes'][level]))
doc['meshes'][0]['extras']={'openyamm_lods':[1,2,3],'openyamm_shadow_lods':[4,5,6,7]}
doc,binary=compact(doc,binary);write_glb(E/'mm6_lch_lods.glb',doc,binary)
(E/'lods.json').write_text(json.dumps({'triangles':counts,'colour_meshes':[0,1,2,3],'shadow_meshes':[4,5,6,7],
    'source':'review/triangle_reduction/selected.json','method':'independent measured switch-distance fits, preserved original rig/clips'},indent=2)+'\n')
print('PACKED_MEASURED_LEVELS',counts)
