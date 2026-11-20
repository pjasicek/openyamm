import sys,os,json,shutil
from pathlib import Path
P=Path(__file__).resolve().parents[1]
os.chdir(P)
(P/'work/round2/joints_final.json').write_bytes((P/'work/joints_final.json').read_bytes())
for name in ['fit_fingers.py','finger_joints.py']:
 s=(P/'scripts'/name).read_text().replace("'work', 'joints_final.json'","'work', 'round2', 'joints_final.json'").replace("'work', 'fingers_fit.json'","'work', 'round2', 'fingers_fit.json'").replace("'work', 'finger_joints.json'","'work', 'round2', 'finger_joints.json'")
 sys.argv=[name,'--',str(P/'work/round2/bound_body.blend')]
 exec(compile(s,str(P/'scripts'/name),'exec'),{'__name__':'__main__','__file__':str(P/'scripts'/name)})
