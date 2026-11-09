"""A repeated service action ID must not select another destination when an exact label is requested."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import yaml
PROJECT=Path(__file__).resolve().parent
ROOT=PROJECT.parents[2]
scenario=yaml.safe_load((PROJECT/'stables_travel.yml').read_text())
results=[]
for label,message in [('', 'match_label must be a nonempty scalar'),
                      ('1 day to Missing Town for 42 gold','matching dialog action is unavailable')]:
    steps=scenario['steps'][:3]+[{'select_topic':{'action_id':22,'match_label':label}}]
    with tempfile.TemporaryDirectory(prefix='levelgen-route-label-') as directory:
        source=Path(directory)/'invalid.yml'
        source.write_text(yaml.safe_dump(dict(id='levelgen.invalid.route_label',world='mm8',mode='faithful',steps=steps)))
        proc=subprocess.run([str(ROOT/'build/game/openyamm'),'--world','mm8','--headless-run-scenario',str(source),
                             '--scenario-no-color'],cwd='/tmp/openyamm-brackenford-greywatch',
                            capture_output=True,text=True)
        passed=proc.returncode!=0 and message in proc.stdout+proc.stderr
        results.append(dict(label=label,passed=passed,expected=message))
report=dict(results=results,all_passed=all(r['passed'] for r in results),
            binary_sha256=hashlib.sha256((ROOT/'build/game/openyamm').read_bytes()).hexdigest())
(PROJECT/'review/travel_label_rejections.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
raise SystemExit(0 if report['all_passed'] else 1)
