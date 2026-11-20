from pathlib import Path
import runpy,sys
P=Path(__file__).resolve().parents[1]
sys.argv=['stride.py','--',str(P/'work/rig_reduced.blend'),'Walking','Running']
runpy.run_path(str(P/'scripts/stride.py'),run_name='__main__')
