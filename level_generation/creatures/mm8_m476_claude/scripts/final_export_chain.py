from pathlib import Path
import runpy,sys,subprocess
p=Path(__file__).resolve().parents[1];repo=p.parents[2]
def run(name,*args):
 s=p/'scripts'/name;sys.argv=[str(s),'--',*map(str,args)];runpy.run_path(str(s),run_name='__main__')
run('attach_club.py');run('check_contacts.py')
run('g5_hand_stretch.py',p/'work/rig_v5.blend','Standing','Walking','Running','Attack','Hit','Fidget','Death')
run('export_runtime.py')
subprocess.run(['/usr/bin/python3',str(repo/'tools/prepare_actor_glb.py'),str(p/'export/mm8_m476_lod0.glb'),str(p/'export/mm8_m476_prepared.glb')],check=True)
run('build_lods.py')
subprocess.run(['/usr/bin/python3',str(p/'scripts/finish_runtime.py')],check=True)
subprocess.run(['/usr/bin/python3',str(p/'scripts/viewer_tiers.py')],check=True)
