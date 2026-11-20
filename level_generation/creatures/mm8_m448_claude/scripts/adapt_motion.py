from pathlib import Path
import bpy,sys,json,math
import numpy as np
from mathutils import Vector,Quaternion,Matrix
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/motion_twist.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
co=np.array([tuple(v.co) for v in body.data.vertices]);pid=np.array([v.value for v in body.data.attributes['piece'].data])
tail=(pid==0)&(co[:,1]>.12)&(co[:,2]<.94)
assert 100<int(tail.sum())<1500
ys=np.linspace(.12,co[tail,1].max(),9);pts=[]
for i,y in enumerate(ys):
    band=co[tail & (abs(co[:,1]-y)<.055)]
    assert len(band)>0
    pts.append(Vector((float(np.median(band[:,0])),float(y),float(np.median(band[:,2])))))
pts[0]=Vector((0,.12,.90))
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for i in range(8):
    b=rig.data.edit_bones.new('Tail'+str(i));b.head=pts[i];b.tail=pts[i+1]
    b.parent=rig.data.edit_bones['B_Pelvis' if i==0 else 'Tail'+str(i-1)]
    b.use_deform=True
bpy.ops.object.mode_set(mode='OBJECT')
groups={g.name:g for g in body.vertex_groups}
for i in range(8):groups['Tail'+str(i)]=body.vertex_groups.new(name='Tail'+str(i))
def set_weights(vi,weights):
    for g in body.vertex_groups:g.remove([int(vi)])
    for name,w in weights.items():
        if w>1e-6:groups[name].add([int(vi)],float(w),'REPLACE')
for vi in np.where(tail)[0]:
    t=np.interp(co[vi,1],ys,np.arange(9));i=min(int(t),7);f=min(t-i,1)
    if i==0:weights={'B_Pelvis':1-f,'Tail0':f}
    else:weights={'Tail'+str(i-1):1-f,'Tail'+str(i):f}
    set_weights(vi,weights)
# The pouch follows the belt; incisors stay rigidly attached to the skull.
for vi in np.where((pid==3)|(pid==201))[0]:set_weights(vi,{'B_Pelvis' if pid[vi]==3 else 'B_Head':1})
# Rat claws are rigid with each foot, without a human toe curl.
for side in ('L','R'):
    toe=groups['B_'+side+'_Toe0'];foot=groups['B_'+side+'_Foot']
    for v in body.data.vertices:
        w=sum(e.weight for e in v.groups if e.group==toe.index)
        if w:foot.add([v.index],w,'ADD');toe.remove([v.index])
report={}
for act in [a for a in bpy.data.actions if a.use_fake_user]:
    rig.animation_data.action=act
    if len(act.slots):rig.animation_data.action_slot=act.slots[0]
    f0,f1=map(int,act.frame_range);max_bend=0;max_fix=0
    for f in range(f0,f1+1):
        bpy.context.scene.frame_set(f)
        for side in ('L','R'):
            hand=rig.pose.bones['B_'+side+'_Hand'];fore=rig.pose.bones['B_'+side+'_Forearm'];kn=rig.pose.bones['B_'+side+'_Finger2']
            fa=(hand.head-fore.head).normalized();ha=(kn.head-hand.head).normalized();ang=ha.angle(fa)
            max_bend=max(max_bend,math.degrees(ang))
            if ang>math.radians(58):
                correction=Quaternion().slerp(ha.rotation_difference(fa),(ang-math.radians(58))/ang)
                m=hand.matrix.copy();m3=correction.to_matrix()@m.to_3x3();new=m3.to_4x4();new.translation=m.translation
                hand.matrix=new;hand.keyframe_insert('rotation_quaternion',frame=f)
                max_fix=max(max_fix,math.degrees(ang)-58)
                bpy.context.view_layer.update()
        phase=(f-f0)/max(1,f1-f0)*2*math.pi
        amp={'Walking':.10,'Running':.14,'Attack':.07,'Hit':.06,'Fidget':.06,'Standing':.035,'Death':0}[act.name]
        for i in range(8):
            b=rig.pose.bones['Tail'+str(i)];b.rotation_mode='QUATERNION'
            b.rotation_quaternion=Quaternion((0,0,1),amp*math.sin(phase-i*.45))
            b.keyframe_insert('rotation_quaternion',frame=f)
    report[act.name]={'original_max_wrist_bend_deg':max_bend,'max_correction_deg':max_fix}
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
(p/'work/motion_adaptation.json').write_text(json.dumps({'tail_points':[list(x) for x in pts],'tail_vertices':int(tail.sum()),'wrists':report},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/motion_adapted.blend'))
print('ADAPT',report)
