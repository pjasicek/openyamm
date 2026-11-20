"""Inspect owned mutant and wolfman sources before selecting the Guardian attack revision."""
from pathlib import Path
import bpy,sys,json,hashlib
from mathutils import Vector
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2]
sys.path.insert(0,str(P.parent/'mm6_natm_claude/scripts'));import common
O=P/'review/attack_revision_02/sources';O.mkdir(parents=True,exist_ok=True)
items=[('mutant_swipe','anim_library/mixamo/Mutant Swiping.fbx',None),('mutant_punch','anim_library/mixamo/Mutant Punch.fbx',None),('mutant_jump','anim_library/mixamo/Mutant Jump Attack.fbx',None),('wolfman','assets_source/worlds/mm6/models/mm6_wwf.glb','Attack')]
reports=[]
for label,rel,clip in items:
 bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene;scene.render.fps=30
 if clip:
  bpy.ops.import_scene.gltf(filepath=str(ROOT/rel));rig=next(o for o in scene.objects if o.type=='ARMATURE');act=next(a for a in bpy.data.actions if a.name==clip or a.name.startswith(clip+'_'))
 else:
  bpy.ops.import_scene.fbx(filepath=str(ROOT/'anim_library/mixamo/characters/warrok_w_kurniawan.fbx'));rig=next(o for o in scene.objects if o.type=='ARMATURE');before=set(bpy.data.objects);acts=set(bpy.data.actions)
  bpy.ops.import_scene.fbx(filepath=str(ROOT/rel));act=next(a for a in bpy.data.actions if a not in acts)
  for ob in set(bpy.data.objects)-before:bpy.data.objects.remove(ob,do_unlink=True)
 rig.animation_data_create();rig.animation_data.action=act
 if act.slots:rig.animation_data.action_slot=act.slots[0]
 for tr in rig.animation_data.nla_tracks:tr.mute=True
 fps=scene.render.fps/scene.render.fps_base;f0,f1=act.frame_range
 common.workbench_clay(scene);frames=[]
 for i in range(7):
  f=f0+(f1-f0)*i/6;scene.frame_set(int(f),subframe=f%1);bpy.context.view_layer.update()
  coords=[o.matrix_world@Vector(v) for o in scene.objects if o.type=='MESH' for v in o.bound_box];lo=min(v.z for v in coords);hi=max(v.z for v in coords)
  center=(hi+lo)/2;extent=max(hi-lo,2.4 if clip else 2.0)
  common.render_views(str(O/f'{label}_{i}'),center,extent*1.35,views=('front','left'),resolution=(440,440));frames.append({'time':(f-f0)/fps,'frame':f})
 reports.append({'name':label,'path':rel,'sha256':hashlib.sha256((ROOT/rel).read_bytes()).hexdigest(),'fps':fps,'duration':(f1-f0)/fps,'frames':frames,'bones':[b.name for b in rig.data.bones]})
 print('SOURCE',label,fps,(f1-f0)/fps,flush=True)
(O/'sources.json').write_text(json.dumps(reports,indent=2)+'\n')
assert len(reports)==4
