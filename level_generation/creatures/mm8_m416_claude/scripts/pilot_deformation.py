from pathlib import Path
import runpy,sys
P=Path(__file__).resolve().parents[1];W=P/'work'
def run(n,args):
 s=P/'scripts'/n;sys.argv=[str(s),'--',*map(str,args)];runpy.run_path(str(s),run_name='__main__')
run('twist_bones.py',[W/'pilot.blend',W/'pilot_twist.blend'])
run('foot_level.py',[W/'pilot_twist.blend',W/'pilot_level.blend','Standing','Walking:const','Attack'])
run('g4_weights.py',[W/'pilot_level.blend','pilot','Standing:0','Walking:0','Walking:6','Walking:12','Walking:18','Attack:0','Attack:8','Attack:15','Attack:20','Attack:30','Attack:39','Attack:45','Attack:51'])
run('g5_hand_stretch.py',[W/'pilot_level.blend','Standing','Walking','Attack'])
