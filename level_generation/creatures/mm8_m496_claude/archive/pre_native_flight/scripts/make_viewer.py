from pathlib import Path
import json,hashlib,shutil
p=Path('level_generation/creatures/mm8_m496_claude');v=p/'review/viewer';src=p.parent/'mm8_m520_claude/review/viewer'
v.mkdir(exist_ok=True,parents=True)
for name in ['index.html','review.js']:
 s=(src/name).read_text().replace('Cyclops','Fire Elemental').replace('m520','m496').replace('Single-eye face study, heavy unarmed movement, native boulder throw and three palette variants.','Humanoid torso, rising flames, dual-palm casting and native tier sizes.')
 if name=='review.js':
  s=s.replace('time = 0, playing', 'time = 0, scrollTime = 0, playing')
  s=s.replace('time = Math.min(manifest.clips[current].duration, Math.max(0,value));', 'time = Math.min(manifest.clips[current].duration, Math.max(0,value)); if (stop) scrollTime = time;')
  s=s.replace('    seek(next,false);', "    scrollTime += dt * Number($('speed').value); seek(next,false);")
  s=s.replace('THREE.ACESFilmicToneMapping','THREE.NoToneMapping')
  s=s.replace('body:[0,1.2,0,5.4], head:[0,2.17,0,1.15], arms:[0,1.75,0,3.5]', 'body:[0,1.55,0,6.5], head:[0,1.99,0,.9], arms:[0,1.55,0,3.5]')
  s=s.replace("model.updateMatrixWorld(true); updateUI();", "model.traverse(o => { for (const m of (o.material ? (Array.isArray(o.material) ? o.material : [o.material]) : [])) { const speed = m.userData.openyamm_uv_scroll; if (speed && m.map) m.map.offset.set(scrollTime * speed[0], scrollTime * speed[1]); } });\n  model.updateMatrixWorld(true); updateUI();")
 (v/name).write_text(s)
inventory=json.loads((p/'native/inventory.json').read_text());models=[]
for tier,label in zip('abc',['Lesser Fire Elemental','Fire Elemental','Greater Fire Elemental']):
 f=v/f'mm8_m496_{tier}.glb';h=hashlib.sha256(f.read_bytes()).hexdigest();models.append({'id':f'm496_{tier}','label':label,'revision':'m496_review_01','url':f'{f.name}?v={h[:12]}','sha256':h})
durations={'Standing':3.,'Walking':1.2,'Running':.8,'Attack':1.5,'Cast':1.5,'Hit':22/30,'Fidget':2.4,'Death':22/30,'Dead':1.}
roles={'Standing':'standing','Walking':'walk','Running':'walk','Attack':'attack','Cast':'attack2','Hit':'hit','Fidget':'fidget','Death':'death','Dead':'corpse'};clips={}
for name,duration in durations.items():
 native=inventory['bindings']['73']['actions'].get(roles[name],{});frames=native.get('views',{}).get('0',[]);anchors=[]
 for i,row in enumerate(frames):
  if not row.get('frame'):continue
  anchors.append({'time':duration*i/max(len(frames)-1,1),'label':str(i+1),'phase':'Native silhouette/motion reference; 3D motion fitted to Djinn','source_images':[f'../../native/{native["views"][str(view)][min(i,len(native["views"][str(view)])-1)]["frame"]}.png' for view in range(5) if str(view) in native['views']]})
 clips[name]={'label':name,'duration':duration,'mode':'loop' if name in ['Standing','Walking','Running','Dead'] else 'once','provenance':'MM8 fire extinction and persistent ash corpse' if name in ['Death','Dead'] else 'Accepted MM6 Djinn upper-body motion fitted to MM8 torso; MM6 Fire effects treatment','anchors':anchors}
(v/'manifest.json').write_text(json.dumps({'revision':'m496_review_01','model':models[0]['url'],'default_model':'m496_a','default_clip':'Standing','model_sha256':models[0]['sha256'],'feedback':'feedback/user_feedback.json','models':models,'clips':clips},indent=2)+'\n');(v/'feedback').mkdir(exist_ok=True)
if not (v/'feedback/user_feedback.json').exists():(v/'feedback/user_feedback.json').write_text('{"findings": []}\n')
shutil.copy2(__file__,p/'scripts/make_viewer.py') if Path(__file__).resolve()!= (p/'scripts/make_viewer.py').resolve() else None
print('Viewer ready')
