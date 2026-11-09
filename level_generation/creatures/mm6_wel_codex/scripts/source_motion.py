"""Preview owned upper-body sources before fitting the hybrid rig."""
import bpy,sys,json,math
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parent/'mm6_bar1_claude/scripts'))
import common
dump={};rows=[];rest={}
for file,clips in [('1Hand',['SpearAttackR1','SpearAttackR3','SpearAttackR4']),('Unarmed',['UnarmedGetHitF2'])]:
 bpy.ops.wm.read_factory_settings(use_empty=True)
 bpy.context.scene.render.fps=30
 bpy.ops.import_scene.gltf(filepath=str(P.parents[2]/'anim_library/humanoid_set'/f'{file}.glb'))
 rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
 rig.rotation_mode='XYZ';rig.rotation_euler=(0,0,math.pi);bpy.context.view_layer.update()
 scene=bpy.context.scene;scene.render.fps=30;common.workbench_clay(scene)
 acts=list(bpy.data.actions)
 for name in clips:
  found=[a for a in acts if a.name.endswith(name)]
  if not found:raise ValueError((name,[a.name for a in acts]))
  act=found[0];rig.animation_data.action=act
  if hasattr(act,'slots') and act.slots:rig.animation_data.action_slot=act.slots[0]
  f0,f1=act.frame_range;keys=[]
  for f in range(int(f0),int(f1)+1):
   scene.frame_set(f);keys.append({n:{'q':list((rig.matrix_world@b.matrix).to_quaternion()),'p':list((rig.matrix_world@b.matrix).translation)} for n,b in rig.pose.bones.items() if n.startswith('B_')})
  dump[name]={'fps':30,'keys':keys,'duration':(f1-f0)/30}
  for view in ['front','left']:
   row=[]
   for i in range(5):
    f=f0+(f1-f0)*i/4;scene.frame_set(int(f),subframe=f%1)
    path=common.render_views(str(P/'review'/f'source_{name}_{i}'),1.25,2.9,views=(view,),resolution=(240,360))[0];row.append([path,f'{name} {f:.1f}'])
   rows.append(row)
 rig.animation_data.action=None
 for b in rig.pose.bones:b.matrix_basis.identity()
 if not rest:
  for b in rig.data.bones:
   if not b.name.startswith('B_'):continue
   m=rig.matrix_world@b.matrix_local
   children=[x for x in b.children if x.name.startswith('B_')]
   child=next((x for x in children if 'Finger' not in x.name),children[0] if children else None)
   seg=rig.matrix_world.to_3x3()@(child.head_local-b.head_local) if child else None
   rest[b.name]={'parent':b.parent.name if b.parent else None,'head':list(m.translation),'rot':[list(r) for r in m.to_3x3().normalized()],'child':child.name if child else None,'seg':list(seg) if seg else None}
(P/'work/source_motion.json').write_text(json.dumps(dump))
(P/'review/source_motion_frames.json').write_text(json.dumps(rows))
(P/'work/source_rest.json').write_text(json.dumps(rest,indent=2))
rom={}
for clip,data in dump.items():
 rom[clip]={n:{'min':np.min([k[n]['p'] for k in data['keys']],axis=0).tolist(),'max':np.max([k[n]['p'] for k in data['keys']],axis=0).tolist()} for n in data['keys'][0]}
(P/'work/rom.json').write_text(json.dumps(rom,indent=2))
print('SOURCE_MOTION',[(n,v['duration']) for n,v in dump.items()])
