"""Level planted feet, fit garment follow-through, and run the pilot's numerical deformation checks."""
from pathlib import Path
import bpy,sys,runpy,os,math,ast,json,numpy as np
from mathutils import Vector,Quaternion,Matrix
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
def run(name,args):
 s=p/'scripts'/name;sys.argv=[str(s),'--']+[str(x) for x in args];runpy.run_path(str(s),run_name='__main__')
acts=['Standing','Walking','Running','Attack']
run('foot_level.py',[p/'work/pilots_authored.blend',p/'work/pilots_feet.blend','Standing','Walking:const','Running:const','Attack'])
bpy.ops.wm.open_mainfile(filepath=str(p/'work/pilots_feet.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene;names=[b.name for b in rig.data.bones]
tree=ast.parse((p/'scripts/author_pilots.py').read_text())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'set_act','sample','apply','current','write'}],type_ignores=[]),'pilot_helpers','exec'),globals())
pv=np.array([x.value for x in body.data.attributes['piece'].data]);foot_ids=np.where(np.isin(pv,[3,4]))[0]
cape_axes={n:rig.data.bones[n].matrix_local.to_3x3().inverted()@Vector((1,0,0)) for n in ['Cape0','Cape1','Cape2','LoinFront']}
restangles={s:math.atan2(-(rig.data.bones[f'B_{s}_Calf'].head_local-rig.data.bones[f'B_{s}_Thigh'].head_local).y,-(rig.data.bones[f'B_{s}_Calf'].head_local-rig.data.bones[f'B_{s}_Thigh'].head_local).z) for s in 'LR'}
pelrest=rig.data.bones['B_Pelvis'].matrix_local
report={}
for name in acts:
 act=bpy.data.actions[name];poses=[sample(act,f) for f in range(int(act.frame_range[1])+1)];low=[]
 for pose in poses:
  apply(pose);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh()
  low.append(min(m.vertices[i].co.z for i in foot_ids));ev.to_mesh_clear()
 # Keep the run's airborne phase; other pilots have a continuously grounded support foot.
 if name=='Running':
  shift=np.maximum(0,-np.array(low));held=np.array([shift[max(0,i-1):i+2].max() for i in range(len(shift))]);shift=np.maximum(shift,np.convolve(np.pad(held,1,mode='edge'),[.25,.5,.25],mode='valid'))
 else:shift=-np.array(low)
 for f,pose in enumerate(poses):
  apply(pose);root=rig.pose.bones['B_Pelvis'];m=root.matrix.copy();m.translation.z+=float(shift[f]);root.matrix=m;bpy.context.view_layer.update()
  phase=2*math.pi*f/(len(poses)-1);motion=1 if name=='Running' else .55 if name=='Walking' else .10
  for k in range(3):
   base=([18,12,8] if name=='Running' else [8,5,3] if name=='Walking' else [4,3,1])[k]
   angle=base+motion*3*math.sin(phase-k*.6)
   if name=='Attack':angle+=3*math.sin(math.pi*f/(len(poses)-1))**2
   rig.pose.bones[f'Cape{k}'].rotation_quaternion=Quaternion(cape_axes[f'Cape{k}'],math.radians(angle))
  undo=(rig.pose.bones['B_Pelvis'].matrix@pelrest.inverted()).inverted().to_3x3();angles=[]
  for s in 'LR':
   d=undo@(rig.pose.bones[f'B_{s}_Calf'].head-rig.pose.bones[f'B_{s}_Thigh'].head);angles.append(math.atan2(-d.y,-d.z)-restangles[s])
  rig.pose.bones['LoinFront'].rotation_quaternion=Quaternion(cape_axes['LoinFront'],-max(0,*angles)*1.20-math.radians(12))
  poses[f]=current()
 if name!='Attack':poses[-1]=poses[0]
 write(name,poses);report[name]={'floor_shift_m':[float(shift.min()),float(shift.max())]}
set_act(None)
for pb in rig.pose.bones:pb.matrix_basis.identity()
output=p/'work/pilots_fitted.blend';bpy.ops.wm.save_as_mainfile(filepath=str(output))
(p/'review/pilot_floor.json').write_text(json.dumps(report,indent=2)+'\n')
common.workbench_clay(scene)
for name in acts:
 set_act(bpy.data.actions[name]);n=int(bpy.data.actions[name].frame_range[1])
 for f in sorted(set([0,round(n*.25),round(n*.5),round(n*.75),n])):
  scene.frame_set(f);common.render_views(str(p/f'review/pilots_fitted/{name}_{f:03d}'),.86,2.1,views=('front','left','back'),resolution=(380,500))
os.environ['STEP']='0.5'
run('sole_probe.py',[output,*acts])
run('g5_hand_stretch.py',[output,*acts])
run('g4_weights.py',[output,'pilot','Standing:0','Walking:12','Running:12','Attack:12','Attack:23','Attack:33'])
run('jerk_probe.py',[output,*acts])
