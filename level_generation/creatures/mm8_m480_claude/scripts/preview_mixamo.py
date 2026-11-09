from pathlib import Path
import bpy,sys,math,json,hashlib
from mathutils import Vector
P=Path(__file__).resolve().parents[1];R=P.parents[2];sys.path.insert(0,str(P/'scripts'));import common
report={}
for stem in ['Running (5)','Standing Melee Attack Backhand','Standing Melee Attack Horizontal']:
 bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene;sc.render.fps=30
 bpy.ops.import_scene.fbx(filepath=str(R/'anim_library/mixamo/characters/warrok_w_kurniawan.fbx'))
 character=next(o for o in bpy.data.objects if o.type=='ARMATURE');character.animation_data_clear()
 before=set(bpy.data.objects);bpy.ops.import_scene.fbx(filepath=str(R/'anim_library/mixamo'/f'{stem}.fbx'))
 imported=set(bpy.data.objects)-before;source=next(o for o in imported if o.type=='ARMATURE');act=source.animation_data.action
 # These downloads use the same named Mixamo mannequin. Verify the rest frames before assigning the source action.
 shared=set(character.data.bones.keys())&set(source.data.bones.keys());assert len(shared)>40,(len(shared),list(source.data.bones.keys())[:2])
 mismatch=max(2*math.acos(min(1,abs(character.data.bones[n].matrix_local.to_quaternion().dot(source.data.bones[n].matrix_local.to_quaternion())))) for n in shared);assert mismatch<0.02,mismatch
 character.animation_data_create();character.animation_data.action=act
 if len(act.slots):character.animation_data.action_slot=act.slots[0]
 for o in imported:bpy.data.objects.remove(o,do_unlink=True)
 character.rotation_mode='XYZ';character.rotation_euler.z=0
 common.workbench_clay(sc);sc.frame_set(int(act.frame_range[0]));meshes=[o for o in bpy.data.objects if o.type=='MESH'];lo,hi=common.world_bounds(meshes);height=hi.z-lo.z;rows=[]
 for view in ['left','three_quarter']:
  row=[]
  for i in range(9):
   f=act.frame_range[0]+(act.frame_range[1]-act.frame_range[0])*i/8;sc.frame_set(int(f),subframe=f-int(f));out=P/'review/motion'/stem;out.mkdir(exist_ok=True)
   path=common.render_views(str(out/f'{view}_{i}'),(hi.z+lo.z)/2,height*1.25,views=(view,),resolution=(240,380))[0];row.append([path,f'{stem} {f:.1f}'])
  rows.append(row)
 (out/'frames.json').write_text(json.dumps(rows));report[stem]={'file':str(R/'anim_library/mixamo'/f'{stem}.fbx'),'sha256':hashlib.sha256((R/'anim_library/mixamo'/f'{stem}.fbx').read_bytes()).hexdigest(),'fps':sc.render.fps/sc.render.fps_base,'frame_range':list(act.frame_range),'max_mannequin_rest_rotation_difference':mismatch}
(P/'review/motion/mixamo_sources.json').write_text(json.dumps(report,indent=2));print(report)
