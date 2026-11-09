"""Shared angular jitter checks plus explicit 48-Hz cyclic pelvis/head position checks."""
import json
from pathlib import Path
import sys
import numpy as np

P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P.parent / 'claude_shared/gates'))
import run_gates as g
path = Path(sys.argv[sys.argv.index('--')+1])
glb = g.Glb(path)
clip = next(a for a in glb.doc['animations'] if a['name']=='Running')
duration = max(float(glb.accessor(s['input']).max()) for s in clip['samplers'])
times = g.sample_grid(0,duration,48)
pose = glb.pose(clip,times)
names = ['B_Pelvis','B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head']
aliases = dict(zip([f'B_{s}_{n}' for s in 'LR' for n in ['UpperArm','Forearm','Hand']],names))
config = json.loads((P/'gates_runswap.json').read_text())
config['bones'] = aliases
report = g.Report(config)
g.bone_gates(glb,pose,times,'Running',config,report,[])
rows = []
for row in report.rows.values():
    if row['gate'] in ['rotation_step_deg','angular_acceleration_deg_s2'] and row['region'] in aliases:
        row['region'] = aliases[row['region']]
        rows.append(row)
assert all(r['status']=='PASS' for r in rows), rows
result = {'sha256':glb.sha256,'shared_angular_jitter':rows,'vertical':{}}
# A uniform periodic grid includes the wraparound seam in derivatives.
n = round(duration*480)
ts = np.arange(n)*duration/n
world = glb.pose(clip,ts)
for name in ['B_Pelvis','B_Head']:
    z = world[:,glb.names[name],2,3]
    sample48 = glb.pose(clip,np.arange(round(duration*48))*duration/round(duration*48))[:,glb.names[name],2,3]
    step = float(abs(np.roll(sample48,-1)-sample48).max())
    half = float(abs(z-np.roll(z,n//2)).max())
    velocity = np.gradient(z,duration/n)
    # Frame-rate derivatives avoid treating the exported linear key knots as physical impulses.
    acc48 = (np.roll(sample48,-1)-2*sample48+np.roll(sample48,1))/(duration/len(sample48))**2
    result['vertical'][name] = {'peak_to_peak_mm':float(np.ptp(z)*1000),
        'max_48hz_step_mm':step*1000,'half_cycle_difference_mm':half*1000,
        'max_speed_m_s':float(abs(velocity).max()),'max_48hz_acceleration_m_s2':float(abs(acc48).max())}
    assert step<.020,(name,step)
    assert abs(acc48).max()<25,(name,abs(acc48).max())
    if name=='B_Pelvis': assert half<.001,(name,half)
result['limits']={'vertical_step_mm':20,'vertical_acceleration_m_s2':25,'pelvis_half_cycle_difference_mm':1}
result['note']='Angular rows use the unmodified shared runner. Positional limits are explicit project jitter checks.'
(P/'review/runswap3_20261013/jitter.json').write_text(json.dumps(result,indent=2)+'\n')
print('RUNNING_JITTER',json.dumps(result['vertical']))
