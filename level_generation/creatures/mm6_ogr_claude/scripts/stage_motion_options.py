from pathlib import Path
import copy, hashlib, json, struct
p=Path(__file__).resolve().parents[1]
out=p/'review/motion_options'; original=p/'review/viewer'
sources=json.loads((out/'sources.json').read_text())
def read(path):
 b=path.read_bytes();n=struct.unpack_from('<I',b,12)[0];return json.loads(b[20:20+n]),bytearray(b[28+n:])
def write(path,j,b):
 b+=b'\0'*(-len(b)%4);j['buffers'][0]['byteLength']=len(b)
 t=json.dumps(j,separators=(',',':')).encode();t+=b' '*(-len(t)%4)
 path.write_bytes(struct.pack('<IIIII',0x46546c67,2,28+len(t)+len(b),len(t),0x4e4f534a)+t+struct.pack('<II',len(b),0x004e4942)+b)
new,nb=read(out/'ogre_motion_options.glb')
manifest=json.loads((original/'manifest.json').read_text())
models=[]
for model in manifest['models']:
 doc,binary=read(original/model['url'].split('?')[0]);byname={n['name']:i for i,n in enumerate(doc['nodes']) if 'name' in n}
 old_animations=copy.deepcopy(doc['animations']);amap={}
 def accessor(index):
  if index in amap:return amap[index]
  a=copy.deepcopy(new['accessors'][index]);assert 'sparse' not in a
  v=copy.deepcopy(new['bufferViews'][a['bufferView']]);assert v.get('buffer',0)==0
  start=v.get('byteOffset',0);raw=nb[start:start+v['byteLength']]
  binary.extend(b'\0'*(-len(binary)%4));v['byteOffset']=len(binary);binary.extend(raw)
  a['bufferView']=len(doc['bufferViews']);doc['bufferViews'].append(v)
  amap[index]=len(doc['accessors']);doc['accessors'].append(a);return amap[index]
 for animation in new['animations']:
  if animation['name'] not in sources:continue
  a=copy.deepcopy(animation)
  for sampler in a['samplers']:
   for k in ['input','output']:sampler[k]=accessor(sampler[k])
  for channel in a['channels']:
   n=new['nodes'][channel['target']['node']];target=byname[n['name']]
   for k,default in [('translation',[0,0,0]),('rotation',[0,0,0,1]),('scale',[1,1,1])]:
    x,y=n.get(k,default),doc['nodes'][target].get(k,default)
    assert max(abs(a-b) for a,b in zip(x,y))<2e-5,(n['name'],k,x,y)
   channel['target']['node']=target
  doc['animations'].append(a)
 assert doc['animations'][:len(old_animations)]==old_animations
 assert len(doc['animations'])==16
 path=out/(model['id']+'_options.glb');write(path,doc,binary)
 digest=hashlib.sha256(path.read_bytes()).hexdigest()
 models.append(dict(model,revision='ogr_motion_options_01',url=path.name+'?v='+digest[:12],sha256=digest))
manifest.update(revision='ogr_motion_options_01',models=models,model=models[0]['url'],model_sha256=models[0]['sha256'],default_clip='Running_Weighted')
manifest['feedback']='../viewer/feedback/user_feedback.json'
clips={}
for role in ['Running','Attack','Hit','Fidget','Standing','Walking','Death','Dead']:
 for name,s in sources.items():
  if s['role']==role:
   clips[name]={'label':s['label'],'duration':s['duration'],'mode':'loop' if role=='Running' else 'once',
    'provenance':'Mixamo: '+Path(s['source']).stem+'. Fitted to the Ogre; full source timing for this comparison.',
    'reference_note':'Library motion study. Source speed; game timing has not been fitted.', 'anchors':[]}
 clips[role]=manifest['clips'][role]
 clips[role]['label']=role+' · current'
manifest['clips']=clips
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
html=(original/'index.html').read_text()
html=html.replace('<h1>MM6 Ogre</h1>','<h1>MM6 Ogre — animation options</h1>')
html=html.replace('Native armour and cleaver, eight animation roles, and three original palette variants. Use the frame controls and reference images to inspect the model.','Compare options A and B with the current animation in each group. Choose a clip, press Play, and use the side camera to judge posture. These are viewer previews; the installed game model is unchanged.')
html=html.replace('src="review.js"','src="../viewer/review.js?v=motion-options-01"')
(out/'index.html').write_text(html)
# The shared existing viewer already supports arbitrary clips; make its empty-reference caption truthful.
js=(original/'review.js').read_text()
js=js.replace("'Meshy preset. No native running animation and no claimed sprite-frame correspondence.'", "info.reference_note || 'Library motion. No claimed sprite-frame correspondence.'")
(original/'review.js').write_text(js)
print('Staged 3 tiers, 16 clips, preserving all current animation data and appearance.')
