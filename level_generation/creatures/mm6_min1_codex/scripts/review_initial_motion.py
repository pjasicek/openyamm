import bpy,os,sys,runpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P);sys.path.insert(0,str(P/'scripts'));import common
sys.argv=['apply_grip.py','--','work/rig_v4.blend','work/rig_v5.blend'];runpy.run_path(str(P/'scripts/apply_grip.py'),run_name='__main__')
rig=bpy.data.objects['Rig'];scene=bpy.context.scene;common.workbench_clay(scene)
for nm in ['Standing','Walking','Running','Attack','Cast','Hit','Death','Fidget']:
 act=bpy.data.actions[nm];rig.animation_data.action=act
 if len(act.slots):rig.animation_data.action_slot=act.slots[0]
 for i in range(4):
  f=int(act.frame_range[0]+(act.frame_range[1]-act.frame_range[0])*i/3);scene.frame_set(f);common.render_views(str(P/f'review/initial_{nm}_{i}'),.95,2.5,views=['front','left','three_quarter'],resolution=(240,360))
roles=['Standing','Walking','Running','Attack','Cast','Hit','Death','Fidget']
sys.argv=['g5_hand_stretch.py','--','work/rig_v5.blend',*roles];runpy.run_path(str(P/'scripts/g5_hand_stretch.py'),run_name='__main__')
sys.argv=['g4_weights.py','--','work/rig_v5.blend','initial','Standing:0','Walking:12','Attack:12','Attack:20','Attack:30','Death:24'];runpy.run_path(str(P/'scripts/g4_weights.py'),run_name='__main__')
