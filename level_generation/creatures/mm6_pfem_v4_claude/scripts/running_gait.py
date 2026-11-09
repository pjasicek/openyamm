"""Running-only posture, per-foot contact and distance-driven stance checks on the exported mesh."""
import json
from pathlib import Path
import sys
import numpy as np

P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P.parent/'claude_shared/gates'))
import run_gates as g

path = Path(sys.argv[sys.argv.index('--')+1])
glb = g.Glb(path)
clips = {a['name']:a for a in glb.doc['animations']}
clip = clips['Running']
config = json.loads((P/'gates_runswap.json').read_text())
mesh = next(m for m in g.load_meshes(glb) if m.label.endswith('/colour0'))
g.configure_mesh(mesh, config, g.Report(config))
duration = max(float(glb.accessor(s['input']).max()) for s in clip['samplers'])
n = round(duration*480)
phases = np.arange(n)/n
times = phases*duration
poses = glb.pose(clip, times)
standing = glb.pose(clips['Standing'], np.array([0.]))[0,glb.names['B_Pelvis'],2,3]
height = poses[:,glb.names['B_Pelvis'],2,3]
sole = {s:[] for s in 'LR'}
knees = {s:[] for s in 'LR'}
for pose in poses:
    points = mesh.posed(pose)
    for s in 'LR':
        sole[s].append(float(points[mesh.feet[s][0],2].min()))
        hip,knee,ankle = [pose[glb.names[f'B_{s}_{b}'],:3,3] for b in ['Thigh','Calf','Foot']]
        knees[s].append(float(g.angle(knee-hip,ankle-knee)))
sole = {s:np.array(v) for s,v in sole.items()}
contact = {s:sole[s]<=.01 for s in 'LR'}
result = {'sha256':glb.sha256,'standing_pelvis_m':float(standing),'pelvis_min_m':float(height.min()),
          'pelvis_mean_m':float(height.mean()),'pelvis_min_pct':float(height.min()/standing*100),
          'pelvis_mean_pct':float(height.mean()/standing*100),'pelvis_bob_mm':float(np.ptp(height)*1000),
          'stride_m':1.6,'duration_s':duration,'samples_hz':480,'feet':{}}
for s,start in [('L',.25),('R',.75)]:
    # Add the engine's forward translation to the in-place foot during its 35% stance.
    phase = start+np.linspace(0,.35,180)
    stance_pose = glb.pose(clip,(phase%1)*duration)
    foot = stance_pose[:,glb.names[f'B_{s}_Foot'],:3,3].copy()
    foot[:,1] -= 1.6*phase
    drift = float(np.linalg.norm(foot[:,:2]-foot[:1,:2],axis=1).max()*1000)
    pct = float(contact[s].mean()*100)
    stance = ((phases-start)%1)<.35
    result['feet'][s] = {'contact_pct':pct,'stance_slip_max_mm':drift,
        'stance_knee_min_deg':float(np.array(knees[s])[stance].min()),
        'stance_knee_max_deg':float(np.array(knees[s])[stance].max()),
        'swing_knee_max_deg':float(np.array(knees[s])[~stance].max())}
    assert 35<=pct<=45,(s,pct)
    assert drift<2,(s,drift)
flight = ~(contact['L']|contact['R'])
low = np.minimum(sole['L'],sole['R'])
result['any_contact_pct'] = float((~flight).mean()*100)
result['flight_pct'] = float(flight.mean()*100)
result['max_flight_sole_mm'] = float(low.max()*1000)
result['runtime_cycle_seconds'] = {str(speed):1.6*98.9/speed for speed in [260,280,300]}
assert height.min() >= .92*standing
assert low.max() <= .06
assert flight.any()
(P/'review/runswap3_20261013/gait.json').write_text(json.dumps(result,indent=2)+'\n')
print('RUNNING_GAIT',json.dumps(result))
