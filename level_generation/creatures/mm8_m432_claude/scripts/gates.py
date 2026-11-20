"""Run the shared deformation/contact probes on this exact assembled revision."""
import bpy,sys,runpy,os
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
src=P/os.environ.get('GATE_INPUT','work/rig_assembled.blend');acts=['Standing','Walking','Running','Attack','Hit','Cast','Fidget','Death']
bpy.ops.wm.open_mainfile(filepath=str(src));picks=[]
for n in acts:
    last=int(bpy.data.actions[n].frame_range[1]);picks.extend(f'{n}:{f}' for f in sorted(set([0,last]+list(range(0,last+1,4)))))
for script,args in [('g4_weights.py',[src,os.environ.get('GATE_LABEL','assembled'),*picks]),('g5_hand_stretch.py',[src,*acts]),('sole_probe.py',[src,*acts]),('jerk_probe.py',[src,*acts]),('g6_contacts.py',[src,*acts])]:
    print('RUN',script,flush=True);os.environ['STEP']='0.5';sys.argv=[script,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/script),run_name='__main__')
