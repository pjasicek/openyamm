from pathlib import Path
import subprocess,json
p=Path(__file__).resolve().parents[1];url=json.loads((p/'work/viewer_server.json').read_text())['url'];out=p/'review/round4/browser';out.mkdir(exist_ok=True,parents=True)
r=subprocess.run(['node',str(p.parent/'claude_shared/check_viewer.mjs'),url],text=True,capture_output=True,check=True)
(p/'review/viewer_check.json').write_text(r.stdout);print('VIEWER CHECK PASS',flush=True)
specs=[]
for tier in 'abc':
 specs.extend([f'tier_{tier}:Standing:0:front:body:::sor1_{tier}',f'collar_{tier}:Standing:0:front:head:0,1.45,0.80:0,1.43,0:sor1_{tier}'])
for view in ['front','left','back','quarter']:
 specs.append(f'robe_{view}:Standing:0:{view}:body:::sor1_c')
specs += ['robe_close:Standing:0:front:body:0,.75,1:0,.75,0:sor1_c','hem_close:Standing:0:front:body:0,.22,.8:0,.22,0:sor1_c','cast:Cast:.7375:quarter:body:::sor1_c','attack:Attack:1.220833:quarter:body:::sor1_c']
subprocess.run(['node',str(p/'scripts/viewer_shots.mjs'),url,str(out),*specs],check=True)
print('BROWSER REVIEW PASS',len(specs),'stills',flush=True)
