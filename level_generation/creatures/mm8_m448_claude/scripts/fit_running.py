from pathlib import Path
import bpy,sys,math,json
import numpy as np
from mathutils import Vector,Matrix
p=Path(__file__).resolve().parents[1]
# Reuse the pose sampling/writing routines; this prefix only opens the input and defines helpers.
code=(p/'scripts/finalize_motion.py').read_text().split('stand=sample')[0].replace('work/motion_level.blend','work/motion_final.blend')
exec(compile(code,str(p/'scripts/finalize_motion.py'),'exec'))
a=bpy.data.actions['Running'];nf=int(a.frame_range[1]);poses=[sample(a,f) for f in range(nf+1)];targets=[];hip=[]
for pose in poses:
    apply(pose);hip.append(rig.pose.bones['B_Pelvis'].head.z)
    targets.append({side:{name:rig.pose.bones['B_'+side+'_'+name].matrix.copy() for name in ('Thigh','Calf','Foot')} for side in ('L','R')})
low=float(np.percentile(hip,35));out=[];miss=[]
for f,pose in enumerate(poses):
    apply(pose);pel=rig.pose.bones['B_Pelvis'];m=pel.matrix.copy()
    m.translation.z=low+.025*(1-math.cos(4*math.pi*f/nf));pel.matrix=m;bpy.context.view_layer.update()
    for side in ('L','R'):
        th,ca,ft=[rig.pose.bones['B_'+side+'_'+n] for n in ('Thigh','Calf','Foot')]
        H,K,A=[b.head.copy() for b in (th,ca,ft)];target=targets[f][side]['Foot'].translation.copy()
        l1,l2=(K-H).length,(A-K).length;d=target-H;reach=min(d.length,(l1+l2)*.999);u=d.normalized()
        old=targets[f][side];oldH,oldK,oldA=[old[n].translation for n in ('Thigh','Calf','Foot')]
        oldAxis=(oldA-oldH).normalized();pole=(oldK-oldH)-oldAxis*(oldK-oldH).dot(oldAxis);pole=oldAxis.rotation_difference(u)@pole
        v=(pole-u*pole.dot(u)).normalized();c=max(-1,min(1,(l1*l1+reach*reach-l2*l2)/(2*l1*reach)))
        knee=H+l1*(u*c+v*math.sqrt(max(0,1-c*c)))
        for parent,child,tgt in ((th,ca,knee),(ca,ft,H+u*reach)):
            m=parent.matrix.copy();q=(child.head-parent.head).normalized().rotation_difference((tgt-parent.head).normalized())
            nr=(q.to_matrix()@m.to_3x3()).to_4x4();nr.translation=m.translation;parent.matrix=nr;bpy.context.view_layer.update()
        m=old['Foot'].copy();m.translation=ft.head;ft.matrix=m;bpy.context.view_layer.update()
        miss.append((ft.head-target).length)
    out.append({n:(rig.pose.bones[n].rotation_quaternion.copy(),rig.pose.bones[n].location.copy()) for n in names})
out[-1]=out[0];write('Running',out)
(p/'work/running_fit.json').write_text(json.dumps({'old_hip_range': [min(hip),max(hip)],'new_hip_range':[low,low+.05],'max_ankle_miss_m':max(miss)},indent=2))
print('RUNNING_FIT',min(hip),max(hip),'to',low,low+.05,'max ankle miss',max(miss))
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/motion_final.blend'))
