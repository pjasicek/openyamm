from pathlib import Path
import bpy,sys,runpy,json
P=Path(__file__).resolve().parents[1]
def run(n,args):
 s=P/'scripts'/(n+'.py');sys.argv=[str(s),'--',*map(str,args)];runpy.run_path(str(s),run_name='__main__')
bpy.ops.wm.open_mainfile(filepath=str(P/'work/ready_final.blend'));roles=['Standing','Walking','Running','Attack','Hit','Death','Fidget'];picks=[f'{n}:{bpy.data.actions[n].frame_range[1]*w}' for n in roles for w in [0,.25,.5,.75,1]]
run('g4_weights',[P/'work/ready_final.blend','delivered',*picks]);run('g5_hand_stretch',[P/'work/ready_final.blend',*roles]);run('export_parity',[])
run('render_tex',[P/'work/ready_final.blend',P/'textures/m416_basecolor_1k.png','composed',P/'textures/m416_head_basecolor_1k.png'])

run('loop_checks',[])
