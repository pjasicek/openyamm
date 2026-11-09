"""Assemble unchanged shared-viewer captures into reviewer sheets."""
from pathlib import Path
import json
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[1];R=P/'review/round2'
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14)
manifest=json.loads((P/'review/viewer/manifest.json').read_text())
plan=json.loads((R/'capture_after.json').read_text());assert all((R/(x[0]+'.png')).exists()for x in plan)
def board(title,entries,cols,size=(360,350),crop=False):
 w,h=size;out=Image.new('RGB',(w*cols,h*((len(entries)+cols-1)//cols)+48),(31,34,39));d=ImageDraw.Draw(out);d.text((15,12),title,font=font,fill='white')
 for i,(path,label)in enumerate(entries):
  im=Image.open(path).convert('RGB')
  if crop:
   # Remove empty space only; retain the actual rendered switch-size pixels.
   im=im.crop(((im.width-w)//2,max(0,(im.height-h+34)//2),(im.width+w)//2,min(im.height,(im.height+h-34)//2)))
  im.thumbnail((w-8,h-34),Image.Resampling.LANCZOS);x=(i%cols)*w+(w-im.width)//2;y=(i//cols)*h+48
  out.paste(im,(x,y));d.text(((i%cols)*w+8,y+h-27),label,font=small,fill='white')
 return out
for clip,c in manifest['clips'].items():
 entries=[(R/f'viewer_clips/{clip}/{i:02}_{view}.png',f'{view} | {c["duration"]*i/5:.3f} s')for view in ['front','left','three_quarter']for i in range(6)]
 board(f'PeasantF3 — Review round 2 — {clip} — direct GLB viewer',entries,6).save(P/f'review/sheets/{clip}.png')
for area in ['face','blouse','midriff','arm']:
 entries=[(R/f'{phase}/{area}.png',f'{phase.title()} — identical camera and lighting')for phase in ['before','after']]
 board(f'Review round 2 — {area}',entries,2,(805,754)).save(R/f'before_after_{area}.png')
entries=[(R/f'attack_recovery/{frame}_{view}.png',f'{view} | frame {frame} / {frame/48:.3f}s')for view in ['front','left','three_quarter']for frame in [24,32,40,48,54]]
board('Attack — preserved cut, then direct recovery to the side by frame 54',entries,5,(370,375)).save(R/'attack_recovery.png')
entries=[(R/f'lods/lod{level}_{tier}_three_quarter.png',f'LOD{level} / {tier} / {[700,550,220,88][level]} px target')for level in range(4)for tier in 'abc']
board('Four LODs / three tiers — original switch-size pixels, cropped empty space',entries,3,(540,754),True).save(R/'lod_tiers.png')
entries=[(R/f'viewer_grip_{phase}_{view}.png',f'{phase} / {view}')for phase in ['windup','impact']for view in ['left','three_quarter']]
board('Retained reverse grip — final exported textures and motion',entries,2,(550,540)).save(R/'grip.png')
entries=[(P.parent/f'mm6_mfp/trimmed_2x/mfpatt{c}0.png',f'Restored native attack {c}')for c in 'bcd']
entries += [(R/f'viewer_clips/Attack/{phase}_front.png',f'3D {phase}')for phase in ['windup','impact','followthrough']]
board('Native slash intent — poses, not identical source timing',entries,3,(420,420)).save(R/'attack_native_comparison.png')
print('Eight clip sheets, four full-resolution comparisons, recovery, grip, LODs and native sheet assembled')
