from pathlib import Path
import json,yaml,shutil
P=Path(__file__).resolve().parents[1];out=P/'review/ingame';scale=json.loads((P/'work/scale.json').read_text())['runtime_scale'];fixture=Path(json.loads((out/'fixture.json').read_text())['assets_root']);shutil.copy(P/'export/mm8_m624_runtime_lod0.glb',fixture/'worlds/mm8/models/m624_review_assembly.glb')
for place,position in [('in',(1200,-2935,-47)),('out',(-4200,3180,1))]:
 steps=[{'expect':'gameplay'},{'wait':1},{'key':'`'},{'text':f'model spawn worlds/mm8/models/m624_review_assembly.glb {position[0]} {position[1]} {position[2]} {scale} .15'},{'key':'Return'}]
 poses=[('Standing',.4),('Walk',.2),('Walk',.6),('Running',.3),('Attack',.65),('Attack',1.),('Cast',.95),('Hit',.18),('Fidget',.7),('Death',.55),('Death',1.1),('Dead',.5)]
 for k,(clip,t)in enumerate(poses):
  if k:steps.append({'key':'`'})
  for command in [f'model play 0 {clip} once','model pause 0',f'model scrub 0 {t}']:steps.extend([{'text':command},{'key':'Return'}])
  steps.extend([{'key':'`'},{'wait':.1},{'capture':f'{clip}-{t:.3f}'}])
 steps.extend([{'key':'`'},{'text':'model stop all'},{'key':'Return'},{'text':f'actor spawn 169 1 {position[0]} {position[1]} {position[2]}'},{'key':'Return'},{'key':'`'},{'wait':.8},{'capture':'hostile-approach'},{'wait':3},{'capture':'hostile-combat'},{'key':'`'},{'text':'actor damage last 1'},{'key':'Return'},{'key':'`'},{'wait':.1},{'capture':'hostile-hit'},{'key':'`'},{'text':'actor kill 2000'},{'key':'Return'},{'key':'`'},{'wait':.4},{'capture':'hostile-death'},{'wait':2},{'capture':'hostile-remains'}])
 steps=[{'console':s['text']}if'text'in s else s for s in steps if'key'not in s]
 (out/f'{place}_actions.yml').write_text(yaml.safe_dump({'output_dir':f'/tmp/m624-actions-{place}','exit':True,'steps':steps},sort_keys=False))
