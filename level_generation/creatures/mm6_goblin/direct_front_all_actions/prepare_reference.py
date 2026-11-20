"""All native goblin front actions, one row each, common source canvas/scale."""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[3]
ROWS=[('Attack',[f'gobat{x}0' for x in 'abcdef'],False),
 ('Death',[f'gobdy{x}0' for x in 'abcde'],False),
 ('Walk',[f'gobwa{x}0' for x in 'abcdef'],True),
 ('Hit',[f'gobwi{x}0' for x in 'abcdef'],False),
 ('Fidget',[f'gobfi{x}0' for x in 'abcdef'],True),
 ('Standing',['gobsta0'],True),('Corpse',['gobdyf0'],False)]
CELL=(384,320);OFFSET=(14,15);KEY=(255,0,255)
sheet=Image.new('RGB',(CELL[0]*6,CELL[1]*7),KEY)
manifest={'direction':'native front / index 0','columns':6,'rows':7,'cell_size':CELL,
 'canvas_offset':OFFSET,'native_canvas':[355,289],'key_rgb':KEY,'actions':[]}
for row,(name,stems,loop) in enumerate(ROWS):
 action={'row_index':row,'name':name,'loop':loop,'held':name in ['Standing','Corpse'],
 'animation_length_raw':len(stems)*2,'raw_unit_seconds':1/16,'frames':[]}
 for col,stem in enumerate(stems):
  p=REPO/'assets_dev/engine/sprites'/(stem+'.bmp')
  with Image.open(p) as im:
   assert im.mode=='P' and im.size==(355,289)
   mask=Image.frombytes('L',im.size,bytes(255 if x else 0 for x in im.tobytes()))
   sheet.paste(im.convert('RGB'),(col*CELL[0]+OFFSET[0],row*CELL[1]+OFFSET[1]),mask)
  action['frames'].append({'column':col,'source':str(p.relative_to(REPO)),
   'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'frame_length_raw':2,'duration_seconds':.125})
 manifest['actions'].append(action)
sheet.save(ROOT/'original_front_all_actions.png')
review=Image.new('RGB',(sheet.width+125,sheet.height),(35,35,35));review.paste(sheet,(125,0))
d=ImageDraw.Draw(review)
for row,(name,_,_) in enumerate(ROWS):d.text((8,row*320+15),f'{row+1}. {name}',fill='white')
review.save(ROOT/'original_labeled.png')
(ROOT/'source_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Packed 31 native poses: 6 Attack, 5 Death, 6 Walk, 6 Hit, 6 Fidget, 1 Standing, 1 Corpse.')
