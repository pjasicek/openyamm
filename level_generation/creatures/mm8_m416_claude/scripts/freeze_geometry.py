from pathlib import Path
import runpy,sys,bpy
P=Path(__file__).resolve().parents[1];W=P/'work'
def run(n,args=()):
 s=P/'scripts'/n;sys.argv=[str(s),'--',*map(str,args)];runpy.run_path(str(s),run_name='__main__')
run('refine_clearance.py')
run('all_deformation.py')
run('surface_checks.py')
run('jerk_probe.py',[W/'animated.blend','Standing','Walking','Running','Attack','Hit','Death','Fidget'])
run('reduce_rigged.py',[W/'animated.blend',W/'reduced.blend'])
run('export_uploads.py')
run('clean_props.py')
