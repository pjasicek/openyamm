from pathlib import Path
from collections import Counter
import subprocess,json,yaml,re
ROOT=Path.cwd();P=ROOT/'level_generation/creatures/hes_overseer_codex';ids={10030,10031,10032,10102,10103}
results=[]
for f in sorted((ROOT/'level_generation/projects').glob('hesper_*/runtime/worlds/hesper/maps/*.scene.yml')):
 scene=yaml.safe_load(f.read_text());actors=scene.get('initial_state',{}).get('actors',[]);placed=Counter(a['monster_id'] for a in actors if a.get('monster_id')in ids)
 if not placed:continue
 stem=f.name.split('.')[0];mapfile=stem+('.odm' if '_out' in stem else '.blv')
 command=['flock','-s','output/hesper_stage/locks/engine_build.lock','flock','-s','output/hesper_stage/locks/stage.lock','./tools/run_game.sh','--isolated','overseers_'+stem,'--world','hesper','--map',mapfile,'--assets',str(ROOT/'output/hesper_stage/assets_editor_dev'),'--warmup','1','--seconds','3']
 try:r=subprocess.run(command,text=True,capture_output=True,timeout=120);output=r.stdout+r.stderr;code=r.returncode
 except subprocess.TimeoutExpired as e:output=str(e);code=124
 (P/'review'/f'smoke_{stem}.log').write_text(output)
 match=re.search(r'Isolated run: (.+)',output);run=Path(match.group(1)) if match else None
 game=(run/'game.log').read_text(errors='replace') if run and (run/'game.log').exists() else ''
 metadata=json.loads((run/'run.json').read_text()) if run and (run/'run.json').exists() else {}
 row={'map':mapfile,'placed_rows':dict(placed),'exit_code':code,'run_directory':str(run) if run else None,'status':metadata.get('status'),'error':metadata.get('error'),'model_load_errors':game.count('Actor model load failed') if metadata.get('status')=='completed' else None,'graphical_map_loaded':metadata.get('status')=='completed','passed':code==0 and metadata.get('status')=='completed' and 'Actor model load failed' not in game}
 results.append(row);(P/'review/desktop_smoke.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(row),flush=True)
