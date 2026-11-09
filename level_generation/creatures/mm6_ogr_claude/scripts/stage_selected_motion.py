"""Replace only selected animation streams in the approved geometry/LOD/texture packages."""
from pathlib import Path
import copy,hashlib,json,shutil,sys
p=Path(__file__).resolve().parents[1];repo=p.parents[2];out=p/'revision_03';old=out/'previous'
sys.path.insert(0,str(repo/'tools'))
import merge_head_material as M
new,nb=M.read_glb(out/'selected_motion.glb')
roles={'Running','Attack','Fidget'}
report={}
paths=[x for x in (p/'export').glob('*.glb') if x.name not in {'mm6_ogr_sword.glb','mm6_ogr_lods.geometry.glb'}]
paths += [p/'review/viewer'/f'mm6_ogr_{tier}.glb' for tier in 'abc']
for path in paths:
 backup=old/path.relative_to(p);backup.parent.mkdir(parents=True,exist_ok=True)
 if not backup.exists():shutil.copy2(path,backup)
 doc,binary=M.read_glb(backup)
 before=copy.deepcopy(doc);old_binary=bytes(binary)
 byname={n['name']:i for i,n in enumerate(doc['nodes']) if 'name' in n};amap={}
 def accessor(index):
  if index in amap:return amap[index]
  a=copy.deepcopy(new['accessors'][index]);assert 'sparse' not in a
  v=copy.deepcopy(new['bufferViews'][a['bufferView']]);assert v.get('buffer',0)==0
  offset=v.get('byteOffset',0);raw=nb[offset:offset+v['byteLength']]
  binary.extend(b'\0'*(-len(binary)%4));v['byteOffset']=len(binary);binary.extend(raw)
  a['bufferView']=len(doc['bufferViews']);doc['bufferViews'].append(v)
  amap[index]=len(doc['accessors']);doc['accessors'].append(a);return amap[index]
 for animation in new['animations']:
  if animation['name'] not in roles:continue
  a=copy.deepcopy(animation)
  for s in a['samplers']:
   for key in ('input','output'):s[key]=accessor(s[key])
  for c in a['channels']:
   n=new['nodes'][c['target']['node']];target=byname[n['name']]
   for key,default in [('translation',[0,0,0]),('rotation',[0,0,0,1]),('scale',[1,1,1])]:
    assert max(abs(x-y) for x,y in zip(n.get(key,default),doc['nodes'][target].get(key,default)))<2e-5,(n['name'],key)
   c['target']['node']=target
  index=next(i for i,a0 in enumerate(doc['animations']) if a0['name']==a['name'])
  doc['animations'][index]=a
 assert bytes(binary[:len(old_binary)])==old_binary
 for key in before:
  if key not in {'animations','accessors','bufferViews','buffers'}:assert before[key]==doc[key],key
 assert [a for a in doc['animations'] if a['name'] not in roles]==[a for a in before['animations'] if a['name'] not in roles]
 assert len(doc['animations'])==8
 M.write_glb(path,doc,binary)
 report[str(path.relative_to(p))]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'appearance_and_other_clips_unchanged':True}
shutil.copy2(out/'selected_motion.blend',p/'export/mm6_ogr.blend')
manifest_path=p/'review/viewer/manifest.json';backup=old/'viewer_manifest.json'
if not backup.exists():shutil.copy2(manifest_path,backup)
m=json.loads(backup.read_text());m['revision']='ogr_revision_03';m['default_clip']='Running'
sources=json.loads((p/'review/motion_options/sources.json').read_text())
for source,role in [('Running_Weighted','Running'),('Attack_Downward','Attack'),('Fidget_NeckStretch','Fidget')]:
 s=sources[source]
 m['clips'][role]={'label':role,'duration':s['duration'],'mode':'loop' if role=='Running' else 'once',
  'provenance':'User-selected A: '+Path(s['source']).stem,
  'reference_note':'Selected library motion; native sprite-frame correspondence is not claimed.','anchors':[]}
m['clips']['Attack']['provenance']+='; game impact at 26/30 s'
for model in m['models']:
 name=model['url'].split('?')[0];h=report['review/viewer/'+name]['sha256']
 model.update(revision=m['revision'],url=name+'?v='+h[:12],sha256=h)
m['model_sha256']=m['models'][0]['sha256'];manifest_path.write_text(json.dumps(m,indent=1)+'\n')
(out/'checks/package.json').write_text(json.dumps(report,indent=2)+'\n')
print('STAGED',len(paths),'animation packages; appearance and five other clips preserved exactly')
