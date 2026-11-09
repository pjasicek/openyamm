from pathlib import Path
import sys,runpy,json,bpy
p=Path(__file__).resolve().parents[1];src=str(p/'work/reduced.blend');clips=['Standing','Walking','Running','Attack','Hit','Fidget','Death','Dead']
def run(name,*args):
 path=p/'scripts'/name;sys.argv=[str(path),'--',*map(str,args)];runpy.run_path(str(path),run_name='__main__')
run('audit_motion.py',src)
run('check_contacts.py',src,*clips)
run('hand_frame_check.py',src)
run('g5_hand_stretch.py',src,*clips)
run('jerk_probe.py',src,*clips)
run('sole_probe.py',src,*clips)
run('proportions.py','target',src,'Rig','Body',p/'work/bone_map.json')
report=json.loads((p/'review/animation/measurements.json').read_text())
picks=sorted({n+':'+str(int(v[r]['frame'])) for n,v in report.items() for r in ('hands','arms')})
run('g4_weights.py',src,'final',*picks)
run('export_preview.py')
