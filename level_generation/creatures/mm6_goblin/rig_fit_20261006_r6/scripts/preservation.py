"""Check the retained master and actual export; only shoulder/skirt weights and skirt rest geometry are intentional changes."""
import bpy, hashlib, json, struct
import numpy as np
from pathlib import Path

ROOT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin')
OUT=ROOT/'rig_fit_20261006_r6'
def snapshot(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    arm=bpy.data.objects['Goblin_Rig']
    result={'bones':[(b.name,b.parent.name if b.parent else None,list(map(list,b.matrix_local))) for b in arm.data.bones]}
    result['curves']={a.name:[(fc.data_path,fc.array_index,[(tuple(k.co),tuple(k.handle_left),tuple(k.handle_right),k.interpolation,k.handle_left_type,k.handle_right_type) for k in fc.keyframe_points]) for layer in a.layers for strip in layer.strips for bag in strip.channelbags for fc in bag.fcurves] for a in bpy.data.actions}
    result['meshes']={}
    for name in ['Goblin_Body','Goblin_Sword']:
        o=bpy.data.objects[name];m=o.data
        result['meshes'][name]={'positions':np.array([tuple(v.co) for v in m.vertices]),'polygons':[tuple(p.vertices) for p in m.polygons], 'uv':[(layer.name,[tuple(v.uv) for v in layer.data]) for layer in m.uv_layers],'weights':[sorted((o.vertex_groups[g.group].name,g.weight) for g in v.groups) for v in m.vertices]}
    return result
old=snapshot(ROOT/'anatomy_20261006_r5/goblin_anatomy_r5.blend')
new=snapshot(OUT/'goblin_r6.blend')
assert [r[:2] for r in old['bones']]==[r[:2] for r in new['bones']],'bone hierarchy changed'
assert old['bones']==new['bones'],'rig rest matrices changed'
assert old['curves']==new['curves'],'animation curves changed'
assert len(new['curves'])==9
changed={};reweighted={}
for name,a in old['meshes'].items():
    b=new['meshes'][name]
    assert a['polygons']==b['polygons'],name+' topology changed'
    assert a['uv']==b['uv'],name+' UV changed'
    ids=np.flatnonzero(np.any(a['positions']!=b['positions'],axis=1))
    weights=[i for i,(x,y) in enumerate(zip(a['weights'],b['weights'])) if x!=y]
    if name=='Goblin_Body':
        assert ((a['positions'][ids,2]>=.619)&(a['positions'][ids,2]<=.837)&(np.abs(a['positions'][ids,0])<=.25)).all(),'geometry outside cloth changed'
        assert all((.135<abs(a['positions'][i,0])<.37 and 1.00<a['positions'][i,2]<1.315) or (.619<a['positions'][i,2]<.837 and abs(a['positions'][i,0])<=.25) for i in weights),'weights outside shoulders and skirt changed'
    else:assert not len(ids) and not weights,'sword changed'
    changed[name]=len(ids);reweighted[name]=len(weights)

def glb(path):
    data=path.read_bytes();assert data[:4]==b'glTF'
    size=struct.unpack_from('<I',data,12)[0]
    return json.loads(data[20:20+size]),data[28+size:]
def view(doc,bin,index):
    v=doc['bufferViews'][index];start=v.get('byteOffset',0)
    return bin[start:start+v['byteLength']]
def accessor(doc,bin,index):
    a=doc['accessors'][index]
    return {k:v for k,v in a.items() if k!='bufferView'},view(doc,bin,a['bufferView'])
def channels(doc,bin,a):
    result={}
    for c in a['channels']:
        s=a['samplers'][c['sampler']];t=c['target']
        result[(doc['nodes'][t['node']]['name'],t['path'])]=(s.get('interpolation','LINEAR'),accessor(doc,bin,s['input']),accessor(doc,bin,s['output']))
    return result
a,ab=glb(ROOT/'anatomy_20261006_r5/goblin_anatomy_r5.glb');b,bb=glb(OUT/'goblin_r6.glb')
assert [{k:v for k,v in m.items() if k!='extras'} for m in a['materials']]==[{k:v for k,v in m.items() if k!='extras'} for m in b['materials']]
assert a['textures']==b['textures']
assert len(a['images'])==len(b['images'])
for x,y in zip(a['images'],b['images']):assert x['mimeType']==y['mimeType'] and view(a,ab,x['bufferView'])==view(b,bb,y['bufferView']),'embedded texture changed'
assert len(a['skins'])==len(b['skins'])==1
old_bind=np.frombuffer(accessor(a,ab,a['skins'][0]['inverseBindMatrices'])[1],dtype='<f4').reshape(-1,16)
new_bind=np.frombuffer(accessor(b,bb,b['skins'][0]['inverseBindMatrices'])[1],dtype='<f4').reshape(-1,16)
for i,j in enumerate(a['skins'][0]['joints']):
    assert np.array_equal(old_bind[i],new_bind[i]),'bind changed'
def retained_channels(doc,bin,c):return channels(doc,bin,c)
assert {c['name']:retained_channels(a,ab,c) for c in a['animations']}=={c['name']:retained_channels(b,bb,c) for c in b['animations']},'exported motion changed'
report={'status':'pass','old_sha256':hashlib.sha256((ROOT/'anatomy_20261006_r5/goblin_anatomy_r5.glb').read_bytes()).hexdigest(),'new_sha256':hashlib.sha256((OUT/'goblin_r6.glb').read_bytes()).hexdigest(),'changed_vertices':changed,'reweighted_vertices':reweighted,'unchanged':['master topology and UV coordinates','all non-cloth rest geometry and weights outside shoulders; skirt reweighted','sword geometry and weights','64-bone hierarchy and every rest/inverse bind matrix','all action curves and exported samples across nine actions','embedded PNG images, material factors and texture assignments'],'artistic_acceptance':'pending user review; preservation checks do not establish likeness'}
(OUT/'review/preservation_checks.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report),flush=True)
