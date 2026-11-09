"""Wire authored LODs and existing runtime materials; reuse the shared creature review page."""
import copy,hashlib,json,re,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P.parents[2]
sys.path.insert(0,str(R/'tools'))
from merge_head_material import read_glb,write_glb,compact
from model_hide_collapsed_meshes import analyse,write as hide_collapsed
d,b=read_glb(P/'export/mm8_m528_raw.glb');info=json.loads((P/'export/export_info.json').read_text())
assert len(d['skins'])==1
for base in ['WispRing','WispSparks']:
    meshes={m['name']:i for i,m in enumerate(d['meshes'])}
    ids=[meshes[f'{base}_LOD{i}'] for i in range(1,4)]
    d['meshes'][meshes[base]].setdefault('extras',{})['openyamm_lods']=ids
    for n in d['nodes']:
        if n.get('mesh') in ids:n.pop('mesh');n.pop('skin',None)
for m in d['materials']:
    m.update(alphaMode='BLEND',doubleSided=False,extensions={'KHR_materials_unlit':{}},
        extras={'openyamm_specular':0,'openyamm_edge_darkening':0})
    m.pop('emissiveTexture',None);m.pop('emissiveFactor',None)
    p=m['pbrMetallicRoughness'];p['metallicFactor']=0;p['roughnessFactor']=1
    # Keep the core visible when the engine sorts the smoke surface over the light cards.
    if m['name']=='WispSmoke':p['baseColorFactor']=[1,1,1,.45]
    texture=d['textures'][p['baseColorTexture']['index']]
    sampler=d['samplers'][texture['sampler']]
    sampler['wrapS']=10497 if m['name']=='WispSmoke' else 33071
    sampler['wrapT']=10497 if m['name']=='WispSmoke' else 33071
    if m['name']=='WispSmoke':m['extras']['openyamm_uv_scroll']=[.18,0]
d['extensionsUsed']=['KHR_materials_unlit'];d.pop('extensionsRequired',None)
d,b=compact(d,b)
visibility=analyse(d,b)
b=hide_collapsed(d,b,visibility)
write_glb(P/'export/mm8_m528.glb',d,b)
(P/'work/visibility.json').write_text(json.dumps({d['nodes'][i]['name']:v for i,v in visibility.items()},indent=2)+'\n')

V=P/'review/viewer';template=P.parent/'mm8_m628/review/viewer'
html=(template/'index.html').read_text().replace('MM8 Skeleton Archer','MM8 Will-o’-Wisp')
html=re.sub(r'<header>.*?</header>','<header><h1>MM8 Will-o’-Wisp</h1><p>Body and animation preview. White stars are engine particles; see the native captures for the complete creature.</p></header>',html)
html=html.replace('Head / neck','Core').replace('Arms / wrists','Spark ring').replace('Shoulders / wings','Pulse').replace('Hands','Smoke').replace('Feet','Underside')
(V/'index.html').write_text(html)
js=(template/'review.js').read_text().replace('MM8 Skeleton Archer','MM8 Will-o’-Wisp')
js=re.sub(r'const focuses = .*?;', 'const focuses = {body:[0,0,0,2.6],head:[0,0,0,1.05],arms:[0,0,0,1.65],shoulders:[0,0,0,2.2],skirt:[0,0,0,2.4],feet:[0,-.15,0,1.4]};',js)
js=js.replace('scene.add(grid);','scene.add(grid); grid.position.y=-.65;')
js=js.replace('model=gltf.scene;model.animations=',
    "model=gltf.scene; model.scale.setScalar(info.scale||1); model.traverse(o=>{if(o.isMesh){o.renderOrder=o.name.startsWith('WispRing')?0:1; for(const m of (Array.isArray(o.material)?o.material:[o.material]))m.depthWrite=false;}});model.animations=")
js=js.replace('previousTick=now; controls.update();',
    "previousTick=now; if(model)model.traverse(o=>{if(o.isMesh)for(const m of(Array.isArray(o.material)?o.material:[o.material])){const s=m.userData.openyamm_uv_scroll;if(s&&m.map)m.map.offset.set(time*s[0],time*s[1]);}}); controls.update();")
(V/'review.js').write_text(js)
if not (V/'feedback/user_feedback.json').exists():
    (V/'feedback/user_feedback.json').write_text('{"findings":[]}\n')
sha=hashlib.sha256((P/'export/mm8_m528.glb').read_bytes()).hexdigest()
models=[{'id':f'm528_{c}','label':label,'revision':'m528-v3','url':'../../export/mm8_m528.glb?v='+sha[:12],
    'sha256':sha,'scale':scale} for c,label,scale in [('a','Dancing Light · 1×',1),('b','Wisp · 1.3×',1.299988),('c','Will-o’-Wisp · 1.7×',1.699997)]]
source=json.loads((P/'source/native_inventory.json').read_text())['actions']
mapping={'Standing':'standing','Walking':'walk','Attack':'attack','Hit':'hit','Death':'death','Dead':'corpse'}
clips={}
for name,duration in info['clips'].items():
    a=source[mapping[name]];t=0;anchors=[]
    for f in a['frames']:
        if f['name']:
            anchors.append({'time':min(t,duration),'label':f['name'],'phase':'Native source',
                'source_images':['../../../mm8_m528/aligned_2x/'+f['name']+'.png']})
        t+=f['seconds']
    clips[name]={'label':name,'duration':duration,'mode':'loop' if name in ('Standing','Walking','Dead') else 'once',
        'provenance':'New procedural volume and motion from native m528 effects; Reactor/Air Elemental material methods.',
        'anchors':anchors}
(V/'manifest.json').write_text(json.dumps({'revision':'m528-v3','default_model':'m528_a','default_clip':'Standing',
    'model':'../../export/mm8_m528.glb','model_sha256':sha,'models':models,'clips':clips,'feedback':'feedback/user_feedback.json'},indent=2)+'\n')
print('Prepared runtime and viewer',sha,info['triangles'])
