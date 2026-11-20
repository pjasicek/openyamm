from pathlib import Path
import bpy,sys,runpy
P=Path(__file__).resolve().parents[1]
def run(n,args):
 s=P/'scripts'/(n+'.py');sys.argv=[str(s),'--',*map(str,args)];runpy.run_path(str(s),run_name='__main__')
roles=['Standing','Walking','Running','Attack','Hit','Death','Fidget']
run('render_tex',[P/'work/ready_final.blend',P/'textures/m416_basecolor_1k.png','composed',P/'textures/m416_head_basecolor_1k.png'])
run('clip_sheet',[P/'work/ready_final.blend',P/'review/final_motion','front',8,'Death','Attack'])
run('jerk_probe',[P/'work/ready_final.blend',*roles])
run('g4_weights',[P/'work/ready_final.blend','final',*[f'{n}:{f}' for n in roles for f in [0,5,10,15,20]]])
run('g5_hand_stretch',[P/'work/ready_final.blend',*roles])
run('gait_probe',[])
run('equipment_checks',[])
