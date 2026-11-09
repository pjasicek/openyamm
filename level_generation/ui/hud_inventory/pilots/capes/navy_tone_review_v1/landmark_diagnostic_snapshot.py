import sys,importlib.util,json
from pathlib import Path
from PIL import Image
P=Path('/home/pjasicek/github/OpenYAMM/level_generation/ui/hud_inventory');sys.path.insert(0,str(P))
from freeze_targets import rendered
from finalize_classification import ROOT,digest
spec=importlib.util.spec_from_file_location('spell_processing',P/'pilots/air_spells/process_pair.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
out=P/'pilots/capes/navy_tone_review_v1'
for v in (1,2,3,4):
 name=f'6cape2v{v}a';native=rendered(Image.open(ROOT/f'assets_dev/engine/icons/{name}.bmp'),'item');im=Image.open(out/f'{name}.png').convert('RGBA');native=native.resize(im.size,Image.Resampling.BICUBIC)
 pictures=[]
 for pic in (native,im):
  bg=Image.new('RGBA',pic.size,'#555555');bg.alpha_composite(pic);pictures.append(bg.convert('RGB'))
 patches={'left_shoulder':(58,20,40,40),'neck_notch':(115,20,40,40),'right_peak':(145,12,40,40),'upper_fold':(100,70,30,30),'middle_fold':(105,160,30,30),'lower_left_fold':(90,350,35,35),'lower_right_fold':(170,370,35,35),'right_lower_fold':(214,420,35,45)}
 points,matches=m.match_landmarks(*pictures,patches,8)
 record=dict(points=points,matches=matches,method='Local actual image correlation, radius8, including internal scrolls and folds; diagnostic until visually verified.',script_sha256=digest(Path(__file__)))
 (out/f'{name}-landmark-diagnostic.json').write_text(json.dumps(record,indent=2)+'\n');print(name,[(r['name'],r['measured_shift_x2'],round(r['normalized_correlation'],2)) for r in matches])
(out/'landmark_diagnostic_snapshot.py').write_bytes(Path(__file__).read_bytes())
