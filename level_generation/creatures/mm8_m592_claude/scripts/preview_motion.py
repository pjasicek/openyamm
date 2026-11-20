from pathlib import Path
import hashlib,json,math,sys
import bpy
P=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm8_m592_claude')
ROOT=P.parents[2]
sys.path.insert(0,str(P.parent/'mm6_natm_claude/scripts'))
import common
out=P/'review/source_motion';out.mkdir(parents=True,exist_ok=True)
records=[]
sources=[('humanoid_set','anim_library/humanoid_set/Unarmed.glb',['UnarmedAttackR1','UnarmedAttackR3','UnarmedAttackL2'],True),('ogre','level_generation/creatures/mm6_ogr_claude/export/mm6_ogr.glb',['Walking','Running','Death'],False),('devil','assets_source/worlds/mm6/models/mm6_demon.glb',['Attack'],False)]
for label,path,clips,turn in sources:
 bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene;scene.render.fps=30
 src=ROOT/path;bpy.ops.import_scene.gltf(filepath=str(src));rig=next(o for o in scene.objects if o.type=='ARMATURE')
 if turn:rig.rotation_mode='XYZ';rig.rotation_euler.z=math.pi
 if rig.animation_data:
  for tr in rig.animation_data.nla_tracks:tr.mute=True
 common.workbench_clay(scene);bpy.context.view_layer.update()
 acts=list(bpy.data.actions)
 for name in clips:
  matches=[a for a in acts if a.name==name or a.name.endswith('|'+name) or a.name.endswith('_'+name) or a.name.endswith(name)]
  assert matches,(name,[a.name for a in acts]);act=matches[0];rig.animation_data.action=act
  if act.slots:rig.animation_data.action_slot=act.slots[0]
  f0,f1=act.frame_range;motion=[];renders=[]
  for i in range(round(f1-f0)+1):
   f=f0+i;scene.frame_set(int(f),subframe=f%1)
   motion.append({'t':i/30,'joints':{n:list((rig.matrix_world@b.matrix).translation) for n,b in rig.pose.bones.items()}})
  for i in range(5):
   f=f0+(f1-f0)*i/4;scene.frame_set(int(f),subframe=f%1)
   bounds=[o.matrix_world@__import__('mathutils').Vector(v) for o in scene.objects if o.type=='MESH' for v in o.bound_box]
   zmax=max(v.z for v in bounds);zmin=min(v.z for v in bounds);scale=max(zmax-zmin,2.4)
   renders.append(common.render_views(str(out/f'{label}_{name}_{i:02d}'),(zmax+zmin)/2,scale*1.25,views=('front','left','three_quarter'),resolution=(440,440)))
  records.append({'label':label,'source':path,'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'clip':name,'action':act.name,'fps':30,'duration_seconds':(f1-f0)/30,'frames':renders,'motion':motion})
  print('PREVIEW',label,name,(f1-f0)/30,flush=True)
(out/'clips.json').write_text(json.dumps(records,indent=2)+'\n')
assert len(records)==7
