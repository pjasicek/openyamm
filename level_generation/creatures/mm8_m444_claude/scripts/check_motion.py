from pathlib import Path
import runpy,sys,os
p=Path(__file__).resolve().parents[1]
def run(name,args):
 sys.argv=[str(p/'scripts'/name),'--']+[str(x) for x in args];runpy.run_path(str(p/'scripts'/name),run_name='__main__')
acts=['Standing','Walking','Running','Attack','Hit','Cast','Death','Fidget']
run('g4_weights.py',[p/'work/rig_v5.blend','pilots']+[f'{a}:{f}' for a,frames in [('Attack',[0,8,16,24,32,40]),('Running',[0,5,11,16]),('Cast',[0,10,20]),('Hit',[4,8])] for f in frames])
run('g5_hand_stretch.py',[p/'work/rig_v5.blend']+acts)
os.environ['STEP']='0.5';run('sole_probe.py',[p/'work/rig_v5.blend']+acts)
