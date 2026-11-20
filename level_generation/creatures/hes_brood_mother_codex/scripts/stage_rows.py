"""Stage only the Brood Mother's model and binding; preserve concurrently edited Hesper entries."""
import fcntl,json,re,subprocess,sys
from pathlib import Path
import yaml
P=Path(__file__).resolve().parents[1];R=P.parents[2]
path=R/'level_generation/projects/hesper_stage/monsters.yml'
with open(R/'output/hesper_stage/locks/stage.lock','a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 text=path.read_text();before=yaml.safe_load(text)
 model='hes_brood_mother.glb';source='level_generation/creatures/hes_brood_mother_codex/export/'+model
 if model not in before['models']:text=text.replace('models:\n','models:\n  '+model+': '+source+'\n',1)
 else:assert before['models'][model]==source
 match=re.search(r'  - \{id: 10111,.*?(?=\n  - )',text,re.S);assert match
 entry=match.group();entry=re.sub(r'binding: \{from: [^,]+, entry: [^}]+\}', 'binding: {from: level_generation/creatures/hes_brood_mother_codex/integration/actors.yml, entry: hes_brood_mother}',entry,count=1)
 text=text[:match.start()]+entry+text[match.end():];after=yaml.safe_load(text)
 a=json.loads(json.dumps(before));b=json.loads(json.dumps(after));a['models'].pop(model,None);b['models'].pop(model,None)
 for obj in (a,b):
  rows=[x for x in obj['monsters'] if x['id']==10111];assert len(rows)==1;rows[0].pop('binding')
 assert a==b,'Unrelated stage input changed'
 path.write_text(text)
 with open(P/'review/stage.log','w') as log:
  result=subprocess.run([sys.executable,str(R/'level_generation/projects/hesper_stage/stage.py')],cwd=R,stdout=log,stderr=subprocess.STDOUT)
 print('stage.py exit',result.returncode);sys.exit(result.returncode)
