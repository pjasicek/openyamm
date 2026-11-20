import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for f,args in [('weights_minotaur.py',[]),('finger_weights.py',[P/'work/rig_v3.blend',P/'work/rig_v4.blend']),('fit_pilots.py',[]),('check_pilots.py',[])]:
 sys.argv=[f,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/f),run_name='__main__')
