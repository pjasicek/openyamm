"""Dense surface/arm gate, with contact candidates retained for visual review."""
import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
import armik
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_gated_candidate.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];dagger=bpy.data.objects['DaggerMesh'];me=body.data
names=[g.name for g in body.vertex_groups];nv=len(me.vertices)
rest=np.array([tuple(v.co) for v in me.vertices]);weights=np.zeros((nv,len(names)))
for v in me.vertices:
    for g in v.groups:weights[v.index,g.group]=g.weight
pv=np.zeros(nv,np.int32);me.attributes['piece'].data.foreach_get('value',pv)
faces=[tuple(p.vertices) for p in me.polygons]
arm={s:weights[:,[i for i,n in enumerate(names) if n.startswith(f'B_{s}_') and any(x in n for x in ('Clavicle','UpperArm','Forearm','Hand','Finger'))]].sum(1)>.2 for s in 'LR'}
arm['L'] |= np.isin(pv,[3,7,12,13])
arm['R'] |= np.isin(pv,[4,8,11,14])
hand={s:pv==(3 if s=='L' else 4) for s in 'LR'}
forearm={s:weights[:,[i for i,n in enumerate(names) if n.startswith(f'B_{s}_Forearm')]].sum(1)>.5 for s in 'LR'}
otherfaces={s:[fc for fc in faces if all(not arm[s][i] for i in fc) and (pv[fc[0]] in (3,4) or (pv[fc[0]]==0 and min(rest[i,2] for i in fc)>1.44))] for s in 'LR'}
shellfaces={s:[fc for fc in faces if all(not arm[s][i] for i in fc) and fc not in otherfaces[s]] for s in 'LR'}
E=np.array([tuple(e.vertices) for e in me.edges]);rl=np.linalg.norm(rest[E[:,0]]-rest[E[:,1]],axis=1)
def evaluated(ob):
    ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
    p=np.array([tuple(ob.matrix_world@v.co) for v in mesh.vertices]);ev.to_mesh_clear();return p
report={}
for an in ('Standing','Walking','Running','Hit','Death','Fidget'):
    a=bpy.data.actions[an];rig.animation_data.action=a
    if len(a.slots):rig.animation_data.action_slot=a.slots[0]
    contacts={};wrist={s:[] for s in 'LR'};stretch={s:(0,0,0,0) for s in 'LR'};minZ=1
    for f in np.arange(0,float(a.frame_range[1])+.01,.5):
        bpy.context.scene.frame_set(int(f),subframe=float(f-int(f)));pos=evaluated(body);dp=evaluated(dagger);minZ=min(minZ,float(pos[:,2].min()))
        for s in 'LR':
            sw,tw=armik.wrist_cost(rig,s,armik.W(rig,f'B_{s}_Hand').to_3x3().normalized());wrist[s].append((float(f),sw,tw))
            tree=BVHTree.FromPolygons(pos.tolist(),otherfaces[s])
            shell=BVHTree.FromPolygons(pos.tolist(),shellfaces[s])
            samples={f'{s}_hand':pos[hand[s]],f'{s}_forearm':pos[forearm[s]]}
            if s=='R':
                dm=rig.matrix_world@rig.pose.bones['Dagger'].matrix
                samples['dagger']=np.vstack([dp,np.array([tuple(dm@Vector((0,t,0))) for t in np.linspace(-.067,.325,40)])])
            for label,pts in samples.items():
                worst=0.;point=None
                for p in pts:
                    loc,norm,fi,dist=tree.find_nearest(Vector(p),.10)
                    if loc is not None and dist>worst and (Vector(p)-loc).dot(norm)<-.7*dist:
                        worst=dist;point=p.tolist()
                close=sum(shell.find_nearest(Vector(p),.002)[0] is not None for p in pts)
                if close>contacts.get(label+'_shell',{}).get('vertices',0):contacts[label+'_shell']={'vertices':close,'frame':float(f)}
                if worst>contacts.get(label,{}).get('depth_m',0):contacts[label]={'depth_m':worst,'frame':float(f),'point':point}
            edge=(hand[s][E[:,0]]&hand[s][E[:,1]])
            ids=np.flatnonzero(edge); ratios=np.linalg.norm(pos[E[ids,0]]-pos[E[ids,1]],axis=1)/np.maximum(rl[ids],1e-8)
            j=int(np.argmax(ratios));eid=ids[j]
            if ratios[j]>stretch[s][0]:stretch[s]=(float(ratios[j]),float(f),float(rl[eid]*1000),float((ratios[j]-1)*rl[eid]*1000))
    report[an]={'contacts':contacts,'hand_stretch_ratio_frame_rest_mm_extension_mm':stretch,'minimum_surface_z_m':minZ,
      'wrist':{s:{'swing_max':max(x[1] for x in wrist[s]),'twist_range':[min(x[2] for x in wrist[s]),max(x[2] for x in wrist[s])],
        'twist_step_max':float(np.max(np.abs(np.diff(np.degrees(np.unwrap(np.radians([x[2] for x in wrist[s]])))))))} for s in 'LR'}}
    print('MOTIONGATE',an,json.dumps(report[an]),flush=True)
(P/'work/all_motion_gate.json').write_text(json.dumps(report,indent=2)+'\n')
