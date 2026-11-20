"""Replace rejected clips with local source motion; preserve fitted rig, retained clips and skin weights."""
from pathlib import Path
import bpy, sys, os, json, runpy, ast, math
from mathutils import Vector, Quaternion, Matrix
p=Path(__file__).resolve().parents[1];scripts=p/'scripts';sys.path.insert(0,str(scripts))
roles=json.loads((p/'revision_02/motion/selection.json').read_text())
items=[str(p.parents[2]/roles[n]['file'])+':'+roles[n]['clip']+':'+n for n in ['Standing','Running','Fidget','Death']]
os.environ['ARM_ABDUCT_DEG']='10'
sys.argv=['retarget.py','--',str(p/'work/rig_v7.blend'),str(p/'work/rig_v8.blend'),*items]
runpy.run_path(str(scripts/'retarget.py'),run_name='__main__')
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene
selected=[bpy.data.actions[n] for n in ['Standing','Running','Fidget','Death']]
# Reuse the proven twist bake without recreating bones or reassigning weights.
tree=ast.parse((scripts/'twist_bones.py').read_text());functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['twist_about','bake_twist']]
exec(compile(ast.Module(body=functions,type_ignores=[]),str(scripts/'twist_bones.py'),'exec'),globals())
FA=.5;UA=.5
G=json.loads((p/'work/grip_pose.json').read_text())['finger_local']
G.update({b.name:[1,0,0,0] for b in rig.data.bones if b.name.startswith('B_L_Finger')})
pelrest=rig.data.bones['B_Pelvis'].matrix_local
axes={n:(rig.data.bones[n].matrix_local.to_3x3().inverted()@Vector((1,0,0))).normalized() for n in ['LoinFront','LoinBack']}
restangles={}
for side in 'LR':
 d=rig.data.bones[f'B_{side}_Calf'].head_local-rig.data.bones[f'B_{side}_Thigh'].head_local
 restangles[side]=math.atan2(-d.y,-d.z)
report={}
for act in selected:
 rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
 for f in range(int(act.frame_range[0]),int(act.frame_range[1])+1):
  scene.frame_set(f)
  for n,q in G.items():
   pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=Quaternion(q);pb.keyframe_insert('rotation_quaternion',frame=f)
  undo=(rig.pose.bones['B_Pelvis'].matrix@pelrest.inverted()).inverted().to_3x3()
  angles=[]
  for side in 'LR':
   d=undo@(rig.pose.bones[f'B_{side}_Calf'].head-rig.pose.bones[f'B_{side}_Thigh'].head)
   angles.append(math.atan2(-d.y,-d.z)-restangles[side])
  for name,angle in [('LoinFront',-max(0,*angles)*1.12-math.radians(8)),('LoinBack',-min(0,*angles)*1.12+math.radians(8))]:
   pb=rig.pose.bones[name];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=Quaternion(axes[name],angle);pb.keyframe_insert('rotation_quaternion',frame=f)
 bake_twist(act)
 rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
 # Source loops are effectively closed; report before any endpoint correction.
 scene.frame_set(int(act.frame_range[0]));start={b.name:(b.rotation_quaternion.copy(),b.location.copy()) for b in rig.pose.bones}
 scene.frame_set(int(act.frame_range[1]));end={b.name:(b.rotation_quaternion.copy(),b.location.copy()) for b in rig.pose.bones}
 report[act.name]={'duration':float(act.frame_range[1]-act.frame_range[0])/30,'loop_rotation_deg':max(math.degrees(min(q.rotation_difference(end[n][0]).angle,2*math.pi-q.rotation_difference(end[n][0]).angle)) for n,(q,l) in start.items()),'loop_translation_m':max((l-end[n][1]).length for n,(q,l) in start.items())}
 if act.name in ['Standing','Running']:
  assert report[act.name]['loop_rotation_deg']<1.0,report[act.name]
  assert report[act.name]['loop_translation_m']<.01,report[act.name]
  last=int(act.frame_range[1]);rows=[]
  for f in range(last-4,last+1):
   scene.frame_set(f);u=(f-last+4)/4;u=u*u*(3-2*u)
   rows.append((f,{n:(pb.rotation_quaternion.slerp((q@end[n][0].inverted())@pb.rotation_quaternion,u),pb.location+(l-end[n][1])*u) for n,(q,l) in start.items() for pb in [rig.pose.bones[n]]}))
  for f,pose in rows:
   for n,(q,l) in pose.items():
    pb=rig.pose.bones[n];pb.rotation_quaternion=q;pb.location=l
    pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f)
# The corpse is the library death's last pose, with no separate choreography.
rig.animation_data.action=bpy.data.actions['Death'];rig.animation_data.action_slot=bpy.data.actions['Death'].slots[0]
scene.frame_set(int(bpy.data.actions['Death'].frame_range[1]));held={b.name:(b.rotation_quaternion.copy(),b.location.copy()) for b in rig.pose.bones}
bpy.data.actions.remove(bpy.data.actions['Dead']);dead=bpy.data.actions.new('Dead');dead.use_fake_user=True;rig.animation_data.action=dead
for f in [0,30]:
 for n,(q,l) in held.items():
  pb=rig.pose.bones[n];pb.rotation_quaternion=q;pb.location=l;pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f)
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
(p/'revision_02/motion/retarget.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_v8.blend'))
print('REVIEW2_MOTION',report)
for view in ['front','left','three_quarter']:
 out=p/'revision_02/motion'/('ogre_'+view)
 sys.argv=['clip_sheet.py','--',str(p/'work/rig_v8.blend'),str(out),view,'7','Standing','Running','Fidget','Death']
 runpy.run_path(str(scripts/'clip_sheet.py'),run_name='__main__')
