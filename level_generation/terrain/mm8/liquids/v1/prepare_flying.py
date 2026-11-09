"""Save stable hovering review poses above native liquid surfaces, avoiding hazard ticks."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import json,shutil,subprocess
from common import *

F=Path(__file__).resolve().parent
rpath=P/'reports/native_stage.json';report=json.loads(rpath.read_text());receipts=[]
for family in ('water','lava','tar'):
    record=dict(report['poses']['liquid_'+family])
    seed=F/(family+'_seed.oysav')
    assert seed.is_file(), 'Retained native scenario seed is required: '+str(seed)
    destination=F/(family+'_flying.oysav')
    pose=list(record['pose']);pose[2]+=192
    subprocess.run(['/tmp/mm8-terrain-capture-save',str(seed),str(destination),*map(str,pose),'--fly-buff'],check=True)
    record.update(pose=pose,start_save=str(destination.relative_to(P)),start_save_sha256=sha(destination))
    report['poses']['liquid_'+family+'_flying']=record
    receipts.append(dict(family=family,seed_sha256=sha(seed),save_sha256=sha(destination),pose=pose))
rpath.write_text(json.dumps(report,indent=2)+'\n')
(F/'flying_poses.json').write_text(json.dumps(dict(poses=receipts,helper_sha256=sha(Path('/tmp/mm8-terrain-capture-save')),helper_source_sha256=sha(P/'prepare_capture_save.cpp')),indent=2)+'\n')
