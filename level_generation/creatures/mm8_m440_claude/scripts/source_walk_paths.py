from pathlib import Path
import bpy,json,math
p=Path(__file__).resolve().parents[1];bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(p.parents[2]/'anim_library/mixamo/Orc Walk.fbx'));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');sc=bpy.context.scene;a=rig.animation_data.action;fps=sc.render.fps/sc.render.fps_base;f0,f1=a.frame_range;prefix=next(n for n in rig.data.bones.keys() if n.endswith('Hips'))[:-4];names=['Hips']+[s+n for s in ('Left','Right') for n in ('UpLeg','Leg','Foot','ToeBase')];rest={n:list(rig.matrix_world@rig.data.bones[prefix+n].head_local) for n in names};rows=[]
for i in range(73):
 f=f0+i/60*fps;sc.frame_set(int(f),subframe=f-int(f));rows.append({n:list(rig.matrix_world@rig.pose.bones[prefix+n].head) for n in names})
x={'fps':60,'duration':(f1-f0)/fps,'rest':rest,'frames':rows};(p/'work/source_walk_paths.json').write_text(json.dumps(x));print('SOURCE_WALK',rest,'FIRST',rows[0])
