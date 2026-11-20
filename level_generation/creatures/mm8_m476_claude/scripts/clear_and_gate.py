from pathlib import Path
import runpy,sys,os,json
p=Path(__file__).resolve().parents[1]
def run(name,*args):
 s=p/'scripts'/name;sys.argv=[str(s),'--',*map(str,args)];runpy.run_path(str(s),run_name='__main__')
run('arm_clearance.py')
os.environ['FA']='0.6';os.environ['FA_RAMP']='0.15,0.85'
run('twist_bones.py',p/'work/motion_clear.blend',p/'work/motion_twist.blend')
run('apply_grip.py',p/'work/motion_twist.blend',p/'work/motion_grip.blend')
run('smooth_thumb_webs.py')
run('reduce_rigged.py',p/'work/motion_grip_smooth.blend',p/'work/rig_v5.blend')
run('attach_club.py')
run('check_contacts.py')
r=json.loads((p/'work/contacts_v1.json').read_text());assert not any(v['depth_m']>.005 for a in r.values() for v in a.values()),'Contact suspects require review'
run('export_uploads.py')
