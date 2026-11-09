"""Package single-palette native actor."""
import subprocess,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
subprocess.run([sys.executable,str(ROOT.parent/'mm6_peasants/package_family.py'),'mcac'],check=True)
p=ROOT/'manifest.json';m=json.loads(p.read_text());m['recolor_model']='exact_base_bypass_v1';m['recolor']={'model':'exact_base_bypass_v1','operation':'Single native palette; no recoloring; preserve base RGBA exactly.'};p.write_text(json.dumps(m,indent=2)+'\n')

scope=json.loads((ROOT/'native_scope.json').read_text())
assert scope['native_bindings']['649']==scope['native_bindings']['650']==scope['native_bindings']['651']
assert all(s['size']==[256,256] for s in scope['sources'].values())
assert all('Center' in step['native_flags'] for action in m['animations'].values() for steps in action['views'].values() for step in steps)
m['logical_pivot']=[128,128];m['anchor']='center'
m['descriptor_aliases']={'650':649,'651':649}
m['native_descriptor_bindings']=scope['native_bindings']
for n,f in m['frames'].items():f['source']=Path(scope['sources'][n]['path']).name
m['native_endpoint_policy']={'sparse_exact_2x':['mcacdm0','mcacdn0','mcacdp0'],'empty':['mcacdq0','mcacdr0'],'reason':'Final native decay has 261, 25 and 2 pixels, then zero. Generated remnants were enlarged/filled; exact endpoints retained.'}
p.write_text(json.dumps(m,indent=2)+'\n')
sp=ROOT/'sources.json';source=json.loads(sp.read_text());source.update(logical_pivot=[128,128],anchor='center; all native sources 256x256, Center flag, offsets [0,0]');sp.write_text(json.dumps(source,indent=2)+'\n')
vp=ROOT/'validation.json';v=json.loads(vp.read_text());v['center_anchor_verified']=True;v['descriptor_aliases_verified']=True
for n in ['mcacdm0','mcacdn0','mcacdp0','mcacdq0','mcacdr0']:
 from PIL import Image
 import numpy as np
 native=Image.open(ROOT/'native'/f'{n}.png').resize((512,512),Image.Resampling.NEAREST)
 enhanced=Image.open(ROOT/'aligned_2x'/f'{n}.png')
 assert np.array_equal(np.array(native)[:,:,3],np.array(enhanced)[:,:,3]),n
v['native_decay_endpoint_alpha_exact']=True
vp.write_text(json.dumps(v,indent=2)+'\n')
