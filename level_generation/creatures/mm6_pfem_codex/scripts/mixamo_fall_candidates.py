"""Inspect local Mixamo fall direction from the animated chest, before choosing a replacement."""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector,Matrix
p=Path(__file__).resolve().parents[1];out={}
for name in ('Falling Forward Death','Standing Death Forward 02','Death From The Back'):
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=30
 bpy.ops.import_scene.fbx(filepath=f'/home/pjasicek/Downloads/mixamo_library/{name}.fbx')
 r=next(o for o in bpy.data.objects if o.type=='ARMATURE');a=r.animation_data.action;sc=bpy.context.scene
 bone=lambda n:next(b for b in r.data.bones if b.name.split(':')[-1]==n)
 toe=r.matrix_world@bone('LeftToeBase').head_local;foot=r.matrix_world@bone('LeftFoot').head_local
 forward=Vector((0,1 if toe.y>foot.y else -1,0));bn=bone('Spine2').name;rest=(r.matrix_world@r.data.bones[bn].matrix_local).to_3x3().normalized()
 sc.frame_set(round(a.frame_range[1]));pose=(r.matrix_world@r.pose.bones[bn].matrix).to_3x3().normalized()
 fw=pose@rest.inverted()@forward
 out[name]={'duration':float((a.frame_range[1]-a.frame_range[0])/sc.render.fps),'fps':sc.render.fps,'frames':list(a.frame_range),'fwd_z_end':fw.z,'toe_forward_y':forward.y,'bones':len(r.data.bones),'meshes':len([o for o in bpy.data.objects if o.type=='MESH'])}
 print('MIXAMO',name,out[name])
(p/'work/mixamo_fall_candidates.json').write_text(json.dumps(out,indent=2))
