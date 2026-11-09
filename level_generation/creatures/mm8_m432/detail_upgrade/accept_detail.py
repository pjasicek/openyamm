"""Record an agent's completed visual review; call only after inspecting the named contacts."""
from pathlib import Path
import json,sys,hashlib,datetime
D=Path(__file__).resolve().parent;p=D/'jobs.json';data=json.loads(p.read_text());reg=json.loads((D/'registration.json').read_text())
for key in sys.argv[1:]:
 job=data['jobs'][key];job['accepted_calibration']=job['generation']['shared_calibration'];job['status']='accepted_detail_and_placement';paths=[f'review/registration/{key}.png']+[f'{folder}/{name}.png' for folder in ['registered_2x','toned_2x'] for name in job['frames']];job['visual_acceptance']={'findings':'Native pose, stored view, head direction, equipment, material shapes, anatomical scale and anchored 2x placement visually reviewed. Higher generated detail remains visible at runtime size. Palette/export checks are separate.','accepted_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'hashes':{p:hashlib.sha256((D/p).read_bytes()).hexdigest() for p in paths}}
 for name in job['frames']:reg[name]['state']='accepted_detail_and_placement'
p.write_text(json.dumps(data,indent=2)+'\n');(D/'registration.json').write_text(json.dumps(reg,indent=2)+'\n');print('Recorded detail/placement review for',sys.argv[1:])
