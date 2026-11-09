import bpy,sys,os,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'));import common
R=P/'review';(R/'tiers').mkdir(exist_ok=True);(R/'closeups').mkdir(exist_ok=True)
for tier in 'abc':
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(R/f'viewer/mm6_lch_{tier}.glb'))
 rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');body=bpy.data.objects['Lich'];rig.name='Rig';body.name='Body'
 act=bpy.data.actions['Standing'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];bpy.context.scene.frame_set(0)
 common.workbench_clay(bpy.context.scene,textured=True)
 common.render_views(str(R/f'tiers/lch_{tier}'),.9,2.1,views=('front','left','three_quarter'),resolution=(420,630))
 if tier=='a':
  bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/final_review.blend'))
  common.render_views(str(R/'closeups/head'),1.60,.53,views=('front','left','back','three_quarter'),resolution=(480,480))
for view in ['front','left','three_quarter']:
 sys.argv=['clip_sheet.py','--',str(P/'work/final_review.blend'),str(R/('clips_'+view)),view,'6','Standing','Walking','Attack','Cast','Hit','Death','Dead','Fidget']
 os.environ['TEXTURED']='1';runpy.run_path(str(P/'scripts/clip_sheet.py'),run_name='__main__')
sys.argv=['glb_hand_closeups.py','--',str(R/'viewer/mm6_lch_a.glb'),str(R/'closeups/hands'),'Standing:0','Attack:0.729','Cast:0.625','Fidget:0.7']
runpy.run_path(str(P/'scripts/glb_hand_closeups.py'),run_name='__main__')
