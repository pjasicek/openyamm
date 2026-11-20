from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1];s=p/'scripts/g4_weights.py'
sys.argv=[str(s),'--',str(p/'work/rig_v5.blend'),'skin','Standing:0','Attack:25','Attack:28','Attack:34','Walking:6','Running:6','Death:20'];runpy.run_path(str(s),run_name='__main__')
