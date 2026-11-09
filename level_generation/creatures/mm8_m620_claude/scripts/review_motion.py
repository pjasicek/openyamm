from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1]
runpy.run_path(str(p/'scripts/polish_motion.py'),run_name='__main__')
runpy.run_path(str(p/'scripts/check_motion.py'),run_name='__main__')
for view in ['front','left']:
 sys.argv=['clip_sheet.py','--',str(p/'work/motion_fitted.blend'),str(p/'review'/('motion_'+view)),view,'4','Standing','Walking','Fidget','Hit','Death','Dead']
 runpy.run_path(str(p/'scripts/clip_sheet.py'),run_name='__main__')
