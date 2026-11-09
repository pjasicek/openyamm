from pathlib import Path
import runpy,sys,json
p=Path(__file__).resolve().parents[1]
sys.argv=['meshy_joints.py','--',str(p/'meshy/rig_v1/result_rigged_character_glb_url.glb'),str(p/'work/step1.blend')];runpy.run_path(str(p/'scripts/meshy_joints.py'),run_name='__main__')
d=json.loads((p/'work/meshy_joints.json').read_text());d['height_m']=1.7;(p/'work/meshy_joints.json').write_text(json.dumps(d,indent=2))
sys.argv=['joint_xray.py','--',str(p/'work/step1.blend'),'Body',str(p/'work/meshy_joints.json'),str(p/'review/joints_meshy'),str(p/'work/joints.json')];runpy.run_path(str(p/'scripts/joint_xray.py'),run_name='__main__')
