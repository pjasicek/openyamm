import bpy,sys,math,json
import numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_final_motion.blend'));r=bpy.data.objects['Rig'];a=bpy.data.actions['Attack'];sc=bpy.context.scene
G={s:json.loads((P/f'work/grip_pose{"" if s=="R" else "_L"}.json').read_text()) for s in 'RL'};C={s:Vector(G[s]['handle_centre_hand_local']) for s in 'RL'};A={s:Vector(G[s]['handle_axis_hand_local']) for s in 'RL'}
def restore(p):
 for n,m in p.items():r.pose.bones[n].matrix_basis=m
 bpy.context.view_layer.update()
def costs(s):
 fb,hb=r.data.bones[f'B_{s}_Forearm'],r.data.bones[f'B_{s}_Hand'];fr=r.pose.bones[fb.name].matrix.to_3x3()@fb.matrix_local.to_3x3().inverted();hr=r.pose.bones[hb.name].matrix.to_3x3()@hb.matrix_local.to_3x3().inverted();rel=(fr.inverted()@hr).to_quaternion();sw,tw=armik.split_swing_twist(rel,(hb.head_local-fb.head_local).normalized());return math.degrees(min(sw.angle,2*math.pi-sw.angle)),math.degrees(tw)
report={}
for f in range(16,24):
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc.frame_set(f);p={b.name:b.matrix_basis.copy() for b in r.pose.bones};hr=r.pose.bones['B_R_Hand'].matrix.copy();hl=r.pose.bones['B_L_Hand'].matrix.copy();axis=(hr.translation-r.pose.bones['B_R_Forearm'].head).normalized();rc=hr@C['R'];r.animation_data.action=None;results=[]
 for angle in range(-30,31,5):
  restore(p);rot=Quaternion(axis,math.radians(angle)).to_matrix()@hr.to_3x3().normalized();rw=rc-rot@C['R'];reachR=armik.solve(r,'R',rw,hand_rot=rot);rs,rt=costs('R');d=rot@A['R'];lc=rc-d*(.115+.03*math.sin(math.pi*f/a.frame_range[1])**2);base=(hl.to_3x3()@A['L']).rotation_difference(d).to_matrix()@hl.to_3x3().normalized();lp={b.name:b.matrix_basis.copy() for b in r.pose.bones};sh=r.pose.bones['B_L_UpperArm'].head.copy();el=r.pose.bones['B_L_Forearm'].head.copy();u=(hl.translation-sh).normalized();pole=(el-sh)-u*(el-sh).dot(u);best=None
  for phi in range(-90,91,15):
   for roll in range(-90,91,15):
    restore(lp);rotL=Quaternion(d,math.radians(roll)).to_matrix()@base;reach=armik.solve(r,'L',lc-rotL@C['L'],pole=sh+Quaternion(u,math.radians(phi))@pole,hand_rot=rotL);ls,lt=costs('L');cost=1000*max(0,ls-60)**2+100*max(0,abs(lt)-90)**2+1e7*max(0,reach-.999)**2+ls+.3*abs(lt)+.2*abs(phi)+.2*abs(roll)
    if best is None or cost<best[0]:best=(cost,ls,lt,phi,roll,reach)
  results.append({'angle':angle,'R':[rs,rt,reachR],'L':list(best[1:]),'score':best[0]+1000*max(0,rs-60)**2+100*max(0,abs(rt)-90)**2+1e7*max(0,reachR-.999)**2+abs(angle)})
 report[f]=sorted(results,key=lambda x:x['score']);print('WRIST',f,report[f][:3],flush=True)
(P/'work/wrist_axis_probe.json').write_text(json.dumps(report,indent=1))
