"""Install revised Attack/Cast clips without changing the accepted meshes, maps, skins or other clips."""
from pathlib import Path
import copy
import hashlib
import json
import shutil
import sys

P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P.parents[2] / 'tools'))
from merge_head_material import read_glb, write_glb, accessor_array

CHANGED = ('Attack', 'Cast')
BASE = P / 'work/before_motion_v6'
source, binary = read_glb(P / 'work/motion_v6_clips.glb')

def fingerprint(doc, data, part):
    h = hashlib.sha256()
    def add(value):
        h.update(value if isinstance(value, bytes) else json.dumps(value, sort_keys=True).encode())
    if part == 'geometry':
        for name in ('nodes', 'materials', 'extensions', 'scenes'):
            add(doc.get(name))
        for mesh in doc['meshes']:
            add(mesh.get('extras', {}))
            for primitive in mesh['primitives']:
                add({k:v for k,v in primitive.items() if k not in ('indices','attributes')})
                for name,index in sorted(primitive['attributes'].items()):
                    add(name); add(accessor_array(doc, data, index).tobytes())
                add(accessor_array(doc, data, primitive['indices']).tobytes())
        for skin in doc.get('skins', []):
            add(skin['joints']); add(accessor_array(doc, data, skin['inverseBindMatrices']).tobytes())
        for image in doc.get('images', []):
            view=doc['bufferViews'][image['bufferView']]; start=view.get('byteOffset',0)
            add(bytes(data[start:start+view['byteLength']]))
    else:
        animation=next(a for a in doc['animations'] if a['name']==part)
        for channel in animation['channels']:
            add((doc['nodes'][channel['target']['node']]['name'], channel['target']['path']))
            sampler=animation['samplers'][channel['sampler']]
            add(sampler.get('interpolation','LINEAR'))
            for key in ('input','output'):add(accessor_array(doc,data,sampler[key]).tobytes())
    return h.hexdigest()

def transplant(doc, data, src, srcdata, names):
    nodes={n.get('name'):i for i,n in enumerate(doc['nodes'])}; indices={}
    for name in names:
        animation=copy.deepcopy(next(a for a in src['animations'] if a['name']==name))
        for channel in animation['channels']:
            channel['target']['node']=nodes[src['nodes'][channel['target']['node']]['name']]
        for sampler in animation['samplers']:
            for key in ('input','output'):
                old=sampler[key]
                if old not in indices:
                    acc=copy.deepcopy(src['accessors'][old]); packed=accessor_array(src,srcdata,old).tobytes()
                    data.extend(b'\0'*(-len(data)%4))
                    doc['bufferViews'].append({'buffer':0,'byteOffset':len(data),'byteLength':len(packed)})
                    data.extend(packed);acc['bufferView']=len(doc['bufferViews'])-1;acc.pop('byteOffset',None)
                    doc['accessors'].append(acc);indices[old]=len(doc['accessors'])-1
                sampler[key]=indices[old]
        doc['animations'][next(i for i,a in enumerate(doc['animations']) if a['name']==name)]=animation
    # Compact only animation/accessor storage; the accepted custom burn textures stay untouched.
    used=set()
    for mesh in doc['meshes']:
        for primitive in mesh['primitives']:
            used.update(primitive['attributes'].values());used.add(primitive['indices'])
    for skin in doc['skins']:used.add(skin['inverseBindMatrices'])
    for animation in doc['animations']:
        for sampler in animation['samplers']:used.update((sampler['input'],sampler['output']))
    remap={old:new for new,old in enumerate(sorted(used))}
    doc['accessors']=[doc['accessors'][old] for old in sorted(used)]
    for mesh in doc['meshes']:
        for primitive in mesh['primitives']:
            assert not primitive.get('targets')
            primitive['attributes']={k:remap[v] for k,v in primitive['attributes'].items()}
            primitive['indices']=remap[primitive['indices']]
    for skin in doc['skins']:skin['inverseBindMatrices']=remap[skin['inverseBindMatrices']]
    for animation in doc['animations']:
        for sampler in animation['samplers']:
            for key in ('input','output'):sampler[key]=remap[sampler[key]]
    refs=doc['accessors']+doc.get('images',[])
    assert all('sparse' not in acc for acc in doc['accessors'])
    views=[];packed=bytearray();remap={}
    for old in sorted({a['bufferView'] for a in refs}):
        view=copy.deepcopy(doc['bufferViews'][old]);start=view.get('byteOffset',0)
        packed.extend(b'\0'*(-len(packed)%4));view['byteOffset']=len(packed)
        packed.extend(data[start:start+view['byteLength']]);remap[old]=len(views);views.append(view)
    for ref in refs:ref['bufferView']=remap[ref['bufferView']]
    doc['bufferViews']=views
    return doc,packed

reports=[]
for filename in ('mm6_cdr1_selected.glb','mm6_cdr1_runtime_lod0.glb','mm6_cdr1_lods.glb','mm6_cdr1_shadow.glb','mm6_cdr1.glb'):
    doc,data=read_glb(BASE/'export'/filename)
    keep=['geometry']+[a['name'] for a in doc['animations'] if a['name'] not in CHANGED]
    preserved={name:fingerprint(doc,data,name) for name in keep}
    doc,data=transplant(doc,bytearray(data),source,binary,CHANGED)
    assert preserved=={name:fingerprint(doc,data,name) for name in keep}, filename
    for name in CHANGED:assert fingerprint(doc,data,name)==fingerprint(source,binary,name), (filename,name)
    write_glb(P/'export'/filename,doc,data)
    reports.append({'file':filename,'preserved':preserved,'sha256':hashlib.sha256((P/'export'/filename).read_bytes()).hexdigest()})
# Bring the viewer's stale death clips up to the already-installed burning-death skeleton as well.
final, finaldata=read_glb(P/'export/mm6_cdr1_runtime_lod0.glb')
names=[a['name'] for a in final['animations']]
for tier in 'abc':
    filename=f'mm6_cdr1_{tier}.glb'
    doc,data=read_glb(BASE/'review/viewer'/filename)
    before=fingerprint(doc,data,'geometry')
    doc,data=transplant(doc,bytearray(data),final,finaldata,names)
    assert before==fingerprint(doc,data,'geometry')
    for name in names:assert fingerprint(doc,data,name)==fingerprint(final,finaldata,name)
    write_glb(P/'review/viewer'/filename,doc,data)
shutil.copy2(P/'work/motion_v6.blend', P/'export/mm6_cdr1.blend')
(P/'review/motion_v6/preservation.json').write_text(json.dumps(reports,indent=2)+'\n')
print('Animation-only transplant checked:',len(reports),'production and 3 viewer GLBs')
