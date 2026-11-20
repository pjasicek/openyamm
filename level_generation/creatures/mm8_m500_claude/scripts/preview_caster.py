"""Inspect owned caster sources; use gestures as choreography, not humanoid locomotion."""
import bpy, math, json, sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P.parents[2]
sys.path.insert(0,str(R/'level_generation/creatures/mm6_bar1_claude/scripts'))
import common
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.render.fps=30
bpy.ops.import_scene.gltf(filepath=str(R/'anim_library/humanoid_set/Unarmed.glb'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
rig.rotation_mode='XYZ';rig.rotation_euler=(0,0,math.pi)
for o in bpy.data.objects:
 if o.type=='MESH' and o.parent!=rig:o.hide_render=True
sc=bpy.context.scene;sc.render.fps=30;common.workbench_clay(sc)
acts={a.name.split('@')[-1].split('|')[-1]:a for a in bpy.data.actions}
rows=[];records=[]
for name in ['UnarmedCastDualAOE2','UnarmedCastDualAttack2']:
 matches=[a for k,a in acts.items() if k.replace('-','')==name]
 assert len(matches)==1,(name,list(acts))
 a=matches[0];rig.animation_data.action=a
 if len(a.slots):rig.animation_data.action_slot=a.slots[0]
 start,end=a.frame_range;records.append({'clip':a.name,'frames':[start,end],'fps':30})
 for view in ['front','left']:
  row=[]
  for i in range(6):
   f=start+(end-start)*i/5;sc.frame_set(int(f),subframe=f-int(f))
   out=P/'review/source_motion';out.mkdir(exist_ok=True)
   path=common.render_views(str(out/f'{name}_{i}'),1.3,3.0,views=(view,),resolution=(220,300))[0]
   row.append([path,f'{name} {f:.0f}'])
  rows.append(row)
(P/'review/source_motion/frames.json').write_text(json.dumps(rows))
(P/'work/caster_sources.json').write_text(json.dumps(records,indent=2))
