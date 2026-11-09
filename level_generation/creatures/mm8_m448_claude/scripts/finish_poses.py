"""Seat the rear sole in idle and nearby planted poses using fixed-length leg IK."""
from pathlib import Path
import bpy,math,json
from mathutils import Vector
p=Path(__file__).resolve().parents[1]
code=(p/'scripts/finalize_motion.py').read_text().split('stand=sample')[0].replace('work/motion_level.blend','work/rig_textured_uv.blend')
exec(compile(code,str(p/'scripts/finalize_motion.py'),'exec'))
vg=[g.name for g in body.vertex_groups]
foot={side:np.array([sum(e.weight for e in v.groups if vg[e.group]==f'B_{side}_Foot')>.5 for v in body.data.vertices]) for side in ('L','R')}
report={}
for name in ('Standing','Attack','Hit','Fidget','Death'):
 a=bpy.data.actions[name];poses=[sample(a,f) for f in range(int(a.frame_range[1])+1)];out=[];moves=[]
 for f,pose in enumerate(poses):
  apply(pose);co=points();low={s:float(co[m,2].min()) for s,m in foot.items()}
  for side in ('L','R'):
   h=low[side]
   if name=='Death' and f>6:continue
   if h<=0 or h>=.07:continue
   # Full planting below 4 cm, smoothly released before the foot is lifted 7 cm.
   shift=h*(1-smooth((h-.04)/.03))
   th,ca,ft=[rig.pose.bones[f'B_{side}_'+n] for n in ('Thigh','Calf','Foot')]
   H,K,A=[b.head.copy() for b in (th,ca,ft)];old=ft.matrix.copy();target=A-Vector((0,0,shift))
   l1,l2=(K-H).length,(A-K).length;d=target-H;reach=min(d.length,(l1+l2)*.999);u=d.normalized()
   oldaxis=(A-H).normalized();pole=oldaxis.rotation_difference(u)@((K-H)-oldaxis*(K-H).dot(oldaxis))
   v=(pole-u*pole.dot(u)).normalized();c=max(-1,min(1,(l1*l1+reach*reach-l2*l2)/(2*l1*reach)))
   knee=H+l1*(u*c+v*math.sqrt(max(0,1-c*c)))
   for parent,child,tgt in ((th,ca,knee),(ca,ft,H+u*reach)):
    m=parent.matrix.copy();q=(child.head-parent.head).normalized().rotation_difference((tgt-parent.head).normalized())
    nr=(q.to_matrix()@m.to_3x3()).to_4x4();nr.translation=m.translation;parent.matrix=nr;bpy.context.view_layer.update()
   old.translation=ft.head;ft.matrix=old;bpy.context.view_layer.update();moves.append(shift)
  out.append({n:(rig.pose.bones[n].rotation_quaternion.copy(),rig.pose.bones[n].location.copy()) for n in names})
 write(name,out);report[name]={'max_sole_lowering_m':max(moves,default=0)}
last=sample(bpy.data.actions['Death'],bpy.data.actions['Death'].frame_range[1]);write('Dead',[last,last])
set_act(None)
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_finished.blend'))
(p/'work/sole_fit.json').write_text(json.dumps(report,indent=2));print('SOLE_FIT',report)
