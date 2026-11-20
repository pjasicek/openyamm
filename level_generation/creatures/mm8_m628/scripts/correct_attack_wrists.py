"""Keep the draw and bow grip while limiting wrist bend in anatomical palm space."""
import bpy,json,math,sys
from pathlib import Path
from mathutils import Vector,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_uv.blend'))
rig=bpy.data.objects['Rig'];scene=bpy.context.scene;act=bpy.data.actions['Attack']
def action(a):
    rig.animation_data.action=a
    if a and len(a.slots):rig.animation_data.action_slot=a.slots[0]
frames=[i/4 for i in range(int(act.frame_range[1]*4)+1)]
poses=[]
for f in frames:
    action(act);scene.frame_set(int(f),subframe=f%1)
    poses.append({b.name:b.matrix_basis.copy()for b in rig.pose.bones})
report=[];keys=[]
for f,pose in zip(frames,poses):
    action(None)
    for n,m in pose.items():rig.pose.bones[n].matrix_basis=m
    bpy.context.view_layer.update();row={'frame':f};out={}
    for side in 'LR':
        hand=rig.pose.bones[f'B_{side}_Hand'];wrist=hand.head.copy()
        fore=(wrist-rig.pose.bones[f'B_{side}_Forearm'].head).normalized()
        palm=(sum((rig.pose.bones[f'B_{side}_Finger{i}'].head for i in range(1,5)),Vector())/4-wrist).normalized()
        bend=math.degrees(fore.angle(palm));limit=40 if side=='R' else 45
        target=bend if bend<=limit else limit+10*math.tanh((bend-limit)/10)
        correction=Quaternion().slerp(palm.rotation_difference(fore),max(0,(bend-target)/max(bend,1e-6)))
        m=(correction.to_matrix()@hand.matrix.to_3x3()).to_4x4();m.translation=wrist;hand.matrix=m
        bpy.context.view_layer.update();out[hand.name]=hand.rotation_quaternion.copy()
        row[side]={'before':bend,'after':target}
    keys.append(out);report.append(row)
action(act)
for f,row in zip(frames,keys):
    for n,q in row.items():
        b=rig.pose.bones[n];b.rotation_quaternion=q;b.keyframe_insert('rotation_quaternion',frame=f)
action(None)
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_uv.blend'))
(P/'work/attack_wrist_correction.json').write_text(json.dumps(report,indent=2)+'\n')
common.workbench_clay(scene)
for f in [22,25,27.5,29.375,33]:
    action(act);scene.frame_set(int(f),subframe=f%1)
    common.render_views(str(P/f'review/wrist_corrected_{f}'),1.25,1.2,views=('front','left','three_quarter'),resolution=(700,700))
