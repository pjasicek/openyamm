from pathlib import Path
import runpy,sys,subprocess
P=Path(__file__).resolve().parents[1];W=P/'work'
def run(n,*args):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('transfer_uv.py',W/'master_settled.blend',P/'meshy/body_retexture_v1',W/'master_settled.blend')
run('uv_raster.py',W/'master_settled.blend','UVMap',1024)
subprocess.run(['python3',str(P/'scripts/compose_pirate_mage.py')],check=True)
run('export_final_lods.py')
run('deformation_gates.py')
