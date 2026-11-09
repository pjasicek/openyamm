from pathlib import Path
import json,hashlib
P=Path(__file__).resolve().parents[1];V=P/'review/viewer';V.mkdir(parents=True,exist_ok=True);src=P.parent/'mm6_ert_codex/review/viewer'
s=(src/'index.html').read_text().replace('Earth Elemental · Rock Beast / Earth Spirit / Earth Elemental','PeasantF2 · town peasant').replace('Earth Elemental','PeasantF2').replace('5,998','9,902').replace('only stone colour differs','only the apron and cap colours differ').replace('Hands / fists','Apron / skirt').replace('value="48">48 fps','value="60">60 fps').replace('value="192">192 fps','value="240">240 fps')
(V/'index.html').write_text(s)
s=(src/'review.js').read_text().replace('mm6:gob','mm6:fmp').replace('mm6_gob_claude','mm6_fmp_codex').replace('Earth Elemental','PeasantF2').replace('mm6-earth-elemental','mm6-fmp')
s=s.replace('body:[0,1.05,-0.45,5.8], head:[0,2.1,0.05,1.35], arms:[0,1.6,0,3.0], shoulders:[0,1.6,0,1.6], skirt:[0,1.0,0,1.65], feet:[0,0.20,0,1.65]', 'body:[0,.83,-.12,3.6], head:[0,1.51,.03,.67], arms:[0,1.05,0,2.0], shoulders:[0,1.27,0,1.1], skirt:[0,.6,0,2.0], feet:[0,.15,0,.85]')
s=s.replace("\u00b7 Only a genuine front sprite exists.", "\u00b7 Native reference sheet.").replace('Meshy preset. No native running animation and no claimed sprite-frame correspondence.','Owned library clip; no separate native running sequence.')
s=s.replace('model=gltf.scene;model.animations=', 'model=gltf.scene;model.traverse(o=>{if(o.isSkinnedMesh)o.frustumCulled=false;});model.animations=')
(V/'review.js').write_text(s)
info=json.loads((P/'export/export_info.json').read_text());revision='fmp_v3'
models=[]
for tier,label in [('a','Peasant A · pale lavender'),('b','Peasant B · blue'),('c','Peasant C · ochre')]:
 f=V/f'mm6_fmp_{tier}.glb';models.append({'id':f'fmp_{tier}','label':label,'revision':revision,'url':f.name+'?v='+revision,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
provenance={'Standing':'More visible breathing, head and arm sway over the owned idle','Walking':'Owned relaxed walk fitted to the long skirt','Run':'Owned fleeing run with skirt motion','Hit':'Owned UnarmedGetHitF2 recoil, fitted to a relaxed stance; 0.75 s','Fidget':'Larger head turn with a small shoulder and arm adjustment','Death':'Owned kneeling forward fall, adapted for the long skirt','Dead':'Held prone corpse; refitted skirt and boots at the open hem'}
refs={'Standing':'standing','Walking':'walk_0','Run':'walk_0','Hit':'hit','Fidget':'fidget','Death':'death_corpse','Dead':'death_corpse'}
clips={n:{'label':n,'duration':d,'mode':'loop' if n in ['Standing','Walking','Run','Fidget'] else 'once','provenance':provenance[n],'anchors':[{'time':0,'label':'Native','phase':n,'source_images':['../../../mm6_fmp/references/'+refs[n]+'.png']}]} for n,d in info['clips'].items()}
(V/'manifest.json').write_text(json.dumps({'revision':revision,'model':models[0]['url'],'model_sha256':models[0]['sha256'],'default_model':'fmp_a','default_clip':'Standing','models':models,'clips':clips,'feedback':'feedback/user_feedback.json'},indent=2))
(V/'feedback').mkdir(exist_ok=True);(V/'feedback/user_feedback.json').write_text('{"findings":[]}\n')
