"""Repeat production gates and renders on existing exports without regenerating geometry or animations."""
import sys,runpy,bpy
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parents[1];R=P.parents[2]
for script in ['export_gates.py','ranged_gate.py','string_join_gate.py','cast_gate.py','grip_export.py']:
 runpy.run_path(str(P/'scripts'/script),run_name='__main__')
sys.argv=['g4','--',str(P/'work/export_reimport.blend'),'final','Standing:0','Walking:12','Running:12','Attack:19','Attack:22','Attack:24','Cast:15','Cast:20','Cast:24','Hit:8','Death:10','Death:15','Dead:0','Fidget:8'];runpy.run_path(str(P/'scripts/g4_weights.py'),run_name='__main__')
sys.argv=['hands','--',str(P/'export/mm6_lzd_lod0.glb'),str(P/'review/hands/export'),'Standing:0','Attack:0.7','Cast:0.734375','Death:0.27'];runpy.run_path(str(P/'scripts/glb_hand_closeups.py'),run_name='__main__')
bow=R/'anim_library/humanoid_set/2Hand Bow.glb';relax=R/'anim_library/humanoid_set/Relax.glb'
refs={'Standing':(bow,'2HandBowIdle'),'Walking':(bow,'2HandBowWalk'),'Running':(relax,'RelaxRunForward'),'Attack':(bow,'2HandBowAttack1'),'Cast':(bow,'2HandBowAttack1'),'Hit':(bow,'2HandBowGetHitF1'),'Death':(bow,'2HandBowDeath1'),'Dead':(bow,'2HandBowDeath1'),'Fidget':(bow,'2HandBowIdle')}
sys.argv=['trace','--',str(P/'export/mm6_lzd_raw.glb')]+[f'{r}={f}:{c}'for r,(f,c)in refs.items()]
runpy.run_path(str(P/'scripts/trace_export.py'),run_name='__main__')
sys.path.insert(0,str(P/'scripts'));import common
for tier in ['a','b','c']:
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(P/f'review/viewer/mm6_lzd_{tier}.glb'));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0);common.workbench_clay(bpy.context.scene,textured=True);common.render_views(str(P/f'review/tier_{tier}'),.9,2.12,views=('front','left','three_quarter'),resolution=(600,700))
print('REVIEW_EXPORTS_COMPLETE')
