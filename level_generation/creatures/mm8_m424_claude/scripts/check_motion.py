import runpy,sys,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def run(n,*args):
    sys.argv=[n,'--',*[str(x) for x in args]]
    runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('seal_sleeves.py')
run('all_motion_gate.py')
rom=json.loads((P/'work/rom.json').read_text())['roles']; picks=set()
for name,role in rom.items():
    for j,entry in role['joints'].items():
        for f in ([entry['swing_frame'],*entry['twist_frames']] if 'swing_frame' in entry else [entry['frame_max']]):
            picks.add(f'{name}:{round((f-1)*30/24)}')
picks.update(f'Running:{f}' for f in range(0,23,2)); picks.update(f'Fidget:{f}' for f in [0,6,12,18,26,37,45,55,66])
run('g4_weights.py',P/'work/rig_gated_candidate.blend','final',*sorted(picks))
run('jerk_probe.py',P/'work/rig_gated_candidate.blend','Standing','Walking','Running','Hit','Death','Fidget')
for view in ['front','left','back']:
    run('clip_sheet.py',P/'work/rig_gated_candidate.blend',P/f'review/gated_{view}',view,8,'Fidget','Running','Hit','Death')
