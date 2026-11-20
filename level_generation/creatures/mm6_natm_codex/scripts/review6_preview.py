"""Update existing review GLBs with only the final Attack action; keep their accepted pixels."""
import copy,sys,json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,write_glb,accessor_array,append_accessor
s,sb=read_glb(P/'export/mm6_natm.glb');sa=next(a for a in s['animations']if a['name']=='Attack')
paths=list((P/'review/viewer').glob('mm6_natm_?.glb'))+list((P/'review/runtime').glob('*.glb'))
for path in paths:
 d,b=read_glb(path);before=bytes(b);names={n['name']:i for i,n in enumerate(d['nodes'])if 'name'in n};a=copy.deepcopy(sa);accessors={}
 for sampler in a['samplers']:
  for key in ['input','output']:
   idx=sampler[key]
   if idx not in accessors:
    accessors[idx]=append_accessor(d,b,accessor_array(s,sb,idx),s['accessors'][idx],0);d['bufferViews'][-1].pop('target',None)
    for extent in ['min','max']:
     if extent in s['accessors'][idx]:d['accessors'][-1][extent]=s['accessors'][idx][extent]
   sampler[key]=accessors[idx]
 for c in a['channels']:c['target']['node']=names[s['nodes'][c['target']['node']]['name']]
 d['animations']=[a if old['name']=='Attack'else old for old in d['animations']];assert bytes(b[:len(before)])==before;write_glb(path,d,b)
f=P/'review/viewer/manifest.json';m=json.loads(f.read_text());old=m['clips']['Attack']['duration'];m['clips']['Attack']['duration']=55/48;m['clips']['Attack']['provenance']+=' Round 6 smooths the late body drive; synchronized recovery remains 12 frames.'
for a in m['clips']['Attack']['anchors']:a['time']*=55/48/old
m['revision']='mm6_natm_codex_review_round_6'
for model in m['models']:
 model['revision']=m['revision'];path=P/'review/viewer'/model['url'].split('?')[0];h=hashlib.sha256(path.read_bytes()).hexdigest();model['sha256']=h;model['url']=path.name+'?v='+h[:12]
f.write_text(json.dumps(m,indent=2)+'\n');print('UPDATED_PREVIEWS',len(paths))
