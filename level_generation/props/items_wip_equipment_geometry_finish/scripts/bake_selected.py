"""Bake selected owned models independently and retain every strict-gate failure."""
import json,sys,traceback
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P/'scripts'))
import codex_texture as texture
report={}
for icon in sys.argv[sys.argv.index('--')+1:]:
    try:
        texture.bake('equipment_'+icon)
        report[icon]={'passed':True}
    except Exception as error:
        report[icon]={'passed':False,'error':str(error)}
        traceback.print_exc()
    (P/'review/bake_batch_latest.json').write_text(json.dumps(report,indent=2)+'\n')
print('BATCH_RESULTS',json.dumps(report),flush=True)
