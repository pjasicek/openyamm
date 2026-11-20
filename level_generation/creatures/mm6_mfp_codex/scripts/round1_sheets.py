"""Assemble final viewer captures; no rendering or gate calculations."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
P=Path(__file__).resolve().parents[1]; R=P/'review/round1'
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14)
manifest=json.loads((P/'review/viewer/manifest.json').read_text())
plan=json.loads((R/'capture_plan.json').read_text())
assert len(plan)==159 and all((R/(x[0]+'.png')).exists() for x in plan)
def board(title, entries, cols, size=(360,350), nearest=False):
 w,h=size; rows=(len(entries)+cols-1)//cols
 out=Image.new('RGB',(w*cols,h*rows+48),(31,34,39));d=ImageDraw.Draw(out);d.text((15,12),title,font=font,fill='white')
 for i,(path,label) in enumerate(entries):
  im=Image.open(path).convert('RGBA');im.thumbnail((w-8,h-34),Image.Resampling.NEAREST if nearest else Image.Resampling.LANCZOS)
  x=(i%cols)*w+(w-im.width)//2;y=(i//cols)*h+48
  out.paste(im,(x,y),im);d.text(((i%cols)*w+8,y+h-27),label,font=small,fill='white')
 return out
for clip,c in manifest['clips'].items():
 entries=[]
 for view in ['front','left','three_quarter']:
  for i in range(6):entries.append((R/f'viewer_clips/{clip}/{i:02}_{view}.png',f'{view} | {c["duration"]*i/5:.3f} s'))
 board(f'PeasantF3 — Review round 1 — {clip} — direct viewer',entries,6).save(P/f'review/sheets/{clip}.png')
entries=[]
for view in ['front','left','three_quarter']:
 for phase in ['windup','impact','followthrough']:entries.append((R/f'viewer_clips/Attack/{phase}_{view}.png',f'{phase} | {view}'))
board('Downward slash — wind-up 0.517 / impact 0.656 / follow-through 0.867 s',entries,3,(460,455)).save(R/'attack_phases.png')
entries=[(R/'viewer_skin_front.png','Skin — front'),(R/'viewer_skin_quarter.png','Skin — quarter')]
entries += [(R/f'viewer_grip_{phase}_{view}.png',f'Grip — {phase}, {view}') for phase in ['windup','impact'] for view in ['left','three_quarter']]
board('Review round 1 — skin and reverse grip — direct viewer',entries,3,(530,515)).save(R/'skin_and_grip.png')
entries=[(P.parent/f'mm6_mfp/trimmed_2x/mfpatt{c}0.png',f'Restored native attack {c}')for c in 'bcd']
entries += [(R/f'viewer_clips/Attack/{phase}_front.png',f'3D {phase}')for phase in ['windup','impact','followthrough']]
board('Native attack intent and revised slash (poses, not identical timing)',entries,3,(420,420),True).save(R/'attack_native_comparison.png')
entries=[(R/f'lods/lod{level}_mfp_{tier}_three_quarter.png',f'LOD{level} — tier {tier}')for level in range(4)for tier in 'abc']
board('Auxiliary Blender LOD/tier renders — original switch-size captures',entries,3,(350,600)).save(R/'lod_tiers.png')
print('Eight clip sheets, attack phases/native comparison, skin/grip and LOD tier sheets assembled')
