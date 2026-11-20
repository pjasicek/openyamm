import runpy,subprocess,json,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];config=json.loads((P/'work/round5/config.json').read_text());step=config['step']
runpy.run_path(str(P/'scripts/round5_project_bake.py'),run_name='__main__')
subprocess.run(['/usr/bin/python3',str(P/'scripts/round5_tiers.py'),f'baked{step}'],check=True)
ns=runpy.run_path(str(P/'scripts/round5_render.py'),run_name='renderer');None if (P/'review/round5/reference/dwa1_a_Standing_7.png').exists()else ns['render'](P/'work/round4_before/work/export_reimport.blend',P/'review/round5/reference',P/'work/round5/source')
ns['render'](P/f'work/round5/baked{step}/candidate.blend',P/f'review/round5/candidate{step}',P/f'work/round5/baked{step}')
if config.get('gates',True):runpy.run_path(str(P/'scripts/round5_trial_gates.py'),run_name='__main__')
