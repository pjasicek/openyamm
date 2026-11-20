"""Prepare frozen native4x4 liquid animation atlases and native capture actions."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import json
from common import *

F=Path(__file__).resolve().parent
(F/'inputs').mkdir(exist_ok=True)
for family,prefix,base in [('water','hdwtr','wtrtyl'),('lava','hdlav','lavtyl'),('tar','hwoil','tartyl')]:
    sheet=Image.new('RGB',(1024,1024))
    for i in range(16):
        name=prefix+'%03d'%i if i<14 else base
        im=Image.open(P/'references'/(name+'.png')).convert('RGB').resize((256,256),Image.Resampling.BICUBIC)
        sheet.paste(im,(i%4*256,i//4*256))
    sheet.save(F/'inputs'/(family+'_atlas.png'))
    Image.open(P/'references'/(prefix+'000.png')).resize((512,512),Image.Resampling.BICUBIC).save(F/'inputs'/(family+'_frame0.png'))
actions=F/'capture_cycle.json'
actions.write_text(json.dumps([dict(burst=dict(count=40,interval=.1,prefix='cycle'))],indent=2)+'\n')
report_path=P/'reports/native_stage.json';report=json.loads(report_path.read_text())
for family in ('water','lava','tar'):
    record=dict(report['poses'][family])
    record.update(actions=str(actions.relative_to(P)),actions_sha256=sha(actions))
    report['poses']['liquid_'+family]=record
report_path.write_text(json.dumps(report,indent=2)+'\n')
