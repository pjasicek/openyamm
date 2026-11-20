"""Review cached spear actions without purchasing animations."""
import bpy,sys,math,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
common.clear_scene();bpy.context.scene.render.fps=48
bpy.ops.import_scene.gltf(filepath=str(P.parents[2]/'anim_library/humanoid_set/2Hand Spear.glb'))
r=next(o for o in bpy.data.objects if o.type=='ARMATURE');r.rotation_euler.z=math.pi
sc=common.setup_render();common.workbench_clay(sc);out=P/'review/round3_sources';out.mkdir(exist_ok=True)
report={}
for number in [1,2,6,7,10]:
 name=f'2HandSpearAttack{number}';a=next(a for a in bpy.data.actions if a.name.split('|')[-1].split('@')[-1]==name)
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];lo,hi=a.frame_range;report[name]=[lo,hi]
 for i,t in enumerate([0,.25,.5,.65,1]):
  f=lo+(hi-lo)*t;sc.frame_set(int(f),subframe=f%1)
  common.render_views(str(out/f'{number}_{i}'),.9,2.3,views=('three_quarter','left'),resolution=(360,440))
(out/'clips.json').write_text(json.dumps(report,indent=2))
