import bpy,json,math
from pathlib import Path
from mathutils import Matrix
p=Path(__file__).resolve().parents[1];bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=30
bpy.ops.import_scene.gltf(filepath=str(p.parents[2]/'anim_library/humanoid_set/Unarmed.glb'));r=next(o for o in bpy.data.objects if o.type=='ARMATURE');turn=Matrix.Rotation(math.pi+math.radians(41.5),4,'Z');k=.9786/(r.matrix_world@r.data.bones['B_Pelvis'].head_local).z
out={}
for role,clip in [('Attack','UnarmedCastDualAttack2'),('Cast','UnarmedCastDualAttack3')]:
 a=next(a for a in bpy.data.actions if a.name.split('@')[-1].split('|')[-1]==clip);r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];pts={s:[] for s in ['L','R']}
 for f in range(int(a.frame_range[0]),int(a.frame_range[1])+1):
  bpy.context.scene.frame_set(f)
  for s in pts:pts[s].append(turn@r.matrix_world@r.pose.bones[f'B_{s}_Foot'].head)
 tracks={}
 for s,rows in pts.items():
  delta=[(v-rows[0])*k for v in rows];peak=max(range(len(delta)),key=lambda i:delta[i].xy.length)
  tracks[s]={'source_peak_frame':peak,'source_delta_m':list(delta[peak]),'step_delta_m':[delta[peak].x*.2,delta[peak].y*.2,0]}
 sd=max(tracks,key=lambda s:sum(v*v for v in tracks[s]['step_delta_m']));out[role]={'clip':clip,'side':sd,**tracks[sd],'all_feet':tracks}
(p/'work/source_steps.json').write_text(json.dumps(out,indent=2));print('SOURCE_STEPS',json.dumps(out))
