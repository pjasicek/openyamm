import sys,importlib.util,json
from pathlib import Path
from PIL import Image
P=Path('/home/pjasicek/github/OpenYAMM/level_generation/ui/hud_inventory');sys.path.insert(0,str(P))
from freeze_targets import rendered
from finalize_classification import ROOT,digest
spec=importlib.util.spec_from_file_location('spell_processing',P/'pilots/air_spells/process_pair.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
out=P/'pilots/capes/green_tone_review_v3'
for v in (1,2,3,4):
 name=f'6cape3v{v}a';native=rendered(Image.open(ROOT/f'assets_dev/engine/icons/{name}.bmp'),'item');im=Image.open(out/f'{name}.png').convert('RGBA');native=native.resize(im.size,Image.Resampling.BICUBIC)
 pictures=[]
 for pic in (native,im):
  bg=Image.new('RGBA',pic.size,'#555555');bg.alpha_composite(pic);pictures.append(bg.convert('RGB'))
 hem_y=410 if v != 4 else 440
 patches={'left_shoulder_hole':(40,8,45,45),'right_shoulder_hole':(165,8,45,45),'left_side_notch':(12,235 if v!=4 else 260,50,50),'right_side_tip':(200,245 if v!=4 else 265,45,50),'upper_fold':(65,100,40,40),'left_hem_scroll':(20,hem_y,45,45),'middle_hem_scroll':(102,hem_y,45,45),'right_hem_scroll':(180,hem_y,45,45)}
 points,matches=m.match_landmarks(*pictures,patches,8)
 record=dict(points=points,matches=matches,method='Local actual image correlation, radius8, including internal scrolls and folds; diagnostic until visually verified.',script_sha256=digest(Path(__file__)))
 (out/f'{name}-landmark-diagnostic.json').write_text(json.dumps(record,indent=2)+'\n');print(name,[(r['name'],r['measured_shift_x2'],round(r['normalized_correlation'],2)) for r in matches])
(out/'landmark_diagnostic_snapshot.py').write_bytes(Path(__file__).read_bytes())
