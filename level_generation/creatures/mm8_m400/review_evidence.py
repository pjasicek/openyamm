from pathlib import Path
import json
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent
reg=json.loads((ROOT/'registration.json').read_text());batches=json.loads((ROOT/'batches.json').read_text())
for action in ('identity','w','n','f','d','a'):
 keys=[k for k in batches if k=='identity'] if action=='identity' else [k for k in batches if k.startswith('native_'+action+'_')]
 names=[n for k in keys for n in batches[k]['frames']]
 cols=8;rows=(len(names)+cols-1)//cols;out=Image.new('RGB',(cols*180,rows*200),(38,38,38));draw=ImageDraw.Draw(out)
 for i,n in enumerate(names):
  im=Image.open(ROOT/f'aligned_2x/{n}.png').convert('RGBA');x,y=reg[n]['edge_export']['position'];patch=im.crop((x-16,y-16,x+16,y+16))
  for j,bg in enumerate(((25,25,25),(240,240,240))):
   cell=Image.new('RGBA',patch.size,(*bg,255));cell.alpha_composite(patch);out.paste(cell.convert('RGB').resize((90,90),Image.Resampling.NEAREST),(i%cols*180+j*90,i//cols*200+20))
  # Whole frame over white reveals dark/pink residual rims outside the hotspot.
  bb=im.getchannel('A').getbbox();thumb=im.crop(bb);thumb.thumbnail((175,80),Image.Resampling.LANCZOS);bg=Image.new('RGBA',(180,85),(240,240,240,255));bg.alpha_composite(thumb,((180-thumb.width)//2,(85-thumb.height)//2));out.paste(bg.convert('RGB'),(i%cols*180,i//cols*200+112));draw.text((i%cols*180+3,i//cols*200+2),n,fill='white')
 out.save(ROOT/f'review/final_edges_{action}.png')
# Frame-stepped death transition, including the two initial hit frames and corpse hold.
inv=json.loads((ROOT/'sources.json').read_text());out=Image.new('RGB',(7*220,5*300),(38,38,38));draw=ImageDraw.Draw(out)
for view in range(5):
 steps=inv['bindings']['1']['actions']['death']['views'][str(view)]+inv['bindings']['1']['actions']['corpse']['views'][str(view)]
 for i,step in enumerate(steps):
  n=step['frame']
  for row,folder in enumerate(('native_variants','previews')):
   im=Image.open(ROOT/f'{folder}/{n}_401.png').convert('RGBA');im.thumbnail((215,135),Image.Resampling.LANCZOS);bg=Image.new('RGBA',im.size,(38,38,38,255));bg.alpha_composite(im);out.paste(bg.convert('RGB'),(i*220,view*300+row*145+10))
  draw.text((i*220+3,view*300+2),n+' / 125ms'+(' hold' if i==6 else ''),fill='white')
out.save(ROOT/'review/death_transition_native_restored.png')
print('Six edge sheets and five-view native death transition saved')
