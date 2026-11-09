import json,sys,importlib.util
from pathlib import Path
from PIL import Image,ImageDraw
P=Path('/home/pjasicek/github/OpenYAMM/level_generation/ui/hud_inventory');sys.path.insert(0,str(P))
from finalize_classification import ROOT,digest,read
from freeze_targets import rendered
import registration
out=P/'pilots/capes/alignment_review_v2';out.mkdir(exist_ok=False)
source=P/'pilots/capes/tone_review_v1/6cape1v2a.png';im=Image.open(source).convert('RGBa');im=im.transform(im.size,Image.Transform.AFFINE,(1,0,-1,0,1,1),Image.Resampling.BICUBIC).convert('RGBA');artifact=out/source.name;im.save(artifact)
job=next(j for j in read('jobs.json')['jobs'] if j['id']=='fitted_equipment_variants-72cd2fa50475');member=job['members'][1];target=next(t for t in read('expected_targets.json')['targets'] if t['id']==member['target']);result=registration.evidence(member,target,artifact,out/'registration')
spec=importlib.util.spec_from_file_location('spell_processing',P/'pilots/air_spells/process_pair.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
native=rendered(Image.open(ROOT/member['source_path']),'item').resize(im.size,Image.Resampling.BICUBIC);pics=[]
for pic in (native,im):
 bg=Image.new('RGBA',pic.size,'#555555');bg.alpha_composite(pic);pics.append(bg.convert('RGB'))
patches={'left_shoulder':(58,20,40,40),'neck_notch':(115,20,40,40),'right_peak':(145,12,40,40),'upper_scroll':(100,70,30,30),'mid_scroll':(105,160,30,30),'lower_left_fold':(90,350,35,35),'lower_right_fold':(170,370,35,35),'right_lower_pattern':(214,420,35,45)}
points,matches=m.match_landmarks(*pics,patches,8);f=Path(result['registration_record']);r=json.loads(f.read_text());r.update(landmarks=points,landmark_measurements=matches);f.write_text(json.dumps(r,indent=2)+'\n')
sheet=Image.new('RGB',(im.width*2,im.height+24),'#555555');draw=ImageDraw.Draw(sheet)
for i,bg in enumerate(('#eeeeee','#171717')):
 tile=Image.new('RGBA',im.size,bg);tile.alpha_composite(im);sheet.paste(tile.convert('RGB'),(i*im.width,24));draw.text((i*im.width,0),bg,fill='white')
sheet.save(out/'light-dark.png');(out/'process_snapshot.py').write_bytes(Path(__file__).read_bytes());(out/'processing.json').write_text(json.dumps(dict(source=str(source),source_sha256=digest(source),shift_x2=[1,-1],script_sha256=digest(Path(__file__)),result=result),indent=2)+'\n');print(result);print(matches)
