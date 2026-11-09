"""Run under the stage lock; replace only the two Bulwark rows and its model source."""
import copy,json
from pathlib import Path
import yaml
P=Path('level_generation/creatures/hes_bulwark_codex');gate=json.loads((P/'review/final_gates.json').read_text());assert len(gate['lods'])==4
f=Path('level_generation/projects/hesper_stage/monsters.yml');s=f.read_text();before=yaml.safe_load(s);tree=yaml.compose(s)
key=next(k.value for k,v in tree.value if isinstance(v,yaml.SequenceNode) and any(isinstance(n,yaml.MappingNode) and any(a.value=='id' for a,b in n.value) for n in v.value));seq=next(v for k,v in tree.value if k.value==key)
expected=copy.deepcopy(before);changes=[];settings={10107:'hes_bulwark',10141:'hes_bulwark_coupled'}
for node,row,wanted in zip(seq.value,before[key],expected[key]):
 if row['id'] not in settings:continue
 wanted['binding']={'from':str(P/'integration/actors.yml'),'entry':settings[row['id']]};wanted['height']=384;wanted['radius']=gate['radius_world']
 text=yaml.safe_dump(wanted,default_flow_style=True,sort_keys=False,width=115).strip().replace('\n','\n    ');changes.append((node.start_mark.index,node.end_mark.index,text))
assert len(changes)==2
for a,b,t in sorted(changes,reverse=True):s=s[:a]+t+s[b:]
name='hes_bulwark.glb';source=str(P/'export/hes_bulwark.glb')
if name not in before['models']:s=s.replace('models:\n','models:\n  '+name+': '+source+'\n',1)
else:assert before['models'][name]==source
expected['models'][name]=source;assert yaml.safe_load(s)==expected
f.write_text(s);(P/'review/stage_rows.json').write_text(json.dumps({'ids':list(settings),'height':384,'radius':gate['radius_world'],'other_rows_unchanged':True,'tactics_preserved':True},indent=2)+'\n')
print('Updated only Bulwark rows 10107/10141 and the shared model source.')
