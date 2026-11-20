"""The prescribed repair ladder, split at the authorized Blender-wrapper render boundary."""
import csv,hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];H=P/'lodrep'
MODEL=os.environ.get('MODEL','hes_lancer');assert MODEL in ('hes_lancer','hes_forgemaster')
W=P/f'work/lodrep_{MODEL}';SOURCE=P/f'work/{MODEL}_near.glb'
PY='/tmp/lancer_lod_venv/bin/python'
W.mkdir(exist_ok=True)
identity=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
record=W/'result.json'
result=json.loads(record.read_text()) if record.exists() else {'source':str(SOURCE),'source_sha256':identity,'node':'Lancer','steps':[],'passed':False,'chosen':None}
assert result['source_sha256']==identity,'Source changed; use a fresh repair directory'
def run(script,*args,python=PY):
 with (W/'wrapper_repair.log').open('a') as out:
  subprocess.run([python,str(H/script),*map(str,args)],check=True,stdout=out,stderr=subprocess.STDOUT)
if sys.argv[1]=='build':
 r2,r3=map(float,sys.argv[2:4]);step=f'r{round(r2*100)}_{round(r3*100)}';built=W/f'{step}.built.glb';baked=W/f'{step}.glb';folder=W/f'bake_{step}'
 shutil.copy2(SOURCE,W/'installed.glb')
 run('build_lods.py',SOURCE,'Lancer',built,f'2:{r2},3:{r3}')
 run('unwrap_lods.py',built,'Lancer',folder,'2:512,3:256')
 run('transfer_textures.py',built,'Lancer',folder)
 run('apply_bake.py',built,'Lancer',folder,baked,'2,3')
 run('lod_split.py',W/'audit',W/'installed.glb',baked,python='python3')
 result['pending']={'step':step,'ratios':[r2,r3]}
 record.write_text(json.dumps(result,indent=2)+'\n')
 print('RENDER_NEXT',W/'audit','installed,'+step,flush=True)
elif sys.argv[1]=='score':
 pending=result.pop('pending');step=pending['step'];audit=W/'audit'
 scored=subprocess.check_output(['python3','-I',str(H/'lod_score.py'),str(audit)],text=True)
 (audit/'scores.tsv').write_text(scored)
 table={(r['model'],int(r['lod'])):[float(r['outline_pct']),float(r['colour_diff'])] for r in csv.DictReader(scored.splitlines(),delimiter='\t')}
 entry={**pending,'installed':{k:table['installed',k] for k in (1,2,3)},'repaired':{k:table[step,k] for k in (1,2,3)}}
 entry['pass']={2:entry['repaired'][2][0]<=6 and entry['repaired'][2][1]<=max(16,entry['installed'][1][1]+3),3:entry['repaired'][3][0]<=13 and entry['repaired'][3][1]<=19.5}
 result['steps'].append(entry);result['passed']=all(entry['pass'].values());result['chosen']=step
 shutil.copytree(audit,W/f'audit_{step}',dirs_exist_ok=True)
 if result['passed']:shutil.copy2(W/f'{step}.glb',P/f'work/{MODEL}_far.glb')
 record.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(entry),flush=True)
else:raise ValueError(sys.argv[1])
