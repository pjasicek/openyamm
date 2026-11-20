"""Refine the fitted cylindrical grip against the actual irregular bone shaft."""
from pathlib import Path
import bpy,bmesh,json,math,numpy as np
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/authored.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];club=bpy.data.objects['Club'];me=body.data
act=bpy.data.actions['Standing'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];bpy.context.scene.frame_set(0)
snap={pb.name:pb.matrix_basis.copy() for pb in rig.pose.bones};rig.animation_data.action=None
for n,m in snap.items():rig.pose.bones[n].matrix_basis=m
bpy.context.view_layer.update()
ev=club.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();tree=BVHTree.FromPolygons([club.matrix_world@v.co for v in mesh.vertices],[list(f.vertices) for f in mesh.polygons]);ev.to_mesh_clear()
G=json.loads((p/'work/grip_pose.json').read_text());axis=(rig.pose.bones['B_R_Hand'].matrix.to_3x3()@Vector(G['handle_axis_hand_local'])).normalized()
D=Vector((.313,.719,.621)).normalized()
def inside(point):
    origin=point+D*.00001;hits=0
    for _ in range(50):
        loc,n,idx,dist=tree.ray_cast(origin,D,3)
        if loc is None:break
        hits+=1;origin=loc+D*.00002
    return hits%2==1
names=[g.name for g in body.vertex_groups]
report={}
for digit,label in [(0,1),(1,2),(2,3),(4,5)]:
    ids=[v.index for v in me.vertices if v.co.x<0 and me.attributes['finger'].data[v.index].value==label]
    verts=np.array([list(me.vertices[i].co)+[1] for i in ids]);groups={names[g.group] for i in ids for g in me.vertices[i].groups if g.weight>1e-6}
    weights={n:np.array([sum(g.weight for g in me.vertices[i].groups if names[g.group]==n) for i in ids]) for n in groups}
    inv={n:rig.data.bones[n].matrix_local.inverted() for n in groups}
    chain=[f'B_R_Finger{digit}',f'B_R_Finger{digit}1',f'B_R_Finger{digit}2'] if digit else ['B_R_Finger0','B_R_Finger0.001','B_R_Finger0.002']
    def surface():
        out=np.zeros((len(ids),3))
        for n in groups:out+=(verts@np.array(rig.pose.bones[n].matrix@inv[n]).T)[:,:3]*weights[n][:,None]
        return out
    def measure():
        distances=[];depth=[]
        for point in surface():
            v=Vector(point);loc,n,idx,d=tree.find_nearest(v)
            interior=(v-loc).dot(n)<0 and inside(v)
            distances.append(d);depth.append(d if interior else 0)
        return np.array(distances),np.array(depth)
    def score():
        distances,depth=measure()
        return 2000*float(np.square(np.maximum(depth-.0003,0)).sum())+float(np.min(distances))**2
    def turn(n,ax,angle):
        pb=rig.pose.bones[n];m=pb.matrix.copy();rotation=Matrix.Rotation(angle,3,ax)@m.to_3x3();nm=rotation.to_4x4();nm.translation=m.translation;pb.matrix=nm;pb.location=(0,0,0);bpy.context.view_layer.update()
    before=measure();axes=[(n,axis) for n in chain]
    if digit==0:
        f=(rig.pose.bones['B_R_Finger2'].head-rig.pose.bones['B_R_Hand'].head).normalized();axes += [(chain[0],f),(chain[0],axis.cross(f).normalized())]
    for deg in (6,3,1):
        for _ in range(5):
            changed=False
            for n,ax in axes:
                q0=rig.pose.bones[n].rotation_quaternion.copy();best=(score(),q0)
                for sign in (-1,1):
                    rig.pose.bones[n].rotation_quaternion=q0;bpy.context.view_layer.update();turn(n,ax,math.radians(deg)*sign)
                    val=score()
                    if val<best[0]-1e-10:best=(val,rig.pose.bones[n].rotation_quaternion.copy())
                rig.pose.bones[n].rotation_quaternion=best[1];bpy.context.view_layer.update();changed|=q0.rotation_difference(best[1]).angle>.0001
            if not changed:break
    after=measure();report[str(digit)]={'before_gap_m':float(before[0].min()),'before_penetration_m':float(before[1].max()),'gap_m':float(after[0].min()),'penetration_m':float(after[1].max())}
    for n in chain:G['finger_local'][n]=list(rig.pose.bones[n].rotation_quaternion)
    print('REFINED GRIP',digit,report[str(digit)],flush=True)
G['actual_mesh_refinement']=report;(p/'work/grip_pose.json').write_text(json.dumps(G,indent=2))
for act in [a for a in bpy.data.actions if a.use_fake_user]:
    rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
    for n,q in G['finger_local'].items():
        pb=rig.pose.bones[n]
        for f in range(int(act.frame_range[1])+1):
            pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f)
(p/'review/actual_grip_refinement.json').write_text(json.dumps(report,indent=2))
rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];bpy.context.scene.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/authored.blend'))
