"""Transplant the revised Attack while preserving every accepted mesh/map/other clip."""
from pathlib import Path
import copy, hashlib, json, sys, runpy
import numpy as np
P=Path(__file__).resolve().parents[1];E=P/'export';V5=P/'review/revisions/water_v5/export'
sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,write_glb,accessor_array,compact
source,sb=read_glb(E/'mm6_wel_lod0.glb')
attack=next(a for a in source['animations'] if a['name']=='Attack')
def fingerprint(d,b,part):
 h=hashlib.sha256()
 def add(value):h.update(value if isinstance(value,bytes) else json.dumps(value,sort_keys=True).encode())
 if part=='geometry':
  add(d['nodes']);add(d['materials']);add(d.get('extensions',{}))
  for mesh in d['meshes']:
   add(mesh.get('extras',{}))
   for p in mesh['primitives']:
    for name,i in sorted(p['attributes'].items()):add(name);add(accessor_array(d,b,i).tobytes())
    add(accessor_array(d,b,p['indices']).tobytes())
  for skin in d.get('skins',[]):add(skin['joints']);add(accessor_array(d,b,skin['inverseBindMatrices']).tobytes())
  for im in d['images']:
   v=d['bufferViews'][im['bufferView']];start=v.get('byteOffset',0);add(bytes(b[start:start+v['byteLength']]))
 else:
  a=next(x for x in d['animations'] if x['name']==part)
  for c in a['channels']:
   add((d['nodes'][c['target']['node']]['name'],c['target']['path']))
   s=a['samplers'][c['sampler']];add(s.get('interpolation','LINEAR'))
   for k in ['input','output']:add(accessor_array(d,b,s[k]).tobytes())
 return h.hexdigest()
reports=[]
for original in sorted(V5.glob('*.glb')):
 d,b=read_glb(original)
 if not d.get('animations'):continue
 before={n:fingerprint(d,b,n) for n in ['geometry']+[a['name'] for a in d['animations'] if a['name']!='Attack']}
 a=copy.deepcopy(attack);node_ids={n.get('name'):i for i,n in enumerate(d['nodes'])};accessors={}
 for c in a['channels']:c['target']['node']=node_ids[source['nodes'][c['target']['node']]['name']]
 for sampler in a['samplers']:
  for k in ['input','output']:
   old=sampler[k]
   if old not in accessors:
    acc=copy.deepcopy(source['accessors'][old]);values=accessor_array(source,sb,old);packed=values.tobytes();b.extend(b'\0'*(-len(b)%4))
    d['bufferViews'].append({'buffer':0,'byteOffset':len(b),'byteLength':len(packed)});b.extend(packed)
    acc['bufferView']=len(d['bufferViews'])-1;acc.pop('byteOffset',None);d['accessors'].append(acc);accessors[old]=len(d['accessors'])-1
   sampler[k]=accessors[old]
 index=next(i for i,x in enumerate(d['animations']) if x['name']=='Attack');d['animations'][index]=a
 d,b=compact(d,b)
 for n,h in before.items():assert h==fingerprint(d,b,n),(original.name,n)
 assert fingerprint(source,sb,'Attack')==fingerprint(d,b,'Attack')
 write_glb(E/original.name,d,b)
 reports.append({'file':original.name,'preserved':before,'attack_sha256':fingerprint(d,b,'Attack'),'sha256':hashlib.sha256((E/original.name).read_bytes()).hexdigest()})
(P/'review/attack_timing_v6/preservation.json').write_text(json.dumps(reports,indent=2))
audit=json.loads((P/'work/animation_audit.json').read_text());audit['Attack']['duration']=79/60;audit['Attack']['choreography']='Whole-body low-grip thrust: tail/hips load back-right, deeper chamber, tip drives farther forward/inward toward the right-pectoral line, left hand counterbalances. Continuous wind-up to frame 32, 12-frame thrust to impact at frame 44 (0.733333 s), ready at frame 79 (1.316667 s).';(P/'work/animation_audit.json').write_text(json.dumps(audit,indent=2))
runpy.run_path(str(P/'scripts/viewer_tiers.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/update_viewer_manifest.py'),run_name='__main__')
print('Preserved all geometry/textures and eight other clips in',len(reports),'GLBs.')
