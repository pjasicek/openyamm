"""Rebuild the two weapons on the fitted masters without changing their body or motion."""
from pathlib import Path
import runpy,sys
P=Path(__file__).resolve().parents[1]
for name in ('lancer_polished','lancer_complete'):
    source=P/f'work/{name}.blend'
    sys.argv=['make_lance.py','--',str(source),str(source)]
    runpy.run_path(str(P/'scripts/make_lance.py'),run_name='__main__')
sys.argv=['export_lancer.py','--',str(P/'work/lancer_complete.blend')]
runpy.run_path(str(P/'scripts/export_lancer.py'),run_name='__main__')
