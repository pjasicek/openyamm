"""Roll the round bow grip during aim so the true joined string clears the bow arm."""
import bpy,sys,json,math,runpy
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
def string_rotation(bm,d,name):
 base=bm.to_quaternion()@Quaternion((1,0,0),math.pi if name=='StringTop'else 0)
 return (base@Vector((0,0,1))).rotation_difference(d)@base
selection=json.loads((P/'review/rebake/final_selection.json').read_text())
for level,item in selection.items():
 path=P/f"work/rebake/{item['tag']}_baked.blend";bpy.ops.wm.open_mainfile(filepath=str(path));rig=bpy.data.objects['Rig'];a=bpy.data.actions['Attack'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];sc=bpy.context.scene
 def ease(t):t=max(0,min(1,t));return t*t*(3-2*t)
 records={};nocks={}
 for f in range(36):
  sc.frame_set(f);source_f=f if f<=23 else 23+(f-23)/2 if f<27 else f-2;t=ease(f/12)if f<=23 else 1-ease((source_f-23)/10);rig.pose.bones['Bow'].rotation_quaternion=Quaternion();bpy.context.view_layer.update();rig.pose.bones['B_L_Finger4'].location=Vector();bpy.context.view_layer.update();bm=rig.pose.bones['Bow'].matrix.copy()@Matrix.Rotation(math.radians(-120)*t,4,'Z');rig.pose.bones['Bow'].matrix=bm;bpy.context.view_layer.update()
  finger=rig.pose.bones['B_L_Finger4'];axis=bm.to_3x3().col[2].normalized();radial=finger.head-bm.translation;radial-=axis*radial.dot(axis);fm=finger.matrix.copy();fm.translation-=radial.normalized()*.005*t;finger.matrix=fm;bpy.context.view_layer.update()
  mid=bm@Vector((0,.215,.04));finger=rig.pose.bones['B_R_Finger11'].head.lerp(rig.pose.bones['B_R_Finger12'].head,.55);nock=mid.lerp(finger,max(0,min(1,f-18)))if 18<=f<=22 else mid;nocks[f]=nock.copy()
  for name,z in [('StringTop',.55),('StringBottom',-.55)]:
   b=rig.pose.bones[name];tip=bm@Vector((0,.215,z));d=nock-tip;m=string_rotation(bm,d,name).to_matrix().to_4x4();m.translation=tip;b.matrix=m@Matrix.Scale(d.length,4)@b.bone.matrix_local
  d=Vector((0,-1,0))if f>=23 else bm@Vector((0,-.08,.04))-nock;m=d.to_track_quat('Z','Y').to_matrix().to_4x4();m.translation=nock;b=rig.pose.bones['Arrow'];b.matrix=m@Matrix.Scale(1.22,4)@Matrix.Translation((0,0,.32))@b.bone.matrix_local
  if not 19<=f<23:b.scale*=.001
  bpy.context.view_layer.update();records[float(f)]={n:rig.pose.bones[n].matrix_basis.copy()for n in ['B_L_Finger4','Bow','StringTop','StringBottom','Arrow']}
 for f,row in records.items():
  for name,m in row.items():
   b=rig.pose.bones[name];b.matrix_basis=m
   for channel in ['rotation_quaternion','location','scale']:b.keyframe_insert(channel,frame=f)
 # Subframes share one physical nock. Ease-out puts peak speed at the start of the release.
 for start,i in [(start,i)for start in [18,22]for i in range(1,16)]:
  f=start+i/16;sc.frame_set(start,subframe=i/16);bm=rig.pose.bones['Bow'].matrix;nock=nocks[start].lerp(nocks[start+1],i/16 if start==18 else (i/16)*(2-i/16))
  for name,z in [('StringTop',.55),('StringBottom',-.55)]:
   b=rig.pose.bones[name];tip=bm@Vector((0,.215,z));d=nock-tip;m=string_rotation(bm,d,name).to_matrix().to_4x4();m.translation=tip;b.matrix=m@Matrix.Scale(d.length,4)@b.bone.matrix_local;bpy.context.view_layer.update()
   for channel in ['rotation_quaternion','location','scale']:b.keyframe_insert(channel,frame=f)
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for name in ['Bow','Arrow','StringTop','StringBottom']:
     cs=sorted([c for c in bag.fcurves if c.data_path==f'pose.bones["{name}"].rotation_quaternion'],key=lambda c:c.array_index);prev=None
     for k in range(len(cs[0].keyframe_points)):
      q=[c.keyframe_points[k].co.y for c in cs]
      if prev is not None and sum(x*y for x,y in zip(q,prev))<0:q=[-x for x in q]
      for c,v in zip(cs,q):c.keyframe_points[k].co.y=v
      prev=q
    for c in bag.fcurves:
     for k in c.keyframe_points:k.interpolation='LINEAR'
     c.update()
 if 'Cast'in bpy.data.actions:bpy.data.actions.remove(bpy.data.actions['Cast'])
 c=a.copy();c.name='Cast';c.use_fake_user=True;rig.animation_data.action=None;bpy.ops.wm.save_as_mainfile(filepath=str(path))
 if level=='0':
  result=runpy.run_path(str(P/'scripts/equipment_gate.py'),run_name='__main__',init_globals={'GATE_BLEND':path});assert max(v['depth_m']for x in result['report'].values()for v in x['contacts'].values())<=.002
print('STRING_AUTHORING_COMPLETE',flush=True)
