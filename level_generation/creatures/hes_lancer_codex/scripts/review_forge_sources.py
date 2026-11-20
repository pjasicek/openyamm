"""Extract owned attack poses for the heavy-maul selection study."""
import bpy,json,sys,os
from pathlib import Path
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2]
jobs=[('RPG '+str(i),'anim_library/humanoid_set/2Hand Axe.glb','2HandAxeAttack'+str(i)) for i in range(1,7)]
jobs += [('Meshy 128','anim_library/meshy/128_heavy_hammer_swing/animation.glb',None)]
jobs += [('Mixamo '+str(i),'anim_library/mixamo/Great Sword Slash ('+str(i)+').fbx',None) for i in (2,4)]
report={}
for label,path,clip in jobs:
 bpy.ops.wm.read_factory_settings(use_empty=True)
 if path.endswith('.fbx'):bpy.ops.import_scene.fbx(filepath=str(ROOT/path))
 else:bpy.ops.import_scene.gltf(filepath=str(ROOT/path))
 rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');a=bpy.data.actions.get(clip) if clip else list(bpy.data.actions)[0]
 rig.animation_data_create();rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
 names=[b.name for b in rig.data.bones if not any(t in b.name.lower() for t in ('finger','thumb','index','middle','ring','pinky','end','twist'))]
 frames=[];start,end=a.frame_range;fps=bpy.context.scene.render.fps
 for t in [0,.16,.3,.42,.52,.66,.82,1]:
  f=start+t*(end-start);bpy.context.scene.frame_set(int(f),subframe=f-int(f))
  frames.append({n:list(rig.matrix_world@rig.pose.bones[n].head) for n in names})
 report[label]={'file':path,'clip':a.name,'duration':(end-start)/fps,'parents':{n:rig.data.bones[n].parent.name if rig.data.bones[n].parent else None for n in names},'frames':frames}
(P/'review/heavy_maul_sources.json').write_text(json.dumps(report,indent=2))
print('SOURCE_STUDY_READY',flush=True);os._exit(0)
