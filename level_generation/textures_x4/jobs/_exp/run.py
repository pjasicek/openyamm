import sys, json, concurrent.futures
sys.argv=['x']; sys.path.insert(0,'.')
import tex
from pathlib import Path
inv=tex.inventory()
J=Path('jobs/_exp')
mats={}
for jp in Path('jobs').glob('2026*/job.json'):
    for m,r in json.load(open(jp))['requests'].items(): mats[r['name']]=r.get('material','')
work=[]
for name in ['cvdor3','bemtila','t1f1','swcirc2','d2wlbctr','beemdorc']:
    for blur in (1.2,2.0):
        e=dict(inv['mm6/'+name]); key=f'{name}_b{blur}'
        tex.make_reference(e, J/'refs'/f'{key}.png', blur=blur)
        work.append((key,e,mats.get(name,'')))
def go(item):
    key,e,mat=item
    prompt=tex.build_prompt({**e,'material':mat})
    (J/'prompts'/f'{key}.txt').write_text(prompt)
    worker=tex.WORKER_PROMPT.format(prompt=prompt,target=J/'raw'/f'{key}.png',alpha='')
    import subprocess
    with open(J/'raw'/f'{key}.log','w') as s:
        subprocess.run(['codex','exec','--json','-s','workspace-write','-C',str(J.resolve()),'--skip-git-repo-check','-i',str((J/'refs'/f'{key}.png').resolve())],input=worker,text=True,stdout=s,stderr=subprocess.STDOUT,timeout=900)
    return key,(J/'raw'/f'{key}.png').exists()
with concurrent.futures.ThreadPoolExecutor(10) as p:
    for r in p.map(go,work): print(r,flush=True)
