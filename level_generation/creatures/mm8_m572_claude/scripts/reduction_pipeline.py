from pathlib import Path
import runpy,sys,json,shutil
P=Path(__file__).resolve().parents[1];selected=None
for step in range(7,21):
 sys.argv=[str(P/'scripts/reduce_geometry.py'),'--',str(step)]
 runpy.run_path(str(P/'scripts/reduce_geometry.py'),run_name='__main__')
 d=json.loads((P/f'review/reduction/step_{step:02d}.json').read_text())
 if d['failed_checks']:break
 selected=step
assert selected is not None,'No passing reduction'
shutil.copy2(P/f'review/reduction/step_{selected:02d}.blend',P/'work/reduced.blend')
(P/'work/selected_reduction.json').write_text(json.dumps({'selected':selected,'last_attempt':step,'agent_visual':'pending'},indent=2))
print('SELECTED',selected,flush=True)
