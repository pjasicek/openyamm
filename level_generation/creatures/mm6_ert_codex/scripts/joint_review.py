import sys,runpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path('level_generation/creatures/mm6_bar1_claude/scripts').resolve()))
j=json.loads((P/'work/meshy_joints.json').read_text());j['height_m']=2.4
(P/'work/meshy_joints.json').write_text(json.dumps(j,indent=2))
sys.argv=['joint_xray','--',str(P/'work/step1.blend'),'Body',str(P/'work/meshy_joints.json'),str(P/'review/joints_meshy')]
runpy.run_path('level_generation/creatures/mm6_bar1_claude/scripts/joint_xray.py',run_name='__main__')
