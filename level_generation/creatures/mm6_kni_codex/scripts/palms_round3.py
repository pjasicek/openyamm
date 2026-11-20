"""48 Hz preservation of accepted palm frames, plus actual hand-to-grip attachment distance."""
import bpy,json,numpy as np,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];W=P/'work/round3';R=P/'review/round3';cache={};report={};centre=Vector(json.loads((P/'work/weapon_fit.json').read_text())['centre_rest'])
for tag,path in [('baseline',W/'baseline_mm6_kni.glb'),('reduced',P/'export/mm6_kni.glb')]:
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(path));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');scene=bpy.context.scene
 for act in bpy.data.actions:
  rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];samples=[];grips=[]
  for f in np.arange(0,float(act.frame_range[1])+.001,scene.render.fps/48):
   scene.frame_set(int(f),subframe=float(f%1));samples.append([np.array(rig.pose.bones[f'B_{s}_Hand'].matrix).tolist()for s in 'LR'])
   h=rig.pose.bones['B_R_Hand'].matrix@rig.data.bones['B_R_Hand'].matrix_local.inverted()@centre;g=rig.pose.bones['Sword'].matrix@rig.data.bones['Sword'].matrix_local.inverted()@centre;grips.append((h-g).length)
  if tag=='baseline':cache[act.name]=np.array(samples)
  else:
   delta=float(np.max(abs(cache[act.name]-samples)));assert delta==0;gap=max(grips);assert gap<.003
   report[act.name]={'samples':len(samples),'both_palm_frame_max_matrix_delta':delta,'right_palm_grip_anchor_max_mm':gap*1000,'accepted_palm_direction_preserved':True}
(R/'palms.json').write_text(json.dumps({'sample_hz':48,'scope':'Both complete hand frames equal accepted frames on every sample; right grip anchor <=3 mm. Absolute palm design is the accepted baseline, not re-authored. Actual finger/guard/pommel contact is separately tested on each LOD.','clips':report,'pass':True},indent=2));print('PALMS',report)
