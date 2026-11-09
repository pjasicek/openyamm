"""Final GLB motion corrections, shared-rig checks and binding preparation."""
import copy,json,sys,hashlib
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
P=Path(__file__).resolve().parents[1] if Path(__file__).parent.name=='scripts' else Path.cwd()/'level_generation/creatures/hes_drudge_codex'
ROOT=P.parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'level_generation/creatures/claude_shared/floor')]
from glb_pose import Glb,Model
from merge_head_material import write_glb,compact,append_accessor,accessor_array
source=Glb(P/'work/drudge_after_lod.glb');m=Model(source);d=source.json
names=[n.get('name') for n in d['nodes']];rest=m.world({})
def rotation(w,i):
    a=w[i,:3,:3];return a/np.linalg.norm(a,axis=0)
def replace(animation,node,path,times,values):
    channel=next(c for c in animation['channels'] if c['target']=={'node':node,'path':path})
    animation['samplers'].append({'input':source.append_accessor(np.float32(times)[:,None],'SCALAR'),
        'output':source.append_accessor(np.float32(values),'VEC4' if path=='rotation' else 'VEC3'),'interpolation':'LINEAR'})
    channel['sampler']=len(animation['samplers'])-1
report={}
for clip in ['Drudge_Walking','Drudge_Running','Drudge_Death','Drudge_Dead']:
    animation=d['animations'][m.clips[clip]];duration=max(m.clip_times(clip));times=np.linspace(0,duration,round(duration*120)+1)
    if clip=='Drudge_Death':
        for side in 'LR':
            fi,hi=[names.index('B_'+side+'_'+n) for n in ['Forearm','Hand']]
            rel0=np.linalg.inv(rotation(rest,fi))@rotation(rest,hi)
            axis=np.linalg.inv(rotation(rest,hi))@(rest[hi,:3,3]-rest[fi,:3,3]);axis/=np.linalg.norm(axis)
            quats=[]
            for t in times:
                world=m.world(m.sample(clip,t));rel=np.linalg.inv(rel0)@np.linalg.inv(rotation(world,fi))@rotation(world,hi)
                q=Rotation.from_matrix(rel).as_quat();proj=axis*(q[:3]@axis);tq=np.r_[proj,q[3]];tq/=np.linalg.norm(tq)
                angle=(2*np.arctan2(tq[:3]@axis,tq[3])+np.pi)%(2*np.pi)-np.pi
                swing=Rotation.from_quat(q)*Rotation.from_quat(tq).inv()
                constrained=(swing*Rotation.from_rotvec(axis*np.clip(angle,-np.radians(85),np.radians(85)))).as_matrix()
                desired=rotation(world,fi)@rel0@constrained
                local=np.linalg.inv(rotation(world,m.parent[hi]))@desired
                nq=Rotation.from_matrix(local).as_quat()
                if quats and nq@quats[-1]<0:nq=-nq
                quats.append(nq)
            replace(animation,hi,'rotation',times,quats)
    pelvis=names.index('B_Pelvis');values=[];lifts=[]
    for t in times:
        local=m.sample(clip,t);world=m.world(local);floor=m.lowest(clip,t)
        lift=max(0,.003-floor)
        parent=world[m.parent[pelvis]] if m.parent[pelvis]>=0 else np.eye(4)
        delta=np.linalg.inv(parent[:3,:3])@np.array([0,lift,0])
        values.append(local.get(pelvis,m.rest[pelvis])[0]+delta);lifts.append(lift)
    replace(animation,pelvis,'translation',times,values)
    report[clip]={'max_floor_lift_m':max(lifts),'sample_hz':120}
source.json,source.bin=compact(d,source.bin);write_glb(P/'export/hes_drudge.glb',source.json,source.bin)
other=Glb(P/'work/thrix_after_lod.glb');other.json['animations']=[]
for animation in source.json['animations']:
    a=copy.deepcopy(animation)
    for sampler in a['samplers']:
        for key in ['input','output']:
            index=sampler[key];sampler[key]=append_accessor(other.json,other.bin,accessor_array(source.json,source.bin,index),source.json['accessors'][index],34962)
    other.json['animations'].append(a)
other.json,other.bin=compact(other.json,other.bin);write_glb(P/'export/hes_thrix.glb',other.json,other.bin)
(P/'review/final_motion_corrections.json').write_text(json.dumps(report,indent=2)+'\n')
print(report)
