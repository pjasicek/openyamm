"""Dense deformation, loop endpoints and orthographic scale samples from the animated master."""
from pathlib import Path
import sys,json,bpy
import numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
from common import coordinates
bpy.ops.wm.open_mainfile(filepath=str(P/'work/uv_master.blend'))
m=bpy.data.objects['Wyvern'];rig=bpy.data.objects['Wyvern_Rig'];sc=bpy.context.scene
edges=np.array([list(e.vertices) for e in m.data.edges]);rest=np.array([tuple(v.co) for v in m.data.vertices]);length=np.linalg.norm(rest[edges[:,0]]-rest[edges[:,1]],axis=1)
report={};fly=[];samples={}
for name in ['Fly','Attack','Hit','Death','Dead']:
    action=bpy.data.actions[name];rig.animation_data.action=action
    a,b=action.frame_range;poses=[];stretches=[];root_z=[]
    for f in np.arange(a,b+.01,.25):
        sc.frame_set(int(f),subframe=float(f%1));co=coordinates(m)
        assert np.isfinite(co).all();assert co[:,2].min()>-.006,(name,f,co[:,2].min())
        poses.append(co)
        root_z.append(float(rig.pose.bones['Spine1'].head.z))
        if name=='Fly':
            times=np.arange(25)/24
            expected=.405+np.interp((f-a)/24,times,.009*np.sin(2*np.pi*times+1))
            actual=root_z[-1]-rig.data.bones['Spine1'].head_local.z
            assert abs(actual-expected)<1e-5,('wing-driven root lift',f,actual,expected)
        delta=np.linalg.norm(co[edges[:,0]]-co[edges[:,1]],axis=1)-length
        stretches.append(float(np.abs(delta).max()))
        for bone in rig.pose.bones:assert np.max(np.abs(np.array(bone.scale)-1))<1e-5
    if name in ['Fly','Dead']:assert np.max(np.abs(poses[0]-poses[-1]))<1e-5
    report[name]={'samples':len(poses),'root_z_range':[min(root_z),max(root_z)],'root_z_travel':max(root_z)-min(root_z),'max_absolute_edge_change':max(stretches),'min_z':float(np.min(np.array(poses)[:,:,2]))}
    samples[name]=np.array(poses)
for name in ['Attack','Hit','Death']:
    assert np.max(np.abs(samples[name][0]-samples['Fly'][0]))<1e-5,(name,'entry pose')
for name in ['Attack','Hit']:
    assert np.max(np.abs(samples[name][-1]-samples['Fly'][0]))<1e-5,(name,'recovery pose')
assert np.max(np.abs(samples['Death'][-1]-samples['Dead'][0]))<1e-5
rig.animation_data.action=bpy.data.actions['Fly']
for i in range(8):
    f=1+i*3;sc.frame_set(f);fly.append(coordinates(m))
triangles=np.array([list(t.vertices) for t in m.data.loop_triangles])
np.savez(P/'work/motion_samples.npz',fly=np.array(fly),triangles=triangles,**samples)
(P/'review/dense_motion.json').write_text(json.dumps(report,indent=2)+'\n')
print('DENSE',report,flush=True)
