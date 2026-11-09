"""Half-frame deformation, wrist, floor and full staff contacts on the fitted Cleric."""
import bpy,sys,json,math,os,runpy,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import armik
args=sys.argv[sys.argv.index('--')+1:];source=args[0];tag=args[1]
blend=p/f'work/{source}.blend';bpy.ops.wm.open_mainfile(filepath=str(blend))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];staff=bpy.data.objects['Staff'];me=body.data;sc=bpy.context.scene
P0=np.array([v.co[:] for v in me.vertices]);pv=np.array([a.value for a in me.attributes['piece'].data]);names=[g.name for g in body.vertex_groups]
W=np.zeros((len(P0),len(names)))
for v in me.vertices:
    for g in v.groups:W[v.index,g.group]=g.weight
def mask(side,parts,threshold):
    ids=[i for i,n in enumerate(names) if n.startswith(f'B_{side}_') and any(t in n for t in parts)]
    return W[:,ids].sum(1)>threshold
arm={s:mask(s,['Clavicle','UpperArm','Forearm','Hand','Finger'],.2) for s in 'LR'}
sample={s:mask(s,['Forearm','Hand','Finger'],.5) for s in 'LR'}
armstretch={s:mask(s,['UpperArm','Forearm'],.3)&(pv==0) for s in 'LR'}
foot={s:mask(s,['Foot','Toe'],.5) for s in 'LR'}
faces=[tuple(f.vertices) for f in me.polygons];skinfaces=[f for f in faces if all(pv[i] in [0,3,4] for i in f)]
bodyfaces={s:[f for f in skinfaces if not any(arm[s][i] for i in f)] for s in 'LR'}
edges=np.array([e.vertices[:] for e in me.edges]);length=np.linalg.norm(P0[edges[:,0]]-P0[edges[:,1]],axis=1)
edgeflags={s:(armstretch[s][edges[:,0]]&armstretch[s][edges[:,1]]) for s in 'LR'}
handflags={s:np.all(pv[edges]==(3 if s=='L' else 4),axis=1) for s in 'LR'}
def coords(ob):
    ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();v=np.array([tuple(ob.matrix_world@x.co) for x in m.vertices]);ev.to_mesh_clear();return v
def depth(tree,points):
    best=0;point=None
    for pt in points:
        loc,n,face,d=tree.find_nearest(Vector(pt),.06)
        if loc is not None and d>best and (Vector(pt)-loc).dot(n)<-.7*d:best=d;point=pt.tolist()
    return best,point
report={'method':'Every half-frame; signed nearest skin surface excludes the sampled arm. Open-surface boundary cases need visual adjudication.','clips':{}}
for role in (args[2:] or ['Standing','Walking','Attack','Cast','Hit','Death','Dead','Fidget']):
    rig.animation_data.action=None
    for pb in rig.pose.bones:pb.matrix_basis.identity()
    a=bpy.data.actions[role];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];worst={};soles=[];floors=[];tw={s:[] for s in 'LR'};points=[]
    def record(key,value,f,**extra):
        if value>worst.get(key,{}).get('value',-1):worst[key]={'value':float(value),'frame':float(f),**extra}
    for f in np.arange(0,a.frame_range[1]+.001,.5):
        sc.frame_set(int(f),subframe=float(f-int(f)));P=coords(body);Q=coords(staff);assert np.isfinite(P).all() and np.isfinite(Q).all()
        stretch=np.linalg.norm(P[edges[:,0]]-P[edges[:,1]],axis=1)/np.maximum(length,1e-6)
        for side in 'LR':
            record(side+'_arm_p99',np.percentile(stretch[edgeflags[side]],99),f)
            record(side+'_hand_max',max(stretch[handflags[side]]),f)
            sw,t=armik.wrist_cost(rig,side,armik.W(rig,f'B_{side}_Hand').to_3x3());record(side+'_wrist_swing',sw,f);tw[side].append(t)
            tree=BVHTree.FromPolygons(P.tolist(),bodyfaces[side]);d,pt=depth(tree,P[sample[side]]);record(side+'_arm_contact',d,f,point=pt)
            if side=='R':
                # Include every triangle centroid so a crossing of the long shaft cannot hide between its rings.
                qf=np.array([Q[list(face.vertices)].mean(0) for face in staff.data.polygons]);d,pt=depth(tree,np.vstack([Q,qf]));record('staff_contact',d,f,point=pt)
        tree=BVHTree.FromPolygons(P.tolist(),skinfaces);d,pt=depth(tree,P[np.isin(pv,[2,5,12,13,14,15,16])]);record('robe_skin',d,f,point=pt)
        soles.append([float(P[foot[s],2].min()) for s in 'LR']);floors.append([float(P[:,2].min()),float(Q[:,2].min())])
        points.append(list(armik.W(rig,'Socket_Staff_Head').translation))
    for side in 'LR':
        values=np.degrees(np.unwrap(np.radians(tw[side])));worst[side+'_wrist_twist_range']=[float(values.min()),float(values.max())]
    sole=np.array(soles);floor=np.array(floors);worst['grounded_sole_range_m']=[float(sole.min(1).min()),float(sole.min(1).max())];worst['body_floor_min_m']=float(floor[:,0].min());worst['staff_floor_min_m']=float(floor[:,1].min())
    report['clips'][role]=worst;print('CHECK',role,json.dumps(worst),flush=True)
    if role in ['Attack','Cast']:report[role+'_staff_head_60hz']=points
(p/f'review/{tag}_motion_checks.json').write_text(json.dumps(report,indent=2)+'\n')
for name,rest in [('g4_weights.py',[blend,tag,'Standing:0','Walking:6','Attack:20','Attack:29','Hit:5','Death:15','Death:35']),('jerk_probe.py',[blend,'Standing','Walking','Attack','Cast','Hit','Death','Fidget'])]:
    s=p/'scripts'/name;sys.argv=[str(s),'--']+[str(v) for v in rest];runpy.run_path(str(s),run_name='__main__')
