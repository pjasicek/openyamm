import sys,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
from bow_loft import replace_bow
from rebake_render import render
choices=[('loft2',2,8,[-.565,-.555,-.54,-.50,-.44,-.38,-.32,-.26,-.20,-.14,-.105,-.095,-.085,.085,.095,.105,.14,.20,.26,.32,.38,.44,.50,.54,.565]),('loft3a',3,4,[-.565,-.555,-.44,-.32,-.20,-.105,-.085,0,.085,.105,.20,.32,.44,.555,.565]),('loft3b',3,6,[-.565,-.35,-.105,-.095,-.085,.085,.095,.105,.35,.565]),('loft3c',3,8,[-.565,-.35,-.085,0,.085,.35,.565])]
for tag,level,n,zs in choices:
 path=replace_bow(P/f'work/rebake/fitfine{level}.blend',tag,n,zs);render(path,tag,level,parts=['bow'])
 r=json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/rebake_measure.py'),tag,str(level),'8','bow'],text=True));(P/f'review/rebake/{tag}_geometry_metrics.json').write_text(json.dumps(r,indent=2));print('LOFT_SILHOUETTE',tag,r['bow']['pooled_iou'],flush=True)
