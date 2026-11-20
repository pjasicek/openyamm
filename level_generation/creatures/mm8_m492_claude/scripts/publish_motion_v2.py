"""Publish the scoped motion revision with byte-checked body, textures, skin and unaffected clips."""
from pathlib import Path
import copy,hashlib,json,shutil,sys
P=Path(__file__).resolve().parents[1];BASE=P/'work/before_motion_v2';OUT=P/'review/motion_v2'
sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,write_glb,accessor_array
from prepare_actor_glb import omit_mesh_nodes
CHANGED=('Attack','Cast','Hit')
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

def omit_flame(doc,data):
    original=copy.deepcopy(doc);before_data=bytes(data)
    mesh_node=next(n for n in doc['nodes'] if n.get('name')=='MouthFire')
    removed=mesh_node['mesh'];used=[i for i in range(len(doc['meshes'])) if i!=removed]
    remap={old:new for new,old in enumerate(used)}
    # The shared omission helper understands scene meshes; keep this engine's extra LOD references reachable too.
    count=len(doc['nodes']);doc['nodes'].extend({'mesh':i} for i in used)
    for a in doc['animations']:
        a['channels']=[c for c in a['channels'] if not doc['nodes'][c['target']['node']].get('name','').startswith('MouthFire')]
    data=omit_mesh_nodes(doc,data,['MouthFire']);del doc['nodes'][count:]
    for mesh in doc['meshes']:
        for key in ['openyamm_lods','openyamm_shadow_lods']:
            if key in mesh.get('extras',{}):mesh['extras'][key]=[remap[i] for i in mesh['extras'][key]]
    # Omission must not discard any body LOD or shadow geometry.
    for old,new in remap.items():
        a=original['meshes'][old];b=doc['meshes'][new]
        for left,right in zip(a['primitives'],b['primitives']):
            for key in left['attributes']:
                assert accessor_array(original,before_data,left['attributes'][key]).tobytes()==accessor_array(doc,data,right['attributes'][key]).tobytes()
            assert accessor_array(original,before_data,left['indices']).tobytes()==accessor_array(doc,data,right['indices']).tobytes()
    return doc,bytearray(data)

def main():
    source,binary=read_glb(P/'work/motion_v2_clips.glb')
    for a in source['animations']:
        a['channels']=[c for c in a['channels'] if not source['nodes'][c['target']['node']].get('name','').startswith('MouthFire')]
    reports=[]
    paths=list((BASE/'export').glob('*.glb'))+list((BASE/'review/viewer').glob('*.glb'))
    for path in paths:
        doc,original_data=read_glb(path)
        if not any(n.get('name')=='MouthFire' and 'mesh' in n for n in doc['nodes']):continue
        doc,data=omit_flame(doc,original_data)
        kept=['geometry']+[a['name'] for a in doc['animations'] if a['name'] not in CHANGED]
        before={name:fingerprint(doc,data,name) for name in kept}
        doc,data=transplant(doc,data,source,binary,CHANGED)
        assert before=={name:fingerprint(doc,data,name) for name in kept},path.name
        for name in CHANGED:assert fingerprint(doc,data,name)==fingerprint(source,binary,name),(path.name,name)
        assert not any(n.get('name')=='MouthFire' and 'mesh' in n for n in doc['nodes'])
        destination=P/path.relative_to(BASE);write_glb(destination,doc,data)
        reports.append({'path':str(destination.relative_to(P)),'preserved':before,'sha256':hashlib.sha256(destination.read_bytes()).hexdigest()})
    assert any(x['path']=='export/mm8_m492.glb' for x in reports)
    shutil.copy2(P/'work/motion_v2.blend',P/'dragon_master.blend')
    (OUT/'preservation.json').write_text(json.dumps(reports,indent=2)+'\n')
    v=P/'review/viewer/manifest.json';manifest=json.loads(v.read_text());manifest.update(revision='motion-v2',default_clip='Attack')
    for model in manifest['models']:
        name=model['url'].split('?')[0];sha=hashlib.sha256((v.parent/name).read_bytes()).hexdigest();model.update(url=name+'?v='+sha[:12],sha256=sha,revision='motion-v2')
    for name in ['Attack','Cast']:
        manifest['clips'][name]['impact']=1.25
        manifest['clips'][name]['provenance']='MM8 frontal attack anchors plus MM6 cdr1 accepted head sweep; deep dip and short forward thrust at the unchanged 1.25s gameplay release, followed by recovery.'
    times=[0,.20,.40,.60,.80,1.00,1.125,1.25,1.375,1.5]
    for name in ['Attack','Cast']:
        for i,a in enumerate(manifest['clips'][name]['anchors']):a.update(time=times[i],label=f'{chr(65+i)} · native {i*.125:.3f}s',phase='native pose retimed to gameplay release')
    manifest['clips']['Hit']['provenance']='Native backward arch, lateral body bank and wide head sweep; 1.25s duration retained.'
    manifest['clips']['Death']['provenance']='Selected grounded collapse retained; flame removed at user request.'
    v.write_text(json.dumps(manifest,indent=2)+'\n')
    print('Published',len(reports),'GLBs; body/skin/maps and other skeletal clips unchanged; flame mesh omitted')

if __name__ == '__main__':
    main()
