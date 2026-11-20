"""Measure the original source axis and the accepted maul/rig before fitting the slam."""
import bpy,sys,os,json,math
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=str(P/'work/before_strike_20261024/work/forge_complete.blend'));r=bpy.data.objects['Rig'];sc=bpy.context.scene
out={};a=bpy.data.actions['Forge_Attack'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
for f in (0,30,36,39,42.5,45,51,60,75):
 sc.frame_set(int(f),subframe=f%1);out[str(f)]={n:list(armik.W(r,n).translation) for n in ('B_Pelvis','B_Spine','B_Spine2','B_R_UpperArm','B_L_UpperArm','B_R_Forearm','B_R_Hand','B_L_Hand','B_R_Calf','B_L_Calf','B_R_Foot','B_L_Foot')}
 out[str(f)]['maul_head']=list(armik.W(r,'Thunder_Maul')@Vector((0,1.02,0)));out[str(f)]['maul_axis']=list(armik.W(r,'Thunder_Maul').to_3x3()@Vector((0,1,0)))
print('CURRENT',json.dumps(out),flush=True)
sc.render.fps=30;before=set(bpy.data.objects);acts=set(bpy.data.actions);bpy.ops.import_scene.gltf(filepath=str(Path('anim_library/humanoid_set/2Hand Axe.glb').resolve()));s=next(o for o in set(bpy.data.objects)-before if o.type=='ARMATURE');a=next(a for a in set(bpy.data.actions)-acts if a.name.split('@')[-1].split('|')[-1]=='2HandAxeAttack1');s.animation_data.action=a;s.animation_data.action_slot=a.slots[0];axis=Vector(json.loads((P/'work/maul_source_grips.json').read_text())['R']['axis_hand']).normalized();turn=Matrix.Rotation(math.pi,4,'Z');rows=[]
for f in range(int(a.frame_range[0]),int(a.frame_range[1])+1):
 sc.frame_set(f);m=turn@s.matrix_world@s.pose.bones['B_R_Hand'].matrix;rows.append({'frame':f,'axis':list((m.to_3x3().normalized()@axis).normalized())})
print('SOURCE',json.dumps(rows),flush=True);(P/'review/forge_slam_source_probe.json').write_text(json.dumps({'current':out,'source_RPG':rows},indent=2)+'\n');sys.stdout.flush();os._exit(0)
