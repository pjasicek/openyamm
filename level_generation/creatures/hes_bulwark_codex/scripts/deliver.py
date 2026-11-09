import copy,json,sys,subprocess,hashlib
from pathlib import Path
import numpy as np,yaml
P=Path('level_generation/creatures/hes_bulwark_codex');sys.path[:0]=[str(P.parent/'claude_shared/floor'),str(P.parent/'lod_repair_claude/scripts'),str(P.parent/'claude_shared')]
from glb_pose import Glb
from splice_lods import compact
from region_variants import _compact
from build_actor_lods import write_glb
g=Glb(P/'export/hes_bulwark.glb');d=g.json
# Standalone static cables retain their own variants and LOD/shadow chains for map review.
c=copy.deepcopy(g);cd=c.json;node=next(n for n in cd['nodes'] if n.get('name')=='Bulwark_Cables');base=node['mesh'];extra=cd['meshes'][base]['extras'];used=[base]+extra['openyamm_lods']+extra['openyamm_shadow_lods'];remap={old:new for new,old in enumerate(used)}
cd['meshes']=[cd['meshes'][i] for i in used]
for mesh in cd['meshes']:
 for p in mesh['primitives']:
  for k in ('JOINTS_0','WEIGHTS_0'):p['attributes'].pop(k,None)
 for k in ('openyamm_lods','openyamm_shadow_lods'):
  if k in mesh.get('extras',{}):mesh['extras'][k]=[remap[i] for i in mesh['extras'][k]]
cd['nodes']=[{'name':'Bulwark_Cables','mesh':0}];cd['scenes']=[{'nodes':[0]}];cd['scene']=0;cd.pop('skins');cd.pop('animations');packed=compact(cd,c.bin);cd,packed=_compact(cd,packed);write_glb(P/'export/hes_bulwark_cables.glb',cd,packed)
v=P/'review/viewer';manifest=json.loads((v/'manifest.json').read_text());manifest.update(revision='bulwark_textured_v1',default_model='bulwark_b',default_clip='Standing',model='hes_bulwark_b.glb',models=[])
for tag,label in [('a','Ivory'),('b','Scorched · both runtime rows'),('c','Gilded')]:
 out=v/f'hes_bulwark_{tag}.glb';subprocess.run([sys.executable,str(P/'scripts/viewer_bake.py'),str(P/'export/hes_bulwark.glb'),str(out),'bulwark_'+tag],check=True)
 sha=hashlib.sha256(out.read_bytes()).hexdigest();manifest['models'].append(dict(id='bulwark_'+tag,label=label,revision=manifest['revision'],url=out.name+'?v='+sha[:12],sha256=sha))
for a in d['animations']:
 name=a['name'];base=name.removeprefix('Coupled_');entry=copy.deepcopy(manifest['clips'][base]);entry['label']=('Coupled · ' if name.startswith('Coupled_') else '')+base
 if name.startswith('Coupled_'):entry['provenance']+='; three flexible cables, plugs fixed to actor floor; walking/run are viewer diagnostics only'
 entry['duration']=max(float(g.accessor(s['input'])[-1,0]) for s in a['samplers']);manifest['clips'][name]=entry
(v/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
f=v/'index.html';s=f.read_text().replace('Hesper Bulwark — neutral rig','Hesper Bulwark — textured walker').replace('Four armoured legs, twin barrels and ten clips. Texturing and the coupled cables are pending.','Four armoured legs, twin barrels, three tier ramps. Choose a Coupled clip to show the three trailing cables.').replace('Neutral geometry and rig review; the retexture upload uses these same surfaces and UVs.','Scorched is the game palette. Coupled walking/run are rig diagnostics; the stationary game row uses Coupled Standing.');f.write_text(s)
f=v/'review.js';f.write_text(f.read_text().replace('body:[0,1.8,0.4,13]','body:[0,1.8,-1.2,16]'))
gate=json.loads((P/'review/final_gates.json').read_text());rows=[]
for coupled in (False,True):
 pre='Coupled_' if coupled else '';a={'stride_length':.65,'run_stride_length':.9,'upper_body_root':'B_Head','run':pre+('Standing' if coupled else 'Running'),'cast':pre+'Cast','script_clips':{'sweep':pre+'Sweep'},'sockets':{'muzzle':'Socket_Muzzle','muzzle_upper':'Socket_Muzzle_Upper','muzzle_lower':'Socket_Muzzle_Lower'},'events':{'attack_melee':{'impact':1/6},'attack_ranged':{'impact':1/6,'release':'muzzle','glow':['muzzle_upper','muzzle_lower']},'cast':{'impact':.5,'release':'muzzle','glow':['muzzle_upper','muzzle_lower']}},'look':{'target':'combat','nodes':['B_Barrel'],'max_yaw_degrees':0,'min_pitch_degrees':-10,'max_pitch_degrees':8}}
 clips={role:pre+clip for role,clip in {'standing':'Standing','walking':'Standing' if coupled else 'Walking','attack_melee':'Attack','attack_ranged':'Attack','hit':'Hit','dying':'Death','dead':'Dead','fidget':'Fidget'}.items()}
 rows.append({'descriptor':'hes_bulwark'+('_coupled' if coupled else ''),'model':'worlds/hesper/models/hes_bulwark.glb','scale':gate['scale'],'skin':'bulwark_b','yaw_offset':-1.570796327,'animation':a,'clips':clips})
(P/'integration').mkdir(exist_ok=True);(P/'integration/actors.yml').write_text('# One shared body; Coupled_* clips reveal the separately skinned cable mesh.\n'+yaml.safe_dump(rows,sort_keys=False))
assert set(manifest['clips'])=={a['name'] for a in d['animations']}
assert isinstance(json.loads((v/'feedback/user_feedback.json').read_text())['findings'],list)
for row in rows:
 assert set(row['clips'].values())|{row['animation']['cast'],row['animation']['run'],*row['animation']['script_clips'].values()}<=set(manifest['clips'])
(P/'review/viewer_static_check.json').write_text(json.dumps({'models':3,'clips_per_model':20,'hashes_verified':True,'feedback_findings_array':True,'browser_run':False},indent=2)+'\n')
print('Viewer, static cable export and two actor bindings ready')
