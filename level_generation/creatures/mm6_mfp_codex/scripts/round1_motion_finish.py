"""Keep the palms' world poses while sharing pronation between forearm and wrist."""
import bpy,sys,math,numpy as np,json
from pathlib import Path
from mathutils import Quaternion,Matrix,Vector
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as G
for level in range(4):
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/round1/lod{level}.blend'));r=bpy.data.objects['Rig'];sc=bpy.context.scene;rest={n:b.matrix_local.copy()for n,b in r.data.bones.items()};names=[f'B_{s}_{n}'for s in 'LR'for n in ['UpperArm','Forearm','Hand','ForearmTwist']]
 for a in bpy.data.actions:
  if a.name not in ['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']:continue
  r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];end=float(a.frame_range[1]);times=np.linspace(0,end,round(end*48/30)+1);rows=[]
  for f in times:
   sc.frame_set(int(f),subframe=f%1)
   for s in 'LR':
    fn,hn=f'B_{s}_Forearm',f'B_{s}_Hand';fa=r.pose.bones[fn];hand=r.pose.bones[hn];H=hand.matrix.copy();Rrest=rest[hn].to_3x3();axis=(sum((rest[f'B_{s}_Finger{i}'].translation for i in range(5)),Vector())/5-rest[hn].translation).normalized();axisLocal=Rrest.inverted()@axis;neutral=fa.matrix.to_3x3()@rest[fn].to_3x3().inverted()@Rrest;rel=neutral.inverted()@H.to_3x3();_,roll=G.swing_twist(np.array(rel),np.array(axisLocal));excess=float(roll-np.clip(roll,-40,40))
    if abs(excess)>.01:
     M=fa.matrix.copy();worldAxis=(H.translation-M.translation).normalized();rot=Quaternion(worldAxis,math.radians(excess)).to_matrix();M=(rot@M.to_3x3()).to_4x4();M.translation=fa.matrix.translation;fa.matrix=M;bpy.context.view_layer.update();hand.matrix=H;bpy.context.view_layer.update()
    axisFa=(rest[fn].inverted()@rest[hn].translation).normalized();r.pose.bones[f'B_{s}_ForearmTwist'].rotation_quaternion=Quaternion(axisFa,math.radians(float(np.clip(roll,-40,40))*.6))
   bpy.context.view_layer.update();rows.append({n:r.pose.bones[n].rotation_quaternion.copy()for n in names})
  # Average neighbouring orientations to remove the retiming corner, without moving the root or feet.
  if a.name in ['Attack','Hit']:
   raw=rows;rows=[];sigma=.075 if a.name=='Attack'else .065
   for i,f in enumerate(times):
    row={};dt=(times-f)/30;indices=np.flatnonzero(abs(dt)<sigma*3);weights=np.exp(-.5*(dt[indices]/sigma)**2)
    for n in names:
     ref=raw[i][n];vec=sum((np.array(raw[j][n])*(1 if ref.dot(raw[j][n])>=0 else -1)*w for j,w in zip(indices,weights)),np.zeros(4));row[n]=Quaternion(vec/np.linalg.norm(vec))
    rows.append(row)
  for layer in a.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for fc in list(bag.fcurves):
      if any(fc.data_path==f'pose.bones["{n}"].rotation_quaternion'for n in names):bag.fcurves.remove(fc)
  for f,row in zip(times,rows):
   for n,q in row.items():r.pose.bones[n].rotation_quaternion=q;r.pose.bones[n].keyframe_insert('rotation_quaternion',frame=f)
  for layer in a.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for fc in bag.fcurves:
      for key in fc.keyframe_points:key.interpolation='LINEAR'
  a.use_fake_user=True
 r.animation_data.action=bpy.data.actions['Standing'];r.animation_data.action_slot=r.animation_data.action.slots[0];sc.frame_set(0);bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/round1/lod{level}.blend'));print('WRIST_REDISTRIBUTED',level,flush=True)
