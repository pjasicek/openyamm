from pathlib import Path
import bpy,json,math
P=Path(__file__).resolve().parents[1];R=P.parents[2]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=30
bpy.ops.import_scene.gltf(filepath=str(R/'anim_library/humanoid_set/2Hand Crossbow.glb'))
a=next(o for o in bpy.data.objects if o.type=='ARMATURE');a.rotation_mode='XYZ';a.rotation_euler=(0,0,math.pi);bpy.context.view_layer.update()
print('OBJECTS',[(o.name,o.type,len(o.data.vertices) if o.type=='MESH' else 0) for o in bpy.data.objects]);print('BONES',[b.name for b in a.data.bones])
acts={x.name.split('@')[-1].split('|')[-1]:x for x in bpy.data.actions};rows={}
for k in ['2HandCrossbowIdle','2HandCrossbowAiming','2HandCrossbowAimingFire','2HandCrossbowReload','2HandCrossbowDeath1','2HandCrossbowGetHitF1','2HandCrossbowWalk']:
 act=acts[k];a.animation_data.action=act
 if act.slots:a.animation_data.action_slot=act.slots[0]
 f0,f1=act.frame_range;out=[]
 for f in [f0,(f0+f1)/2,f1]:
  bpy.context.scene.frame_set(int(f),subframe=f-int(f));out.append({'frame':f,'joints':{b.name:list(a.matrix_world@b.head) for b in a.pose.bones if any(s in b.name for s in ('Hand','Forearm','UpperArm','Finger2'))}})
 rows[k]={'frames':[f0,f1],'poses':out}
(P/'work/crossbow_source_probe.json').write_text(json.dumps(rows,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/source_crossbow.blend'))
print('SOURCE',json.dumps(rows))
