"""Run the existing complete 48-Hz rig gates on one measured LOD."""
import os,sys,runpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P/'review/round3';level=int(os.environ['FIGC_GATE_LOD'])
sys.argv=['full_gates.py','--',str(R/f'lod{level}.blend')];runpy.run_path(str(P/'scripts/full_gates.py'),run_name='__main__')
r=json.loads((P/'work/full_gates.json').read_text());faults=[]
for name,row in r.items():
 for key,limit in [('arm_p99',1.5),('finger_max',4.5),('head_mm',10),('L_contact_mm',2),('R_contact_mm',2),('Axe_mm',2),('Shield_mm',2)]:
  if row[key]>limit:faults.append([name,key,row[key],limit])
 if row['minimum_z']<0:faults.append([name,'floor',row['minimum_z']])
 if name not in ['Death','Dead'] and (row['pelvis_min']<=.9 or row['trunk_lean_max']>=20):faults.append([name,'posture'])
(R/'gates'/f'lod{level}.json').write_text(json.dumps({'pass':not faults,'faults':faults,'clips':r},indent=2)+'\n');print('LOD_RIG_GATE',level,'PASS' if not faults else faults,flush=True)
