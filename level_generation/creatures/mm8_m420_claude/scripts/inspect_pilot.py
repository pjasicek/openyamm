from pathlib import Path
import bpy,runpy,sys
P=Path(__file__).resolve().parents[1];W=P/'work';sys.path.insert(0,str(P/'scripts'))
for view in ['front','left','back']:
 sys.argv=['clip_sheet.py','--',str(W/'pilot.blend'),str(P/'review'/('pilot_'+view)),view,'5','Standing','Walking','Running','AttackSource','HitSource','Death']
 runpy.run_path(str(P/'scripts/clip_sheet.py'),run_name='__main__')
