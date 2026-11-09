"""Replace only the four Sentinel row bindings and register their one shared export."""
import copy,json
from pathlib import Path
import yaml
P=Path('level_generation/creatures/hes_sentinel_codex')
assert json.loads((P/'review/sentinel_final_gates.json').read_text())['factor_only_emission']
f=Path('level_generation/projects/hesper_stage/monsters.yml');s=f.read_text();before=yaml.safe_load(s);tree=yaml.compose(s)
key=next(k.value for k,v in tree.value if isinstance(v,yaml.SequenceNode) and any(isinstance(n,yaml.MappingNode) and any(a.value=='id' for a,b in n.value) for n in v.value))
seq=next(v for k,v in tree.value if k.value==key)
settings={10055:('hes_sentinel',160,99),10056:('hes_heavy_sentinel',192,119),10057:('hes_crown_sentinel',208,129),10144:('hes_throne_turret',208,129)}
changes=[];expected=copy.deepcopy(before)
for node,row,wanted in zip(seq.value,before[key],expected[key]):
 if row['id'] not in settings:continue
 entry,height,radius=settings[row['id']]
 wanted['binding']['from']='level_generation/creatures/hes_sentinel_codex/integration/actors.yml';wanted['binding']['entry']=entry
 wanted['height']=height;wanted['radius']=radius
 # Preserve tactics; new geometry needs whole-body traverse instead of barrel yaw lead.
 if 'look' in wanted['binding'].get('animation',{}):wanted['binding']['animation']['look']['max_yaw_degrees']=0
 text=yaml.safe_dump(wanted,default_flow_style=True,sort_keys=False,width=115).strip()
 text=text.replace('\n','\n    ')
 changes.append((node.start_mark.index,node.end_mark.index,text))
assert len(changes)==4
for a,b,t in sorted(changes,reverse=True):s=s[:a]+t+s[b:]
model='  hes_sentinel.glb: level_generation/creatures/hes_sentinel_codex/export/hes_sentinel.glb\n'
assert 'hes_sentinel.glb' not in before['models'];s=s.replace('models:\n','models:\n'+model,1)
expected['models']['hes_sentinel.glb']='level_generation/creatures/hes_sentinel_codex/export/hes_sentinel.glb'
assert yaml.safe_load(s)==expected
f.write_text(s)
(P/'review/sentinel_stage_rows.json').write_text(json.dumps({'ids':list(settings),'height_radius':{str(k):list(v[1:]) for k,v in settings.items()},'other_rows_unchanged':True,'tactics_preserved':True},indent=2)+'\n')
print('Updated only Sentinel rows 10055/10056/10057/10144 and their shared model source.')
