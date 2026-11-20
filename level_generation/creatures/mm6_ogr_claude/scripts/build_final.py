"""Build and validate the Ogre package from the gated textured master; install only validated artifacts."""
from pathlib import Path
import runpy,subprocess,shutil
p=Path(__file__).resolve().parents[1]
runpy.run_path(str(p/'scripts/export_runtime.py'),run_name='__main__')
subprocess.run(['python3',str(p/'scripts/prepare_runtime.py')],check=True)
runpy.run_path(str(p/'scripts/build_lods.py'),run_name='__main__')
for name in ('finish_runtime.py','validate_runtime.py'):subprocess.run(['python3',str(p/'scripts'/name)],check=True)
for name in ('mm6_ogr.glb','mm6_ogr_sword.glb'):
 out=p.parents[2]/'assets_dev/worlds/mm6/models'/name
 shutil.copyfile(p/'export'/name,out);out.chmod(0o644)
