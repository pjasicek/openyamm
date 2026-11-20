import importlib.util,json,sys
from pathlib import Path
from PIL import Image
P=Path('/home/pjasicek/github/OpenYAMM/level_generation/ui/hud_inventory')
sys.path.insert(0,str(P))
from freeze_targets import rendered
spec=importlib.util.spec_from_file_location('spell_matching',P/'pilots/air_spells/process_pair.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
patches={
 '6boots2v1':{'rear_cuff':(57,30,38,40),'rear_ankle':(68,66,40,42),'rear_toe':(40,102,38,28),'front_cuff':(127,83,43,38),'front_ankle':(111,135,45,40),'front_toe':(103,177,44,33)},
 '6boots2v2':{'rear_cuff':(25,10,43,42),'rear_toe':(40,64,30,42),'front_cuff':(65,60,36,38),'front_ankle':(53,106,38,32),'front_toe':(43,139,43,27)},
 '6boots2v4':{'left_cuff':(28,101,45,34),'left_ankle':(38,152,45,33),'left_toe':(0,179,39,28),'left_heel':(77,154,30,34),'right_cuff':(131,103,53,36),'right_ankle':(135,158,45,31),'right_toe':(106,181,40,27),'right_heel':(177,162,25,34)},
 '6boots2v5':{'left_cuff':(43,88,41,34),'left_ankle':(46,128,42,29),'left_toe':(14,150,42,28),'left_heel':(82,129,27,31),'right_cuff':(132,91,48,33),'right_ankle':(134,134,39,29),'right_toe':(104,154,40,27),'right_heel':(169,140,23,28)}}
out=P/'pilots/boots/steel_final_review'
for n,ps in patches.items():
 im=Image.open(out/(n+'.png')).convert('RGBA');native=rendered(Image.open(P.parents[2]/'assets_dev/engine/icons'/f'{n}.bmp'),'item').resize(im.size,Image.Resampling.BICUBIC)
 def bg(i):
  b=Image.new('RGBA',i.size,'#555555');b.alpha_composite(i);return b
 points,matches=m.match_landmarks(bg(native),bg(im),ps,5)
 f=out/'registration'/f'engine--icons--{n}.bmp-registration.json';d=json.loads(f.read_text());d['contour_landmarks_diagnostic']=d['landmarks'];d['landmarks']=points;d['patch_matches']=matches;d['landmark_method']='Native patch correlation at x2; stable cuff/ankle/toe/heel features replace ambiguous global highest-point median. Raw contour diagnostics retained.';f.write_text(json.dumps(d,indent=2)+'\n')
 print(n,[(r['name'],r['measured_shift_x2']) for r in matches])
(out/'landmark_snapshot.py').write_bytes(Path(__file__).read_bytes())
