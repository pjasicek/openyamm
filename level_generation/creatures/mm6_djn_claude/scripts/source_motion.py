"""Review and retain owned upper-body casting motion before modelling."""
import bpy,sys,json,math
from pathlib import Path
from mathutils import Matrix,Vector
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parent/'mm6_bar1_claude/scripts'))
import common
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.render.fps=30
bpy.ops.import_scene.gltf(filepath=str(P.parents[2]/'anim_library/humanoid_set/Unarmed.glb'))
rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
rig.rotation_mode='XYZ';rig.rotation_euler=(0,0,math.pi);bpy.context.view_layer.update()
for o in bpy.context.scene.objects:
 if o.type=='MESH' and o.parent!=rig:o.hide_render=True
scene=bpy.context.scene;scene.render.fps=30;common.workbench_clay(scene)
clips=['UnarmedCastDualAttack2','UnarmedCastDualAOE2','UnarmedCastDualSummon1']
allacts=list(bpy.data.actions);dump={};rows=[]
for name in clips:
 act=next(a for a in allacts if a.name.endswith(name));rig.animation_data.action=act
 if hasattr(act,'slots') and act.slots:rig.animation_data.action_slot=act.slots[0]
 f0,f1=act.frame_range;keys=[]
 for f in range(int(f0),int(f1)+1):
  scene.frame_set(f);keys.append({n:{'q':list((rig.matrix_world@b.matrix).to_quaternion()),'p':list((rig.matrix_world@b.matrix).translation)} for n,b in rig.pose.bones.items() if n.startswith('B_')})
 dump[name]={'fps':30,'keys':keys,'duration':(f1-f0)/30}
 for view in ['front','three_quarter','left']:
  row=[]
  for i in range(5):
   f=f0+(f1-f0)*i/4;scene.frame_set(int(f),subframe=f%1)
   path=common.render_views(str(P/'review'/f'source_{name}_{i}'),1.25,2.9,views=(view,),resolution=(240,360))[0];row.append([path,f'{name} {f:.1f}'])
  rows.append(row)
(P/'work/source_motion.json').write_text(json.dumps(dump))
(P/'review/source_motion_frames.json').write_text(json.dumps(rows))
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
rest={}
for b in rig.data.bones:
 if not b.name.startswith('B_'):continue
 m=rig.matrix_world@b.matrix_local;rest[b.name]={'parent':b.parent.name if b.parent else None,'head':list(m.translation),'rot':[list(r) for r in m.to_3x3().normalized()]}
(P/'work/source_rest.json').write_text(json.dumps(rest,indent=2))
print('SOURCE_MOTION',[(n,v['duration']) for n,v in dump.items()])
