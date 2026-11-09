from pathlib import Path
import runpy,sys,json
p=Path(__file__).resolve().parents[1]
s=p/'scripts/finger_weights.py';sys.argv=[str(s),'--',str(p/'work/rig_v1.blend'),str(p/'work/rig_weighted.blend')];runpy.run_path(str(s),run_name='__main__')
selection=json.loads((p/'review/motion/selection.json').read_text())
items=[v['file']+':'+v['clip']+':'+role for role,v in selection.items() if role!='review']
s=p/'scripts/retarget.py';sys.argv=[str(s),'--',str(p/'work/rig_weighted.blend'),str(p/'work/motion_v1.blend'),*items];runpy.run_path(str(s),run_name='__main__')
