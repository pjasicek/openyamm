"""Validate the actual GLBs and foot plants after the join/UV/export steps."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parent/'claude_shared/floor'))
from glb_pose import Glb,Model
upload=Glb(P/'work/bulwark_texture_upload.glb');rig=Glb(P/'review/bulwark_rig_preview.glb');model=Model(rig)
assert not upload.json.get('skins') and not upload.json.get('animations')
def corners(g):
    assert len(g.json['meshes'])==1 and len(g.json['meshes'][0]['primitives'])==1
    p=g.json['meshes'][0]['primitives'][0];ix=g.accessor(p['indices']).astype(int).ravel()
    return np.c_[g.accessor(p['attributes']['POSITION'])[ix],g.accessor(p['attributes']['TEXCOORD_0'])[ix]]
assert np.array_equal(corners(upload),corners(rig)), 'Upload differs from animated master geometry or UVs'
p=rig.json['meshes'][0]['primitives'][0];a=p['attributes']
weights=rig.accessor(a['WEIGHTS_0']);joints=rig.accessor(a['JOINTS_0']).astype(int)
assert np.allclose(weights.sum(1),1) and np.all((weights>0).sum(1)==1)
assert np.isfinite(corners(upload)).all()
assert len(corners(upload))//3==10632
assert set(model.clips)=={'Standing','Walking','Running','Attack','Cast','Sweep','Hit','Death','Dead','Fidget'}
foot={}
for leg in ('LF','RF','LH','RH'):
    node=next(i for i,n in enumerate(rig.json['nodes']) if n.get('name')==f'B_{leg}_Foot')
    joint=model.joints.index(node);foot[leg]=np.any((joints==joint)&(weights>0),axis=1)
    assert foot[leg].any()
report={'triangles':10632,'one_influence':True,'static_upload_has_no_skin_or_animations':True,'upload_and_rig_corner_positions_and_uvs_exact':True,'sample_hz':60,'clips':{}}
for clip in model.clips:
    times=model.clip_times(clip);duration=times[-1];minimum=1e9;poses=[];plants={leg:[] for leg in foot};air=0;air_height=0
    for t in np.linspace(0,duration,round(duration*60)+1):
        xyz=model.skinned_positions(model.world(model.sample(clip,t)))[0][0];poses.append(xyz);minimum=min(minimum,float(xyz[:,1].min()))
        if clip in ('Walking','Running'):
            running=clip=='Running';duty=.44 if running else .65;stride=.9 if running else .65
            lowest=min(float(xyz[mask,1].min()) for mask in foot.values());air_height=max(air_height,lowest)
            if lowest>.001:air+=1
            for leg,mask in foot.items():
                phase=(t/duration+(0 if leg in ('LF','RH') else .5))%1
                if .035<phase<duty-.035:
                    centre=xyz[mask].mean(0);centre[2]+=stride*t/duration
                    plants[leg].append((t,centre))
    row={'duration_s':duration,'minimum_y_m':minimum,'samples':len(poses)}
    assert minimum>=-.015,(clip,minimum)
    if clip in ('Standing','Walking','Running','Fidget','Dead'):
        row['loop_error_m']=float(np.linalg.norm(poses[-1]-poses[0],axis=1).max());assert row['loop_error_m']<1e-4
    if clip in ('Walking','Running'):
        slide=0
        for leg,values in plants.items():
            start=None;last=-1
            for t,centre in values:
                if t-last>1.5/60:start=centre
                slide=max(slide,float(np.linalg.norm(centre-start)));last=t
        row.update(planted_foot_slide_m=slide,virtual_forward_speed_mps=stride/duration,aerial_samples_above_1mm=air,maximum_all_feet_clearance_m=air_height)
        assert slide<.003,(clip,'planted slide',slide)
        if clip=='Running':assert air>0
    report['clips'][clip]=row
end=model.skinned_positions(model.world(model.sample('Death',model.clip_times('Death')[-1])))[0][0]
held=model.skinned_positions(model.world(model.sample('Dead',0)))[0][0]
report['death_dead_error_m']=float(np.linalg.norm(end-held,axis=1).max());assert report['death_dead_error_m']<1e-4
report['sha256']={f:hashlib.sha256((P/f).read_bytes()).hexdigest() for f in ('work/bulwark_texture_upload.glb','review/bulwark_rig_preview.glb')}
(P/'review/geometry/upload_gate.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
