"""Solve and inspect the grip, then render the motion pilot from two useful views."""
from pathlib import Path
import runpy, sys, os, json
p=Path(__file__).resolve().parents[1]; w=p/'work'
def run(n,args):
    s=p/'scripts'/n; sys.argv=[str(s),'--',*[str(a) for a in args]]
    runpy.run_path(str(s),run_name='__main__')
os.environ['R_HANDLE']='0.016'
os.environ['GRIP_RENDER']=str(p/'review/grip')
os.environ['GRIP_SCALE']='0.28'
run('grip_solve.py',[w/'fingered.blend','Attack','0'])
run('apply_grip.py',[w/'fingered.blend',w/'pilot.blend'])
picks=[f"{v['role']}:{v['frame']}" for v in json.load(open(w/'rom.json'))['stress_poses']]
run('g4_weights.py',[w/'pilot.blend','pilot',*picks])
roles=['Standing','Walking','Attack','Hit','Death','Fidget','Running']
for view in ('front','left'):
    run('clip_sheet.py',[w/'pilot.blend',p/'review/pilot'/view,view,'6',*roles])
run('g6_contacts.py',[w/'pilot.blend',*roles])
