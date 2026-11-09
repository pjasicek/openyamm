"""Shorten only Attack B's opening through viewer frame 28 (48 fps), preserving the pose path."""
from pathlib import Path
import copy, hashlib, json, sys
import numpy as np
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parent/'claude_shared'))
from region_variants import read_glb,write_glb
CUT=28/48
FACTOR=.7
SHIFT=CUT*(1-FACTOR)
CLIP='AttackRPG6'
OUT=P/'review/attack_windup';OUT.mkdir(parents=True,exist_ok=True)
VIEW=P/'review/viewer'

def warp(t):
    return np.where(np.asarray(t)<=CUT,np.asarray(t)*FACTOR,np.asarray(t)-SHIFT)

def sample(times,values,t,rotation,interpolation):
    i=int(np.clip(np.searchsorted(times,t,side='right')-1,0,len(times)-2))
    if t>=times[-1]:return values[-1].copy()
    if interpolation=='STEP':return values[i].copy()
    f=float(np.clip((t-times[i])/(times[i+1]-times[i]),0,1))
    a,b=values[i].astype(float),values[i+1].astype(float)
    if not rotation:return a*(1-f)+b*f
    a/=np.linalg.norm(a);b/=np.linalg.norm(b)
    dot=float(a@b)
    if dot<0:b=-b;dot=-dot
    angle=np.arccos(np.clip(dot,-1,1))
    if angle<1e-5:q=a*(1-f)+b*f
    else:q=(np.sin((1-f)*angle)*a+np.sin(f*angle)*b)/np.sin(angle)
    return q/np.linalg.norm(q)

# Check the exact join and unchanged elapsed time after it.
assert abs(float(warp(CUT))-CUT*FACTOR)<1e-12
assert abs(float(warp(CUT+.25)-warp(CUT))-.25)<1e-12
report={}
for tier in 'abc':
    source=VIEW/f'mm6_fgt_attacks_{tier}.glb';doc,raw=read_glb(source)
    original=copy.deepcopy(doc);binary=bytearray(raw)
    old=next(a for a in original['animations'] if a['name']==CLIP)
    animation=next(a for a in doc['animations'] if a['name']==CLIP)
    def read(index):
        a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']]
        n={'SCALAR':1,'VEC3':3,'VEC4':4}[a['type']]
        assert a['componentType']==5126 and 'sparse' not in a
        return np.ndarray((a['count'],n),dtype='<f4',buffer=raw,
            offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',n*4),4)).copy()
    def append(values,template):
        a=copy.deepcopy(doc['accessors'][template]);a.pop('byteOffset',None)
        data=np.asarray(values,dtype='<f4');binary.extend(b'\0'*(-len(binary)%4))
        view={'buffer':0,'byteOffset':len(binary),'byteLength':data.nbytes}
        binary.extend(data.tobytes());a['bufferView']=len(doc['bufferViews']);doc['bufferViews'].append(view)
        a['count']=len(data)
        if 'min' in a:a['min']=data.min(axis=0).tolist()
        if 'max' in a:a['max']=data.max(axis=0).tolist()
        result=len(doc['accessors']);doc['accessors'].append(a)
        return result
    time_cache={};maximum=0;duration=0
    for i,sampler in enumerate(animation['samplers']):
        previous=old['samplers'][i]
        times=read(previous['input']).ravel();values=read(previous['output'])
        kind=previous.get('interpolation','LINEAR');assert kind in ('LINEAR','STEP')
        paths={c['target']['path'] for c in animation['channels'] if c['sampler']==i}
        assert len(paths)==1
        rotation='rotation' in paths
        # Split the original interpolation segment at the rate-change boundary.
        index=int(np.searchsorted(times,CUT));assert 0<index<len(times)
        at_cut=sample(times,values,CUT,rotation,kind)
        knots=np.insert(times.astype(float),index,CUT)
        outputs=np.insert(values,index,at_cut,axis=0)
        new_times=np.asarray(warp(knots),dtype='<f4')
        assert np.all(np.diff(new_times)>0)
        assert np.array_equal(np.delete(outputs,index,axis=0),values)
        for t in np.unique(np.r_[np.linspace(0,times[-1],257),knots]):
            before=sample(times,values,t,rotation,kind)
            after=sample(new_times,outputs,float(warp(t)),rotation,kind)
            if rotation and before@after<0:after=-after
            maximum=max(maximum,float(np.max(np.abs(before-after))))
        if previous['input'] not in time_cache:
            time_cache[previous['input']]=append(new_times[:,None],previous['input'])
        sampler['input']=time_cache[previous['input']]
        sampler['output']=append(outputs,previous['output'])
        duration=max(duration,float(new_times[-1]))
    assert maximum<1e-5,maximum
    target=VIEW/f'mm6_fgt_windup_{tier}.glb';write_glb(target,doc,binary)
    check,check_binary=read_glb(target)
    assert bytes(check_binary[:len(raw)])==bytes(raw)
    for key in ('nodes','meshes','skins','materials','images','textures','samplers'):
        assert check.get(key)==original.get(key),key
    assert [a for a in check['animations'] if a['name']!=CLIP]==[a for a in original['animations'] if a['name']!=CLIP]
    report[tier]={'path':str(target.relative_to(P)),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
        'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'preserved_binary_bytes':len(raw),
        'unchanged_clips':12,'max_pose_component_error':maximum,'duration':duration}
metadata={'clip':CLIP,'original_cut_frame':28,'viewer_fps':48,'original_cut_seconds':CUT,
 'windup_duration_factor':FACTOR,'new_cut_seconds':CUT*FACTOR,'time_saved_seconds':SHIFT,
 'original_duration':44/30,'duration':44/30-SHIFT,'original_peak_tip_time':.6833333333333333,
 'peak_tip_time':.6833333333333333-SHIFT,'tiers':report}
(OUT/'retime.json').write_text(json.dumps(metadata,indent=2)+'\n')
# Use a saved input manifest so reruns preserve the same comparison clips.
if not (OUT/'manifest_before.json').exists():
    (OUT/'manifest_before.json').write_bytes((VIEW/'manifest.json').read_bytes())
manifest=json.loads((OUT/'manifest_before.json').read_text())
manifest.update(revision='mm6_fgt_attack_windup',model='mm6_fgt_windup_a.glb',default_clip=CLIP)
for model,tier in zip(manifest['models'],'abc'):
    info=report[tier];model.update(url=Path(info['path']).name+'?v='+info['sha256'][:12],sha256=info['sha256'],revision=manifest['revision'])
manifest['clips'][CLIP].update(label='Attack B — selected, faster windup',duration=metadata['duration'],
 provenance='SwordAttackR6. Opening through old viewer frame 28 (48 fps) takes 30% less time; strike and recovery retain their speed.')
(VIEW/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
html=VIEW/'index.html';s=html.read_text();s=s.replace('Attack auditions from the RPG and updated Mixamo libraries. Running is approved. Select attacks A–C to compare their standing swings; earlier attacks remain available.', 'Selected RPG downward swing: 30% shorter windup through original frame 28 at 48 fps. Strike and recovery retain their speed. Running is approved.')
html.write_text(s)
print(json.dumps(metadata,indent=2))
