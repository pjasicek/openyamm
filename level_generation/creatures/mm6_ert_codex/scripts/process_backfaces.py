import runpy
import sys
sys.argv=['tools/model_backface_split.py','--report','level_generation/creatures/mm6_ert_codex/work/backface_report.json','assets_dev/worlds/mm6/models/mm6_ert.glb']
runpy.run_path(sys.argv[0], run_name='__main__')
