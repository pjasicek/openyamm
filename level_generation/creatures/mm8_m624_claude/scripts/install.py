from pathlib import Path
import sys,subprocess,json,hashlib
P=Path(__file__).resolve().parents[1];receipt=[]
for name in ['mm8_m624']+['mm8_m624_'+sd for sd in ['l1','l2','l3','r1','r2','r3']]:
 source=P/f'export/{name}.glb';subprocess.run([sys.executable,'tools/install_model.py',str(source),'--world','mm8'],check=True)
 installed=Path(f'assets_source/worlds/mm8/models/{name}.glb');runtime=Path(f'assets_dev/worlds/mm8/models/{name}.glb');sha=hashlib.sha256(source.read_bytes()).hexdigest();assert hashlib.sha256(installed.read_bytes()).hexdigest()==sha
 receipt.append({'project':str(source),'source':str(installed),'source_sha256':sha,'runtime':str(runtime),'runtime_sha256':hashlib.sha256(runtime.read_bytes()).hexdigest()})
(P/'review/installation.json').write_text(json.dumps(receipt,indent=2)+'\n')
