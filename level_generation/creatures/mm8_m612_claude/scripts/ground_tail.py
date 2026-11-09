"""Ground the posed mesh and bake a flexible, floor-clearing tail in every clip."""
import bpy,json,math,sys
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P/'scripts'))
import armik
bpy.ops.wm.open_mainfile(filepath=str(P/'work/animated_feet.blend'))
sc=bpy.context.scene;rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data
names=[g.name for g in body.vertex_groups]
feet=np.array([sum(e.weight for e in v.groups if 'Foot' in names[e.group] or 'Toe0' in names[e.group])>.5 for v in me.vertices])
tail=np.array([sum(e.weight for e in v.groups if names[e.group].startswith('Tail'))>.1 for v in me.vertices])
path=np.array(json.loads((P/'work/cleanup.json').read_text())['tail_path'])
def set_act(a):
    rig.animation_data_create();rig.animation_data.action=a
    if a is not None and len(a.slots):rig.animation_data.action_slot=a.slots[0]
def mesh():
    ob=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ob.to_mesh()
    co=np.array([tuple(body.matrix_world@v.co) for v in m.vertices]);ob.to_mesh_clear();return co
report={}
for a in list(bpy.data.actions):
    if not a.use_fake_user:continue
    n=int(a.frame_range[1]);poses=[]
    for f in np.arange(0,n+.01,.5):
        for pb in rig.pose.bones:pb.scale=(1,1,1)
        set_act(a);sc.frame_set(int(f),subframe=float(f-int(f)))
        snap={pb.name:pb.matrix_basis.copy() for pb in rig.pose.bones}
        set_act(None)
        for pb in rig.pose.bones:pb.matrix_basis=snap[pb.name]
        bpy.context.view_layer.update()
        # The tail follows the body; it must not lift a falling corpse above the ground.
        co=mesh();low=float(co[~tail if a.name=='Death' else feet,2].min())
        m=armik.W(rig,'B_Pelvis');m.translation.z-=min(low,0) if a.name=='Running' else low
        armik.set_world(rig,'B_Pelvis',m)
        # Preserve segment lengths while laying the distal tail above the floor.
        pelvis=armik.W(rig,'B_Pelvis')
        forward=pelvis.to_3x3()@rig.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted()@Vector((0,-1,0))
        yaw=math.atan2(forward.x,-forward.y)
        for i in range(len(path)-1):
            name=f'Tail{i:02}';m=armik.W(rig,name);origin=m.translation.copy()
            d=Vector(path[i+1]-path[i]);length=d.length
            wave=math.radians(3)*math.sin(2*math.pi*f/max(n,1)-i*.28)*min(1,i/3)
            d=Matrix.Rotation(yaw+wave,3,'Z')@d
            # Radius margin covers the thickest tail section at this station.
            radius=.055 if i<6 else .045
            d.z=max(d.z,radius-origin.z)
            d.z=min(d.z,length*.95)
            horizontal=math.sqrt(max(0,length*length-d.z*d.z))
            xy=Vector((d.x,d.y,0)).normalized()*horizontal
            d.x,d.y=xy.x,xy.y
            rest=rig.data.bones[name].matrix_local.to_3x3().normalized()
            current=rest@Vector((0,1,0))
            rotation=current.normalized().rotation_difference(d.normalized()).to_matrix()@rest
            m=rotation.to_4x4();m.translation=origin
            armik.set_world(rig,name,m)
            pb=rig.pose.bones[name];pb.scale=(1,1,1);pb.location=(0,0,0)
            bpy.context.view_layer.update()
        check=mesh();assert np.isfinite(check).all() and np.abs(check).max()<10,(a.name,f)
        poses.append({pb.name:(pb.rotation_quaternion.copy(),pb.location.copy()) for pb in rig.pose.bones})
    set_act(a);previous={}
    for f,pose in zip(np.arange(0,n+.01,.5),poses):
        for name,(q,l) in pose.items():
            pb=rig.pose.bones[name]
            if name in previous and q.dot(previous[name])<0:q=-q
            previous[name]=q.copy();pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.location=l
            pb.keyframe_insert('rotation_quaternion',frame=f)
            if name=='B_Pelvis':pb.keyframe_insert('location',frame=f)
    lows=[]
    for f in np.arange(0,n+.01,.5):
        sc.frame_set(int(f),subframe=float(f-int(f)));co=mesh()
        lows.append([float(co[feet,2].min()),float(co[tail,2].min()),float(co[:,2].min())])
    report[a.name]={'seconds':n/30,'min_xyz':[min(x[i] for x in lows) for i in range(3)],'max_low_sole':max(x[0] for x in lows)}
    print('GROUNDED',a.name,report[a.name])
set_act(None)
for pb in rig.pose.bones:pb.matrix_basis=Matrix()
(P/'work/ground_report.json').write_text(json.dumps(report,indent=2,allow_nan=False))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/animated_grounded.blend'))
