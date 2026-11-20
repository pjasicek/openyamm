"""Shared jerk_probe measurements on the final GLB at the viewer's 48 fps (no render)."""
import json,sys
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parent/'claude_shared/floor'))
from glb_pose import Glb,Model
m=Model(Glb(P/'export/hes_drudge.glb'));names=[n.get('name') for n in m.glb.json['nodes']]
bones=['B_Head','B_Neck','B_Spine2']+['B_'+s+'_'+part for s in 'LR' for part in ['UpperArm','Forearm','Hand','Foot']]
report={}
for clip in m.clips:
    end=max(m.clip_times(clip));times=np.unique(np.r_[np.arange(0,end,1/48),end]);world=np.array([m.world(m.sample(clip,t)) for t in times]);out={}
    for bone in bones:
        r=world[:,names.index(bone),:3,:3];r=r/np.linalg.norm(r,axis=1)[:,None,:]
        q=Rotation.from_matrix(r);step=np.degrees((q[:-1].inv()*q[1:]).magnitude());d2=np.abs(np.diff(step))
        assert np.isfinite(step).all()
        i=int(np.argmax(step));j=int(np.argmax(d2)) if len(d2) else 0
        out[bone]={'max_step_degrees':float(step[i]),'step_time':float(times[i]),'max_step_change_degrees':float(d2[j]) if len(d2) else 0,'change_time':float(times[j]),'loop_seam_degrees':float(np.degrees((q[0].inv()*q[-1]).magnitude()))}
        if clip in ['Drudge_Walking','Drudge_Running']:assert out[bone]['loop_seam_degrees']<.05,(clip,bone)
    report[clip]=out
(P/'review/jerk_48fps.json').write_text(json.dumps({'sample_hz':48,'method':'shared jerk_probe.py angular step and second difference; visual interpretation remains with integrator','clips':report},indent=2)+'\n')
for clip in ['Drudge_Walking','Drudge_Running','Drudge_Death']:
 print(clip,'max angular step',round(max(r['max_step_degrees'] for r in report[clip].values()),2),'degrees')
