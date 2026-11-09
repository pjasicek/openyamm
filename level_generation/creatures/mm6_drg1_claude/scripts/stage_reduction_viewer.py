from pathlib import Path
import json,sys,hashlib
p=Path('level_generation/creatures/mm6_drg1_claude');r=p/'review/reduction_v7';v=p/'review/reduction_v7_viewer';step=int(sys.argv[1]);f=r/f'step_{step:02d}.glb';sys.path.insert(0,'tools');from merge_head_material import read_glb,write_glb
d,b=read_glb(f);fire=next(m for m in d['materials'] if m['name']=='DrakeDeathFlames');fire.pop('emissiveTexture',None);fire['emissiveFactor']=[0,0,0];fire.setdefault('extensions',{})['KHR_materials_unlit']={}
if 'KHR_materials_unlit' not in d.setdefault('extensionsUsed',[]):d['extensionsUsed'].append('KHR_materials_unlit')
write_glb(f,d,b)
s=json.loads((v/'manifest.json').read_text());s['models']=[x for x in s['models'] if x['id']!=f'step_{step:02d}'];n=json.loads((r/f'step_{step:02d}.json').read_text())['triangles'];s['models'].append({'id':f'step_{step:02d}','label':f'Step {step}: {n} body tris','url':f'../reduction_v7/step_{step:02d}.glb','revision':f'v7-step-{step}'});s['default_model']=f'step_{step:02d}';
for model in s['models']:model['sha256']=hashlib.sha256((v/model['url']).resolve().read_bytes()).hexdigest()
(v/'manifest.json').write_text(json.dumps(s,indent=2)+'\n')
