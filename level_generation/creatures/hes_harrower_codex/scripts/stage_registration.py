"""Replace only this project's four rows and model sources under the caller's exclusive stage lock."""
from pathlib import Path
import yaml,re,subprocess,sys,copy
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2];path=ROOT/'level_generation/projects/hesper_stage/monsters.yml'
text=path.read_text();before=yaml.safe_load(text);ids={10240,10241,10242,10147};models={f.name:str(f.relative_to(ROOT)) for f in sorted((P/'export').glob('*.glb'))}
assert len(models)==11,models
new_models={k:v for k,v in models.items() if k not in before['models']}
assert all(before['models'].get(k,v)==v for k,v in models.items())
text=text.replace('models:\n','models:\n'+''.join(f'  {k}: {v}\n' for k,v in new_models.items()),1)
for ident,tier in ((10240,'A'),(10241,'B'),(10242,'C')):
 pattern=rf'  - \{{id: {ident},.*?(?=\n  -|\n\n|\n  #|\nbehaviors:)'
 old=re.search(pattern,text,re.S);assert old,ident
 replacement=old.group().replace('level_generation/creatures/hes_kreegan_claude/integration/actors.yml','level_generation/creatures/hes_harrower_codex/integration/actors.yml').replace('entry: Trooper '+tier,'entry: Harrower '+tier)
 assert 'hes_harrower_codex' in replacement;text=text[:old.start()]+replacement+text[old.end():]
boss='  - {id: 10147, picture: hes_harrower Boss, reference: Demon C, height: 267, radius: 74,\n     binding: {from: level_generation/creatures/hes_harrower_codex/integration/actors.yml, entry: Huntmaster Vreth},\n     tactics: {post: {leash: 1300}}}\n'
existing=next((r for r in before['monsters'] if r['id']==10147),None)
if existing:
 pattern=r'  - \{id: 10147,.*?(?=\n  -|\n\n|\n  #|\nbehaviors:)';text,n=re.subn(pattern,boss.rstrip(),text,count=1,flags=re.S);assert n==1
else:
 marker='  - {id: 10107,';assert marker in text;text=text.replace(marker,boss+marker,1)
text=text.replace('# D7: Trooper Harrowers and native Robot Bulwark stand-ins.','# D7: Harrowers and native Robot Bulwark stand-ins; Vreth uses the shared Harrower body.')
text=text.replace("# The Crown's Blooding Ring (hesper_out4, HARROWERS.md): Huntmaster Vreth on the Trooper C body at x1.35\n  # (hesper_out4/vreth_standin.yml) until hes_harrower_codex stages his model; placed immobile, his post keeps him in", "# The Crown's Blooding Ring (hesper_out4, HARROWERS.md): Huntmaster Vreth, Harrower body at x1.35;\n  # placed immobile, his post keeps him in")
after=yaml.safe_load(text)
assert [r for r in before['monsters'] if r['id'] not in ids]==[r for r in after['monsters'] if r['id'] not in ids]
assert {k:v for k,v in before['models'].items() if k not in models}=={k:v for k,v in after['models'].items() if k not in models}
assert sum(r['id'] in ids for r in after['monsters'])==4
for k in before:
 if k not in ('models','monsters'):assert before[k]==after[k]
path.write_text(text)
with (P/'review/stage.log').open('w') as out:subprocess.run([sys.executable,str(ROOT/'level_generation/projects/hesper_stage/stage.py')],cwd=ROOT,stdout=out,stderr=subprocess.STDOUT,check=True)
print('Staged Harrowers rows 10240–10242 and 10147; other monster definitions preserved.')
