"""Probe every half-frame: feet/hands, stretch, anatomical wrist bend and disjoint skin-surface intersections."""
import bpy,json,sys,os,math
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
path=P/'work'/(a[0] if a else 'rig_animated.blend');tag=a[1] if len(a)>1 else 'initial'
bpy.ops.wm.open_mainfile(filepath=str(path));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;sc=bpy.context.scene
co=np.array([v.co[:] for v in me.vertices]);edges=np.array([e.vertices[:] for e in me.edges]);restlen=np.linalg.norm(co[edges[:,0]]-co[edges[:,1]],axis=1)
assert (restlen>1e-8).all()
pieces=np.array([x.value for x in me.attributes['piece'].data]);names=[g.name for g in body.vertex_groups]
W=np.zeros((len(co),len(names)))
for v in me.vertices:
    for g in v.groups:W[v.index,g.group]=g.weight
armw=W[:,[i for i,n in enumerate(names) if any(x in n for x in ['UpperArm','Forearm','Hand','Finger'])]].sum(1)
handw=W[:,[i for i,n in enumerate(names) if 'Hand' in n or 'Finger' in n]].sum(1)
armEdges=(armw[edges[:,0]]>.3)&(armw[edges[:,1]]>.3)
handEdges=(handw[edges[:,0]]>.3)&(handw[edges[:,1]]>.3)
feet={s:np.where(W[:,[i for i,n in enumerate(names) if n in ['B_'+s+'_Foot','B_'+s+'_Toe0']]].sum(1)>.5)[0] for s in ['L','R']}
hands={s:np.where((handw>.5)&(co[:,0]*(1 if s=='L' else -1)>0))[0] for s in ['L','R']}
faceids=[tuple(f.vertices) for f in me.polygons if pieces[f.vertices[0]]==0]
sacfaces=[tuple(f.vertices) for f in me.polygons if pieces[f.vertices[0]]==100]
legw=W[:,[i for i,n in enumerate(names) if any(x in n for x in ['Thigh','Calf','Foot','Toe'])]].sum(1)
trunkw=W[:,[i for i,n in enumerate(names) if n in ['B_Pelvis','B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head']]].sum(1)
regions={
 'arms':[f for f in faceids if all(armw[i]>.9 for i in f)],
 'legs':[f for f in faceids if all(legw[i]>.9 for i in f)],
 'torso_head':[f for f in faceids if all(trunkw[i]>.9 and co[i,2]>1.03 for i in f)]}
assert all(regions.values())
armsides={side:[f for f in faceids if all(armw[i]>.9 and co[i,0]*(1 if side=='L' else -1)>0 for i in f)] for side in ['L','R']}
tracked=['B_Head','B_L_UpperArm','B_R_UpperArm','B_L_Hand','B_R_Hand','B_L_Foot','B_R_Foot']
result={}
for name in ['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget','Cast']:
    act=bpy.data.actions.get(name)
    if act is None:continue
    rig.animation_data.action=act
    if len(act.slots):rig.animation_data.action_slot=act.slots[0]
    f0,f1=act.frame_range
    r={'duration':float((f1-f0)/sc.render.fps),'min_z':1e9,'max_lowest_foot_z':-1e9,'min_hand_z':1e9,'arm_stretch_p99':0,'hand_stretch_max':0,'wrist_bend_deg':0,'arm_leg_intersections':0,'arm_torso_head_intersections':0,'arm_arm_intersections':0,'sac_arm_intersections':0,'worst_frames':{},'rotation_step_deg':0}
    previous=None;frames=[]
    for f in np.arange(f0,f1+.0001,.5):
        sc.frame_set(int(f),subframe=float(f-int(f)))
        ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();arr=np.empty(len(mesh.vertices)*3);mesh.vertices.foreach_get('co',arr);ev.to_mesh_clear();v=arr.reshape(-1,3)
        assert len(v)==len(co) and np.isfinite(v).all()
        stretch=np.linalg.norm(v[edges[:,0]]-v[edges[:,1]],axis=1)/restlen
        metrics={'arm_stretch_p99':float(np.percentile(stretch[armEdges],99)),'hand_stretch_max':float(stretch[handEdges].max())}
        wrist=0
        for s in ['L','R']:
            elbow,hand,finger=[rig.pose.bones['B_'+s+'_'+n].head for n in ['Forearm','Hand','Finger2']]
            wrist=max(wrist,math.degrees((hand-elbow).angle(finger-hand)))
        metrics['wrist_bend_deg']=wrist
        points=v.tolist();trees={key:BVHTree.FromPolygons(points,faces,all_triangles=True) for key,faces in regions.items()}
        metrics['arm_leg_intersections']=len(trees['arms'].overlap(trees['legs']))
        metrics['arm_torso_head_intersections']=len(trees['arms'].overlap(trees['torso_head']))
        metrics['arm_arm_intersections']=len(BVHTree.FromPolygons(points,armsides['L'],all_triangles=True).overlap(BVHTree.FromPolygons(points,armsides['R'],all_triangles=True)))
        if sacfaces:metrics['sac_arm_intersections']=len(trees['arms'].overlap(BVHTree.FromPolygons(points,sacfaces,all_triangles=True)))
        rotations={n:rig.pose.bones[n].matrix.to_quaternion() for n in tracked}
        if previous:
            angles=[previous[n].rotation_difference(rotations[n]).angle for n in tracked]
            metrics['rotation_step_deg']=math.degrees(max(min(x,2*math.pi-x) for x in angles))
        previous=rotations
        for key,value in metrics.items():
            if value>r[key]:
                r[key]=value;r['worst_frames'][key]=float(f)
                if key=='hand_stretch_max':
                    k=np.where(handEdges)[0][int(np.argmax(stretch[handEdges]))];r['worst_hand_edge']={'ids':edges[k].tolist(),'rest':co[edges[k]].tolist(),'posed':v[edges[k]].tolist(),'weights':[{names[j]:float(W[i,j]) for j in np.where(W[i]>.001)[0]} for i in edges[k]]}
        footmin=min(float(v[ids,2].min()) for ids in feet.values());handmin=min(float(v[ids,2].min()) for ids in hands.values())
        r['min_z']=min(r['min_z'],float(v[:,2].min()));r['max_lowest_foot_z']=max(r['max_lowest_foot_z'],footmin);r['min_hand_z']=min(r['min_hand_z'],handmin)
        if abs(f-round(f))<.01:frames.append({'frame':float(f),'foot_min':footmin,'hand_min':handmin,'min_z':float(v[:,2].min()),'pelvis':list(rig.pose.bones['B_Pelvis'].head)})
    result[name]=r;r['frames']=frames
    (P/'review'/('motion_'+tag+'.json')).write_text(json.dumps(result,indent=2)+'\n')
    print('PROBE',name,json.dumps({k:v for k,v in r.items() if k!='frames'}),flush=True)
sys.stdout.flush();sys.stderr.flush();os._exit(0)
