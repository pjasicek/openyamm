"""Numeric half-frame gates on the actual GLB; shared pose evaluator + Blender's triangle BVH.
Run in background Blender (no viewer/render). All inherited clips remain subject to measurement.
"""
import json,sys,os,math
from pathlib import Path
import numpy as np
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1]; ROOT=P.parents[2]
sys.path.insert(0,str(ROOT/'level_generation/creatures/claude_shared/floor'))
from glb_pose import Glb,Model
args=sys.argv[sys.argv.index('--')+1:]
m=Model(Glb(args[0]));d=m.glb.json; names=[n.get('name') for n in d['nodes']]; w0=m.world({})
rest=m.skinned_positions(w0); pos=np.concatenate([p for p,t in rest]); faces=[]; start=0; weight=[]
for prim,(v,t) in zip(m.primitives,rest):
    faces.extend((t+start).tolist());start+=len(v)
    mat=np.zeros((len(v),len(m.joints)))
    for col in range(4): mat[np.arange(len(v)),prim['joints'][:,col]]+=prim['weights'][:,col]
    weight.append(mat)
weight=np.concatenate(weight);faces=np.array(faces)
jn=[names[i] for i in m.joints]
def mask(side,parts,threshold):
    ids=[i for i,n in enumerate(jn) if n.startswith('B_'+side+'_') and any(p in n for p in parts)]
    return weight[:,ids].sum(1)>threshold
edges=np.unique(np.sort(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),1),axis=0)
l0=np.linalg.norm(pos[edges[:,0]]-pos[edges[:,1]],axis=1)
hand={s:mask(s,['Hand','Finger'],.5) for s in 'LR'}
arm={s:mask(s,['UpperArm','Forearm'],.3)&~hand[s] for s in 'LR'}
sole={s:mask(s,['Foot','Toe'],.5) for s in 'LR'}
arm_edges={s:np.all(arm[s][edges],axis=1)&(l0>1e-5) for s in 'LR'}
hand_edges={s:np.all(hand[s][edges],axis=1)&(l0>1e-5) for s in 'LR'}
head_ids=[i for i,n in enumerate(jn) if n in ['B_Head','Bone_025']]
head=weight[:,head_ids].sum(1)>.5; head_faces=faces[np.all(head[faces],axis=1)]
body_faces={s:faces[np.all(~mask(s,['Clavicle','UpperArm','Forearm','Hand','Finger'],.15)[faces],axis=1)] for s in 'LR'}
parts=[]
for part in json.loads((P/'export/attachments.json').read_text()):
    pg=Glb(P/'export'/part['file']); pts=[]
    for p in pg.json['meshes'][0]['primitives']:pts.extend(pg.accessor(p['attributes']['POSITION']).tolist())
    parts.append((part['file'],names.index(part['node']),np.unique(np.round(pts,7),axis=0)))
report={}
for clip in (args[2:] or m.clips):
    duration=max(m.clip_times(clip));times=np.linspace(0,duration,max(2,round(duration*60)+1))
    record={};floors=[];feet={s:[] for s in 'LR'};twist={s:[] for s in 'LR'};pelvis=[]
    def maximum(key,value,t):
        if key not in record or value>record[key]['value']:record[key]={'value':round(float(value),5),'time':round(float(t),5)}
    def minimum(key,value,t):maximum(key,-value,t)
    for t in times:
        world=m.world(m.sample(clip,t)); v=np.concatenate([p for p,_ in m.skinned_positions(world)])
        stretch=np.linalg.norm(v[edges[:,0]]-v[edges[:,1]],axis=1)/np.maximum(l0,1e-6)
        floors.append(float(v[:,1].min()));pelvis.append(world[names.index('B_Pelvis'),:3,3])
        headtree=BVHTree.FromPolygons(v.tolist(),head_faces.tolist(),all_triangles=True)
        for name,joint,pts in parts:
            points=(world[joint]@np.c_[pts,np.ones(len(pts))].T).T[:,:3]
            dist=min(headtree.find_nearest(Vector(p))[3] for p in points)
            minimum(name+'_head_clearance',dist,t)
        for s in 'LR':
            maximum(s+'_arm_p99',np.percentile(stretch[arm_edges[s]],99),t)
            maximum(s+'_hand_max',stretch[hand_edges[s]].max(),t)
            fi,hi=[names.index('B_'+s+'_'+p) for p in ['Forearm','Hand']]
            rotation=lambda w,i:Matrix(w[i,:3,:3]).normalized()
            rest_rel=rotation(w0,fi).inverted()@rotation(w0,hi)
            rel=rest_rel.inverted()@(rotation(world,fi).inverted()@rotation(world,hi))
            q=rel.to_quaternion();axis=(rotation(w0,hi).inverted()@Vector(w0[hi,:3,3]-w0[fi,:3,3])).normalized()
            vec=Vector((q.x,q.y,q.z));proj=axis*vec.dot(axis)
            from mathutils import Quaternion
            tw=Quaternion((q.w,*proj));tw.normalize();sw=q@tw.inverted()
            maximum(s+'_wrist_swing_deg',math.degrees(min(sw.angle,2*math.pi-sw.angle)),t)
            twist[s].append(2*math.atan2(Vector((tw.x,tw.y,tw.z)).dot(axis),tw.w))
            tree=BVHTree.FromPolygons(v.tolist(),body_faces[s].tolist(),all_triangles=True)
            penetration=0
            for point in v[hand[s]]:
                loc,n,idx,distance=tree.find_nearest(Vector(point),.08)
                if loc is not None and (Vector(point)-loc).dot(n)<-.7*distance:penetration=max(penetration,distance)
            maximum(s+'_hand_in_body_m',penetration,t)
            feet[s].append([v[sole[s],1].min(),world[names.index('B_'+s+'_Foot'),2,3]])
    for key in list(record):
        if key.endswith('_head_clearance'): record[key]['value']=-record[key]['value']
    record['body_floor_range_m']=[round(min(floors),5),round(max(floors),5)]
    for s in 'LR':
        tw=np.degrees(np.unwrap(twist[s]));record[s+'_wrist_twist_range_deg']=[round(float(tw.min()),3),round(float(tw.max()),3)]
        f=np.array(feet[s]);record[s+'_sole_range_m']=[round(float(f[:,0].min()),5),round(float(f[:,0].max()),5)]
        velocity=np.diff(f[:,1])/np.diff(times);plant=np.maximum(f[:-1,0],f[1:,0])<.035
        record[s+'_stride_m']=round(float(np.median(np.abs(velocity[plant]))*duration),5) if plant.any() else None
    record['pelvis_max_frame_step_m']=round(float(np.linalg.norm(np.diff(pelvis,axis=0),axis=1).max()),5)
    record['passes_stretch_wrist']=all(record[s+'_arm_p99']['value']<=2 and record[s+'_hand_max']['value']<=4.5 and record[s+'_wrist_swing_deg']['value']<=60.01 for s in 'LR')
    report[clip]=record
    print(clip,record['passes_stretch_wrist'],record['body_floor_range_m'],[(s,record[s+'_arm_p99']['value'],record[s+'_hand_max']['value'],record[s+'_wrist_swing_deg']['value']) for s in 'LR'],flush=True)
(P/'review'/args[1]).write_text(json.dumps({'source':args[0],'sample_hz':60,'clips':report},indent=2)+'\n')
sys.stdout.flush();sys.stderr.flush();os._exit(0)
