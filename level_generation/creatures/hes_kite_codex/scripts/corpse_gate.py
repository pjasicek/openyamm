import bpy,os,sys,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import posing as pose
bpy.ops.wm.open_mainfile(filepath=str(P/'work/animated_v3.blend'));r=bpy.data.objects['Ashkite_Rig'];o=bpy.data.objects['Ashkite'];r.animation_data.action=bpy.data.actions['Dead'];bpy.context.scene.frame_set(1)
c=pose.coordinates(o);d=np.load(P/'work/surface_v3.npz');v=d['positions'];domain=d['domains'];body=(domain=='Body')&(v[:,1]>-.4)&(v[:,1]<.05)&(v[:,2]>.27)
report={'body_min_z':float(c[body,2].min()),'whole_min_z':float(c[:,2].min()),'wings':{}}
for part in ['Front_L','Front_R','Rear_L','Rear_R']:
 z=c[(domain==part)&(abs(v[:,0])>.5),2];report['wings'][part]={'min':float(z.min()),'max':float(z.max()),'mean':float(z.mean())}
assert report['body_min_z'] <= .025, report
assert abs(report['whole_min_z']) < 1e-5, report
assert all(w['mean'] < .12 for w in report['wings'].values()), report
(P/'review/corpse_gate.json').write_text(json.dumps(report,indent=2)+'\n');print(report,flush=True);os._exit(0)
