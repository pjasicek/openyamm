from pathlib import Path
import json,hashlib,shutil,re
P=Path('level_generation/creatures/mm8_m624_claude');V=P/'review/viewer';V.mkdir(exist_ok=True);(V/'feedback').mkdir(exist_ok=True)
old=P.parent/'mm8_m452_claude/review/viewer'
for name in ['index.html','review.js']:
 s=(old/name).read_text().replace('MM8 Wererat — animal form','MM8 Naga').replace('mm8-m452-claude','mm8-m624-claude').replace('Native m452 proportions and palette, with the MM6 Rat’s diagonal gait, bite and tail animation methods. Three native sizes.', 'Six armed hands, six rigid blades and a grounded serpent coil. Original green, violet and red costume palettes.').replace('Front paws','Six hands / blades').replace('Back / shoulders','Torso / shoulders').replace('All paws','Lower coil').replace('The jaw closes too early during the bite.','The lower sword crosses the hand during the strike.')
 if name=='review.js':s=re.sub(r'const focuses = \{[^;]+;',"const focuses = {body:[0,1.35,-0.15,6.8], head:[-0.025,2.0,0.02,1.05], arms:[0,1.5,0.05,3.3], shoulders:[0,1.6,0,2.3], skirt:[0,0.4,-0.4,3.2], feet:[0,0.2,-0.4,2.8]};",s)
 (V/name).write_text(s)
clips={'Standing':3.,'Walk':.875,'Running':.625,'Fidget':2.,'Attack':1.75,'Cast':1.75,'Hit':.625,'Death':1.5,'Dead':1.};native=json.loads((P/'references/native_actions.json').read_text());mapping={'Standing':'standing','Walk':'walk','Running':'walk','Fidget':'fidget','Attack':'attack','Cast':'attack2','Hit':'hit','Death':'death','Dead':'corpse'};manifest={'revision':'mm8_m624_attack_r3','model':'mm8_naga_a.glb','default_clip':'Attack','default_model':'a','feedback':'feedback/user_feedback.json','models':[],'clips':{}}
for tier,label in zip('abc',['Naga','Naga Warrior','Naga Queen']):
 file=V/f'mm8_naga_{tier}.glb';sha=hashlib.sha256(file.read_bytes()).hexdigest();manifest['models'].append({'id':tier,'label':label,'scale':1,'revision':'mm8_m624_attack_r3','url':file.name+'?v='+sha[:12],'sha256':sha})
for clip,duration in clips.items():
 source=native[mapping[clip]];anchors=[]
 for k,frame in enumerate(source['frames']):
  name=frame[:-1];images=[]
  for view in range(5):
   filename=name+str(view)+'_625.png'
   if (P.parent/'mm8_packed_outline_collection_20261002/families/mm8_m624/native_variants'/filename).exists():images.append('../../../mm8_packed_outline_collection_20261002/families/mm8_m624/native_variants/'+filename)
  anchors.append({'time':k/max(1,len(source['frames'])-1)*(1 if clip in ['Attack','Cast']else duration),'label':name[4:],'phase':'Native choreography reference; procedural six-arm coordination.','source_images':images})
 manifest['clips'][clip]={'label':clip,'duration':duration,'mode':'loop'if clip in ['Standing','Walk','Running','Dead']else'once','provenance':'Original m624 motion study, fitted six-arm rig and serpent chain. Cast is a separate inferred spell gesture.','anchors':anchors}
manifest['clips']['Attack']['provenance']='User-directed revision 3: left-back wind-up and right-front slash, with small individual differences in arm timing, position and sweep. Gameplay impact remains 1.0 s.'
(V/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
if not (V/'feedback/user_feedback.json').exists():(V/'feedback/user_feedback.json').write_text(json.dumps({'findings':[]},indent=2)+'\n')
