"""One globally fitted ready pose from the approved walking grip, then the library's idle torso motion."""
import bpy,sys,math,json
from pathlib import Path
from mathutils import Vector,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=str(P/'work/lancer_review2.blend'))
r=bpy.data.objects['Rig'];r.animation_data_create();sc=bpy.context.scene
act=bpy.data.actions['Carbine_Walking'];r.animation_data.action=act;r.animation_data.action_slot=act.slots[0];sc.frame_set(0)
roots=[r.data.bones[f'B_{s}_Clavicle'] for s in 'LR']
names={b.name for root in roots for b in [root,*root.children_recursive]}
reference={n:r.pose.bones[n].matrix_basis.copy() for n in names}
gun=armik.W(r,'Rifle').copy(); hand={s:gun.inverted() @ armik.W(r,f'B_{s}_Hand') for s in 'LR'}
act=bpy.data.actions['Carbine_Standing'];r.animation_data.action=act;r.animation_data.action_slot=act.slots[0];sc.frame_set(0)
r.animation_data.action=None
for n,m in reference.items():r.pose.bones[n].matrix_basis=m
bpy.context.view_layer.update()
base={n:r.pose.bones[n].matrix_basis.copy() for n in names}
left_centre=Vector(json.loads((P/'work/grip_pose_L_tun.json').read_text())['handle_centre_hand_local'])
direction=Vector((.75,-.65,.12)).normalized()
Q=gun.to_3x3().col[1].rotation_difference(direction)
rotation=Q.to_matrix() @ gun.to_3x3()
global_best=None
for roll in [-30]:
 for x in [-.22]:
  for z in [1.06]:
    M=(Quaternion(direction,math.radians(roll)).to_matrix() @ rotation).to_4x4();M.translation=Vector((x,-.46,z))
    chosen={};records={};total=.03*abs(roll)+20*abs(x+.02)+10*abs(z-1.06)
    for side in 'RL':
        bn=[f'B_{side}_{part}' for part in ('UpperArm','Forearm','Hand')]
        target0=M @ hand[side]
        best=None
        for hand_roll in (range(-120,121,10) if side=='L' else [0]):
            target=target0.copy()
            if side=='L':
                centre=target0 @ left_centre
                target=(Quaternion(direction,math.radians(hand_roll)).to_matrix() @ target0.to_3x3()).to_4x4()
                target.translation=centre-target.to_3x3() @ left_centre
            for angle in range(-120,121,15):
                for n in bn:r.pose.bones[n].matrix_basis=base[n]
                bpy.context.view_layer.update()
                shoulder=armik.W(r,bn[0]).translation.copy();elbow=armik.W(r,bn[1]).translation.copy()
                axis=(target.translation-shoulder).normalized()
                pole=shoulder+Quaternion(axis,math.radians(angle)) @ (elbow-shoulder)
                reach=armik.solve(r,side,target.translation,pole,target.to_3x3().normalized())
                swing,twist=armik.wrist_cost(r,side,target.to_3x3().normalized())
                cost=swing+.15*abs(twist)+.1*abs(angle)+1000*max(0,swing-53)+1000*max(0,abs(twist)-160)+10000*max(0,reach-.97)
                el=armik.W(r,bn[1]).translation; sign=1 if side=='L' else -1
                cost+=5000*max(0,.38-sign*el.x)+300*abs(el.y+.12)+300*abs(el.z-1.12)
                if side=='L':cost+=10000*max(0,el.y+.25)+300*abs(el.z-1.02)+.1*abs(hand_roll)
                if best is None or cost<best[0]:best=(cost,{n:r.pose.bones[n].matrix_basis.copy() for n in bn},swing,twist,reach,angle)
        chosen.update(best[1]);records[side]=list(best[2:]);total+=best[0]
    if global_best is None or total<global_best[0]:global_best=(total,chosen,records,roll,x,z)
print('READY_FIT',global_best[2:],flush=True)
assert all(row[0]<60 and row[2]<1 for row in global_best[2].values()),global_best[2:]
for n,m in base.items():r.pose.bones[n].matrix_basis=m
for n,m in global_best[1].items():r.pose.bones[n].matrix_basis=m
records=global_best[2]
carry={n:r.pose.bones[n].matrix_basis.copy() for n in names}
for name in ['Carbine_Standing','Carbine_Fidget']:
    act=bpy.data.actions[name];r.animation_data.action=act;r.animation_data.action_slot=act.slots[0]
    for frame in range(int(act.frame_range[0]),int(act.frame_range[1])+1):
        sc.frame_set(frame)
        for n,m in carry.items():
            b=r.pose.bones[n];b.matrix_basis=m;b.keyframe_insert('rotation_quaternion',frame=frame);b.keyframe_insert('location',frame=frame)
r.animation_data.action=None
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/lancer_review2.blend'))
(P/'review/ready_fit.json').write_text(json.dumps(records,indent=2)+'\n')
