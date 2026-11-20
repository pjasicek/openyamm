import bpy,os,sys,json,traceback
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P/'scripts'))
import posing as pose
try:
    bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v3.blend'))
    rig=bpy.data.objects['Ashkite_Rig'];mesh=bpy.data.objects['Ashkite']
    rig.animation_data_create();base=pose.coordinates(mesh)
    edges=np.array([tuple(e.vertices) for e in mesh.data.edges]);length=np.linalg.norm(base[edges[:,0]]-base[edges[:,1]],axis=1)
    reports={}
    for name in ['Rest','Opposed','Fold','Whip']:
        rig.animation_data.action=None;pose.reset(rig)
        for side in 'LR':
            pose.wing(rig,'Front',side,50 if name=='Opposed' else (15 if name=='Fold' else 0),15,25 if name=='Fold' else 0,10)
            pose.wing(rig,'Rear',side,-35 if name=='Opposed' else (5 if name=='Fold' else 0),-5,30 if name=='Fold' else 0,-10)
        if name=='Whip':
            pose.rotate(rig,'Neck1','Z',25);pose.rotate(rig,'Neck2','X',-25);pose.rotate(rig,'Head','X',20)
            for i in range(1,8):pose.rotate(rig,'Tail'+str(i),'Z',20)
        c=pose.coordinates(mesh);assert np.isfinite(c).all()
        ratio=np.linalg.norm(c[edges[:,0]]-c[edges[:,1]],axis=1)/np.maximum(length,1e-6)
        reports[name]={'stretch_p99':float(np.percentile(ratio,99)),'stretch_max':float(ratio.max()),'bounds':[c.min(0).tolist(),c.max(0).tolist()],
            'worst_edges':[{'ratio':float(ratio[i]),'rest_length':float(length[i]),'points':base[edges[i]].tolist()} for i in np.argsort(ratio)[-5:]]}
        act=bpy.data.actions.new(name);act.use_fake_user=True;rig.animation_data.action=act
        for b in rig.pose.bones:
            b.keyframe_insert('rotation_quaternion',frame=1);b.keyframe_insert('location',frame=1);b.keyframe_insert('scale',frame=1)
    (P/'review/stress_v3.json').write_text(json.dumps(reports,indent=2)+'\n')
    bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/stress_v3.blend'))
    print(json.dumps(reports),flush=True)
except BaseException:traceback.print_exc();sys.stderr.flush();os._exit(1)
sys.stdout.flush();os._exit(0)
