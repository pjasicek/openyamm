"""Install the current Gargoyle and retain the runtime's required back-face split in the delivery copy."""
from pathlib import Path
import runpy,shutil,sys
P=Path(__file__).resolve().parents[1];installed=Path('assets_dev/worlds/mm6/models/mm6_gar.glb')
shutil.copyfile(P/'export/mm6_gar.glb',installed);installed.chmod(0o644)
sys.argv=['model_backface_split','--report',str(P/'work/backface_split.json'),str(installed)]
runpy.run_path('tools/model_backface_split.py',run_name='__main__')
shutil.copyfile(installed,P/'export/mm6_gar.glb')
