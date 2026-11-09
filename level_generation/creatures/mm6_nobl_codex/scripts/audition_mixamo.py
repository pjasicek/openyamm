"""Non-production motion auditions on the selected Swordsman; retain v14 and installed exports."""
import bpy, json, math, os, sys
from pathlib import Path
from mathutils import Matrix, Vector, Quaternion
P=Path(__file__).resolve().parents[1]
OUT=P/'review/animation_alternatives_20261011'
LIB=Path('/home/pjasicek/Downloads/mixamo_library')
sys.path.insert(0,str(P/'scripts'))
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v14.blend'))
scene=bpy.context.scene;rig=bpy.data.objects['Rig']
OFF=json.loads(scene['rig_offsets'])
canonical={n:Matrix(v['R_src']) for n,v in OFF.items()}
mapping={'B_Pelvis':'Hips','B_Spine':'Spine','B_Spine1':'Spine1','B_Spine2':'Spine2','B_Neck':'Neck','B_Head':'Head'}
for s,side in [('L','Left'),('R','Right')]:
 for t,src in [('Clavicle','Shoulder'),('UpperArm','Arm'),('Forearm','ForeArm'),('Hand','Hand'),('Thigh','UpLeg'),('Calf','Leg'),('Foot','Foot'),('Toe0','ToeBase')]:
  mapping[f'B_{s}_{t}']=side+src
def bind(obj,act):
 obj.animation_data_create();obj.animation_data.action=act
 if act.slots: obj.animation_data.action_slot=act.slots[0]
def curves(act):
 return [fc for layer in act.layers for strip in layer.strips for cb in strip.channelbags for fc in cb.fcurves]
bind(rig,bpy.data.actions['Standing']);scene.frame_set(0)
standing={pb.name:pb.matrix.copy() for pb in rig.pose.bones}
basis={pb.name:pb.matrix_basis.copy() for pb in rig.pose.bones}
base_names=('Standing','Running','Attack','Hit')
for a in list(bpy.data.actions):
 if a.name not in base_names:bpy.data.actions.remove(a)
CANDIDATES=[
 ('Run_A_Weighted','Running (5).fbx','run'),
 ('Run_B_Jog','Jog Forward.fbx','run'),
 ('Run_C_Brisk','Running (3).fbx','run'),
 ('Attack_A_Inward','Stable Sword Inward Slash.fbx','attack'),
 ('Attack_B_Outward','Stable Sword Outward Slash.fbx','attack'),
 ('Attack_C_Overhead','Standing Melee Attack Downward.fbx','attack'),
 ('Hit_A_Quick','Hit Reaction (4).fbx','hit'),
 ('Hit_B_Light','Light Hit To Head (2).fbx','hit')]
report={}
def twist_angle(q,axis):
 a=2*math.atan2(Vector((q.x,q.y,q.z)).dot(axis),q.w)
 return (a+math.pi)%(2*math.pi)-math.pi
for name,file,role in CANDIDATES:
 oldobjs=set(bpy.data.objects);oldacts=set(bpy.data.actions)
 bpy.ops.import_scene.fbx(filepath=str(LIB/file))
 newobjs=set(bpy.data.objects)-oldobjs
 src=next(o for o in newobjs if o.type=='ARMATURE')
 source_action=src.animation_data.action
 sourcefps=scene.render.fps/scene.render.fps_base
 f0,f1=source_action.frame_range
 duration=(f1-f0)/sourcefps
 sb={b.name.split(':')[-1]:b for b in src.pose.bones}
 names=[b.name for b in rig.data.bones if b.name in mapping and mapping[b.name] in sb]
 SR={n:(src.matrix_world@sb[mapping[n]].bone.matrix_local).to_3x3().normalized() for n in names}
 def delta(n):return (src.matrix_world@sb[mapping[n]].matrix).to_3x3().normalized()@SR[n].inverted()
 scene.frame_set(int(f0),subframe=f0-int(f0))
 first={n:delta(n) for n in names}
 hp0=(src.matrix_world@sb['Hips'].matrix).translation
 resthip=(src.matrix_world@sb['Hips'].bone.head_local).z
 scale=rig.data.bones['B_Pelvis'].head_local.z/resthip
 act=bpy.data.actions.new(name);act.use_fake_user=True
 bind(rig,act)
 # Extra cloth, grip, fingers and solved attachment start from the accepted standing pose.
 for pb in rig.pose.bones:
  pb.matrix_basis=basis[pb.name]
  pb.rotation_mode='QUATERNION'
  for prop in ('location','rotation_quaternion','scale'):pb.keyframe_insert(prop,frame=0)
 count=round(duration*30)
 for i in range(count+1):
  f=f0+(f1-f0)*i/count
  scene.frame_set(int(f),subframe=f-int(f))
  bind(rig,act)
  for n in names:
   if role!='run' and any(k in n for k in ('Thigh','Calf','Foot','Toe0','Pelvis')):continue
   R=delta(n)@canonical[n]
   if role!='run' and (role=='hit' or n in ('B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head','B_L_Clavicle','B_R_Clavicle')):
    R=delta(n)@first[n].inverted()@standing[n].to_3x3()
   M=R.to_4x4();pb=rig.pose.bones[n]
   M.translation=rig.matrix_world@pb.head
   if n=='B_Pelvis':
    pos=(src.matrix_world@sb['Hips'].matrix).translation
    M.translation=standing[n].translation+Vector(((pos.x-hp0.x)*scale,0,(pos.z-hp0.z)*scale))
   pb.matrix=rig.matrix_world.inverted()@M;bpy.context.view_layer.update()
   pb.keyframe_insert('rotation_quaternion',frame=i)
   if n=='B_Pelvis':pb.keyframe_insert('location',frame=i)
  # Match the fitted source-frame twist helpers without changing vertex weights.
  for s in ('L','R'):
   fb=rig.data.bones[f'B_{s}_Forearm'];hb=rig.data.bones[f'B_{s}_Hand']
   axis=(fb.matrix_local.inverted()@hb.head_local).normalized()
   rel=(rig.pose.bones[fb.name].matrix.inverted()@rig.pose.bones[hb.name].matrix).to_quaternion()
   rest=(fb.matrix_local.inverted()@hb.matrix_local).to_quaternion()
   tw=max(-math.pi/4,min(math.pi/4,twist_angle(rel@rest.inverted(),axis)*.5))
   pb=rig.pose.bones[f'B_{s}_ForearmTwist'];pb.rotation_quaternion=Quaternion(axis,tw);pb.keyframe_insert('rotation_quaternion',frame=i)
   ub=rig.data.bones[f'B_{s}_UpperArm'];ax=(ub.matrix_local.inverted()@fb.head_local).normalized()
   tw=max(-math.pi/4,min(math.pi/4,-.5*twist_angle(rig.pose.bones[ub.name].matrix_basis.to_quaternion(),ax)))
   pb=rig.pose.bones[f'B_{s}_UpperArmTwist'];pb.rotation_quaternion=Quaternion(ax,tw);pb.keyframe_insert('rotation_quaternion',frame=i)
  if role=='run':
   bpy.context.view_layer.update()
   deps=bpy.context.evaluated_depsgraph_get()
   body=bpy.data.objects['Body'];ev=body.evaluated_get(deps);mesh=ev.to_mesh()
   # Audition-only root height; final selection still needs per-foot stance/cloth baking.
   z=min((body.matrix_world@v.co).z for v in mesh.vertices if v.co.z<.4)
   ev.to_mesh_clear()
   pb=rig.pose.bones['B_Pelvis'];M=pb.matrix.copy();M.translation.z+=.001-z;pb.matrix=M
   pb.keyframe_insert('location',frame=i)
  bpy.context.view_layer.update()
 act.use_frame_range=True;act.frame_start=0;act.frame_end=count
 for fc in curves(act):
  for key in fc.keyframe_points:key.interpolation='LINEAR'
 report[name]={'file':file,'role':role,'source_fps':sourcefps,'source_duration':duration,'duration':count/30,
               'adaptation':'Standing legs and relative recoil' if role=='hit' else 'Standing legs and upright chest baseline' if role=='attack' else 'Canonical rest-frame conversion; provisional root floor'}
 rig.animation_data.action=None
 for o in newobjs:bpy.data.objects.remove(o,do_unlink=True)
 for a in set(bpy.data.actions)-oldacts-{act}:bpy.data.actions.remove(a)
 print('AUDITION',name,report[name],flush=True)
scene.render.fps=30;scene.render.fps_base=1
bind(rig,bpy.data.actions['Standing']);scene.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'auditions.blend'))
(OUT/'auditions.json').write_text(json.dumps(report,indent=2))
# Reuse the established exporter in memory, directing every output into this review folder.
code=(P/'scripts/export_runtime.py').read_text()
code=code.replace("os.path.join(HERE, 'work', 'rig_v14.blend')",repr(str(OUT/'auditions.blend')))
start=code.index("death = bpy.data.actions['Death']")
end=code.index("rig.animation_data.action = None",start)
code=code[:start]+code[end:]
code=code.replace("KEEP = ('Standing', 'Walking', 'Running', 'Attack', 'Hit', 'Death', 'Dead', 'Fidget')","KEEP = "+repr(tuple(base_names)+tuple(report)))
code=code.replace("os.path.join(HERE, 'export'","os.path.join("+repr(str(OUT)))
code=code.replace("os.path.join(HERE,'export','mm6_nobl.blend')",repr(str(OUT/'auditions_export.blend')))
assert "os.path.join(HERE, 'export'" not in code and 'rig_v14.blend' not in code.split('bpy.ops.wm.open_mainfile')[1].split('\n')[0]
exec(compile(code,str(P/'scripts/export_runtime.py'),'exec'),{'__file__':str(P/'scripts/export_runtime.py'),'__name__':'__main__'})
