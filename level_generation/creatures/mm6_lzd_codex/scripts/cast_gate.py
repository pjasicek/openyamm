"""A distinct Cast clip must be an exact copy of the accepted bow-shot channels."""
import sys,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
from build_actor_lods import read_glb,accessor_bytes
d,b=read_glb(P/'export/mm6_lzd_raw.glb');clips={a['name']:a for a in d['animations']}
a,c=clips['Attack'],clips['Cast'];assert a['channels']==c['channels'];assert len(a['samplers'])==len(c['samplers'])
for x,y in zip(a['samplers'],c['samplers']):
 assert x.get('interpolation','LINEAR')==y.get('interpolation','LINEAR')
 for key in ['input','output']:assert accessor_bytes(d,b,x[key])==accessor_bytes(d,b,y[key])
release=json.loads((P/'review/ranged_release.json').read_text())
r={'passed':True,'choice':'b','exact_attack_copy':True,'samplers_checked':len(a['samplers']),'duration_seconds':json.loads((P/'export/export_info.json').read_text())['clips']['Cast'],'cast':{'impact_seconds':release['impact_seconds'],'socket':'Socket_Arrow','arrow_target_dot':release['impact_arrow_target_dot']}}
(P/'review/cast_gate.json').write_text(json.dumps(r,indent=2));info=json.loads((P/'export/export_info.json').read_text());info.update(cast_impact_seconds=release['impact_seconds'],cast_socket='Socket_Arrow');(P/'export/export_info.json').write_text(json.dumps(info,indent=2));print('CAST_COPY_GATE',r)
