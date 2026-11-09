"""Check final runtime files, prove far repair retained the measured mesh/animation data, and prepare review."""
import hashlib,json,subprocess,sys
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];S=P/'scripts';R=P.parents[2];sys.path.insert(0,str(P.parent/'claude_shared/floor'))
from glb_pose import Glb
before=Glb(P/'work/hes_forgemaster_near.glb');after=Glb(P/'export/hes_forgemaster.glb')
for name in ('Lancer','Lancer_LOD1'):
 a=next(m for m in before.json['meshes'] if m['name']==name);b=next(m for m in after.json['meshes'] if m['name']==name);assert len(a['primitives'])==len(b['primitives'])
 for pa,pb in zip(a['primitives'],b['primitives']):
  assert pa['attributes'].keys()==pb['attributes'].keys()
  for key in pa['attributes']:assert np.array_equal(before.accessor(pa['attributes'][key]),after.accessor(pb['attributes'][key])),(name,key)
  assert np.array_equal(before.accessor(pa['indices']),after.accessor(pb['indices']))
a={x['name']:x for x in before.json['animations']};b={x['name']:x for x in after.json['animations']};assert a.keys()==b.keys()
changed=[]
for name in a:
 ca={tuple(sorted(c['target'].items())):a[name]['samplers'][c['sampler']] for c in a[name]['channels']};cb={tuple(sorted(c['target'].items())):b[name]['samplers'][c['sampler']] for c in b[name]['channels']};assert ca.keys()==cb.keys()
 for target in ca:
  node=after.json['nodes'][dict(target)['node']]['name'];path=dict(target)['path'];same=all(np.array_equal(before.accessor(ca[target][key]),after.accessor(cb[target][key])) for key in ('input','output'))
  if not same:
   assert name in ('Forge_Death','Forge_Dead') and path=='translation' and node in ('B_Pelvis','Thunder_Maul'),(name,node,path)
   changed.append([name,node,path])
assert len(changed)==4
steps=[]
for animation in after.json['animations']:
 if not animation['name'].startswith('Forge_'):continue
 for channel in animation['channels']:
  node=after.json['nodes'][channel['target']['node']]['name']
  if channel['target']['path']!='rotation' or 'Twist' not in node:continue
  sampler=animation['samplers'][channel['sampler']];q=after.accessor(sampler['output']);values=np.degrees(2*np.arccos(np.clip(np.abs(np.sum(q[:-1]*q[1:],axis=1)),0,1)))
  assert values.max()<15,(animation['name'],node,float(values.max()))
  steps.append({'clip':animation['name'],'node':node,'max_step_degrees':float(values.max())})
(P/'review/forge_runtime_twist_continuity.json').write_text(json.dumps(steps,indent=2)+'\n')
record={'lod0_lod1_attributes_and_indices_identical':True,'all_animation_samples_identical_except_recorded_floor_channels':True,'changed_channels':changed,'source_sha256':hashlib.sha256((P/'work/hes_forgemaster_near.glb').read_bytes()).hexdigest(),'final_sha256':hashlib.sha256((P/'export/hes_forgemaster.glb').read_bytes()).hexdigest()}
(P/'review/forge_far_preservation.json').write_text(json.dumps(record,indent=2)+'\n')
contacts=json.loads((P/'review/runtime_equipment_contacts_forge_review.json').read_text());lancer=json.loads((P/'review/runtime_equipment_contacts_lancer_review2.json').read_text());assert set(contacts)=={'hes_forgemaster'} and set(lancer)=={'hes_lancer'};contacts.update(lancer)
assert not any(frames for clips in contacts.values() for parts in clips.values() for frames in parts.values());(P/'review/runtime_equipment_contacts.json').write_text(json.dumps(contacts,indent=2)+'\n')
assert hashlib.sha256((P.parent/'hes_kreegan_claude/export/hes_kreegan.glb').read_bytes()).hexdigest()=='38cc3345adbebe78ee535f2430886ee52899270951767a938ede58094eafbc11'
def run(name,*args):
 print('FINAL_CHECK',name,flush=True);subprocess.run(['python3',str(S/name),*map(str,args)],check=True)
run('forge_slam_runtime_gate.py')
run('validate_runtime.py')
run('lod_atlas_check.py',*[P/f'export/{n}.glb' for n in ('hes_ion_lance','hes_ion_lance_twin','hes_lancer_graft','hes_thunder_maul')])
run('viewer.py');run('check_lancer_viewer.py')
files=[P/f'export/{n}.glb' for n in ('hes_lancer','hes_ion_lance','hes_ion_lance_twin','hes_lancer_graft','hes_forgemaster','hes_thunder_maul','hes_lancer_lod0','hes_lancer_twin_lod0','hes_forgemaster_lod0')]+list((P/'review/viewer').glob('*.glb'))
result=subprocess.run(['python3',str(R/'level_generation/decorations/mm8_3d/animated/scripts/check_winding.py'),*map(str,files)],check=True,capture_output=True,text=True);(P/'review/winding.txt').write_text(result.stdout);print(result.stdout,flush=True)
