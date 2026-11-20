import bpy,json,math
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1];bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(P.parents[2]/'anim_library/mixamo/Great Sword Slash (2).fbx'));r=next(o for o in bpy.data.objects if o.type=='ARMATURE');a=r.animation_data.action;sc=bpy.context.scene;W=r.matrix_world;pre=next(n for n in r.data.bones.keys() if n.endswith('Hips'))[:-4];sf=json.loads((P/'work/source_rest.json').read_text());rows=[]
for f in range(int(a.frame_range[0]),int(a.frame_range[1])+1):
 sc.frame_set(f);hands={s:W@r.pose.bones[pre+sd+'Hand'].matrix for s,sd in [('R','Right'),('L','Left')]};centers={s:sum((W@r.pose.bones[pre+sd+'Hand'+fi+'2'].head for fi in ['Index','Middle','Ring','Pinky']),Vector())/4 for s,sd in [('R','Right'),('L','Left')]};axis=(centers['R']-centers['L']).normalized();local=hands['R'].to_3x3().normalized().inverted()@axis;targetlocal=Matrix(sf['B_R_Hand']['rot']).inverted()@(W@r.data.bones[pre+'RightHand'].matrix_local).to_3x3().normalized()@local;rows.append({'frame':f,'axis_world':list(axis),'axis_source_local':list(local),'axis_target_local':list(targetlocal),'grip_spacing':(centers['R']-centers['L']).length})
print('GRIP_AXES',json.dumps(rows[::4]));(P/'work/round1_mixamo_grip.json').write_text(json.dumps(rows,indent=2))
