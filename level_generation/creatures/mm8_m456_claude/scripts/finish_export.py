from pathlib import Path
import sys,runpy,bpy
p=Path(__file__).resolve().parents[1]
def run(n,*args):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
run('fit_underlayer.py')
run('polish_motion.py')
run('reduce_rigged.py',p/'work/master_uv_fitted.blend',p/'work/master_reduced.blend')
run('render_tex.py',p/'work/master_reduced.blend',p/'textures/body_basecolor.png','texture_graded',p/'textures/head_basecolor.png')
run('export_runtime.py')
