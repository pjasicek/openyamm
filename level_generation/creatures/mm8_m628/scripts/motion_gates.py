"""Measure delivered weights, rigid bone lengths, glove deformation, floor contact and bow/string contacts."""
import bpy,json,math,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'export/m628_master.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;scene=bpy.context.scene
piece=np.array([x.value for x in me.attributes['piece'].data]);rest=np.array([tuple(v.co)for v in me.vertices])
edges=np.array([tuple(e.vertices)for e in me.edges]);length=np.linalg.norm(rest[edges[:,1]]-rest[edges[:,0]],axis=1)
good=length>.001;edges=edges[good];length=length[good];ep=piece[edges[:,0]]
same=piece[edges[:,0]]==piece[edges[:,1]]
single=np.array([v.groups[0].group if len(v.groups)==1 else -1 for v in me.vertices])
rigid=same&(single[edges[:,0]]>=0)&(single[edges[:,0]]==single[edges[:,1]])&(ep<4000)
hand=same&((ep==5)|((ep>=3000)&(ep<4000)));arm=same&(ep==9)
gn={g.index:g.name for g in body.vertex_groups}
foot=np.array([v.index for v in me.vertices if sum(g.weight for g in v.groups
    if gn[g.group]in ['B_L_Foot','B_R_Foot','B_L_Toe0','B_R_Toe0'])>.7])
bone_names=[b.name for b in rig.data.bones if b.name.startswith('B_')]
assert max(len(v.groups)for v in me.vertices)<=4
assert all(abs(sum(g.weight for g in v.groups)-1)<1e-4 for v in me.vertices)
tips=[Vector(v)for v in json.loads(scene['bow_local'])['tips']]
string_ids={pid:np.where(piece==pid)[0]for pid in [4001,4002]}
report={};findings=[]
for act in bpy.data.actions:
    rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
    r={'rigid_edge_error':0.,'hand_p99':0.,'hand_max':0.,'glove_arm_p99':0.,'floor_min':1e9,
       'floor_max':-1e9,'string_tip_error':0.,'string_join_error':0.,'samples':0}
    for f in np.arange(0,float(act.frame_range[1])+.01,.5):
        scene.frame_set(int(f),subframe=float(f%1));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh()
        co=np.empty(len(m.vertices)*3);m.vertices.foreach_get('co',co);ev.to_mesh_clear();co=co.reshape(-1,3)
        assert np.isfinite(co).all()
        ratio=np.linalg.norm(co[edges[:,1]]-co[edges[:,0]],axis=1)/length
        r['rigid_edge_error']=max(r['rigid_edge_error'],float(abs(ratio[rigid]-1).max()))
        r['hand_p99']=max(r['hand_p99'],float(np.percentile(ratio[hand],99)))
        r['hand_max']=max(r['hand_max'],float(ratio[hand].max()))
        r['glove_arm_p99']=max(r['glove_arm_p99'],float(np.percentile(ratio[arm],99)))
        ids=np.where(piece<4000)[0]if act.name in ['Death','Dead']else foot
        floor=float(co[ids,2].min());r['floor_min']=min(r['floor_min'],floor);r['floor_max']=max(r['floor_max'],floor)
        for n in bone_names:
            assert max(abs(v-1)for v in rig.pose.bones[n].scale)<1e-4,(act.name,n,'body scale')
        ends=[]
        bm=rig.pose.bones['Bow'].matrix
        posed_tips=[rig.pose.bones[n].matrix@rig.data.bones[n].matrix_local.inverted()@rig.data.bones['Bow'].matrix_local@v
            for n,v in zip(json.loads(scene['bow_tip_bones']),tips)]
        for pid,tip in zip([4001,4002],posed_tips):
            ids=string_ids[pid];start=co[ids[rest[ids,2]<.1]].mean(0);end=co[ids[rest[ids,2]>.9]].mean(0)
            r['string_tip_error']=max(r['string_tip_error'],float(np.linalg.norm(start-np.array(tip))))
            ends.append(end)
        r['string_join_error']=max(r['string_join_error'],float(np.linalg.norm(ends[0]-ends[1])))
        r['samples']+=1
    for key,limit in [('rigid_edge_error',.01),('hand_p99',4.5),('glove_arm_p99',2.),('string_tip_error',.002),('string_join_error',.002)]:
        if r[key]>limit:findings.append({'clip':act.name,'metric':key,'value':r[key],'limit':limit})
    if r['floor_min']<-.02 or r['floor_max']>.02:findings.append({'clip':act.name,'metric':'floor','value':[r['floor_min'],r['floor_max']]})
    report[act.name]=r
result={'clips':report,'findings':findings,'maximum_influences':max(len(v.groups)for v in me.vertices),
        'limitations':'Prop/body penetration and finger silhouette still require the retained visual and surface contact review.'}
(P/'work/motion_gates.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
common.workbench_clay(scene);a=bpy.data.actions['Attack'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];scene.frame_set(25)
for side in 'LR':
    center=rig.pose.bones[f'B_{side}_Hand'].head
    common.render_views(str(P/f'review/hand_{side}'),center.z,.30,views=('front','left','three_quarter'),
        resolution=(500,500),target=(center.x,center.y))
assert not findings,'Measured motion gates have findings; inspect work/motion_gates.json'
