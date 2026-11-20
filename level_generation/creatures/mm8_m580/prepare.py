from pathlib import Path
import json
from PIL import Image
ROOT=Path(__file__).resolve().parent
batches=json.loads((ROOT/'batches.json').read_text())
for key,b in batches.items():
 im=Image.open(ROOT/f'references/{key}.png').convert('RGBA');bg=Image.new('RGBA',im.size,(255,0,255,255));bg.alpha_composite(im);bg.convert('RGB').save(ROOT/f'references/{key}_matte.png')
 if key=='identity':detail='Restore these five stored directions of the same Dragon Turtle, preserving frontal foreshortening, both quarter views, the long side profile, and rear shell view. This pose is shared by the first swim, attack, hit and fidget frames.'
 elif key.startswith('native_d'):detail='Preserve the exact native roll and collapse: these are tilted or overturned turtle poses and the low final corpse, not upright swimming poses. Follow the original head direction and flipper silhouettes in each cell.'
 elif key.startswith('native_a'):detail='Preserve every individual native bite/neck-lunge pose: exact mouth opening, jaw, teeth, raised or extended neck, shell angle, tail curve and flipper stroke. Do not add fire, spell effects or new movement.'
 else:detail='Follow each native pose exactly, including its individual neck and head position, mouth state, tail curve, shell tilt and flipper angles. Do not normalize all poses to the identity stance.'
 prompt=f'''Use case: identity-preserve. Restore Might and Magic VIII Dragon Turtle native sprites, base palette 581.
Input 1 is the exact native appearance, pose, view, color, tonal weight and layout authority. {b['columns']} columns by {b['rows']} rows, {len(b['frames'])} occupied cells, row-major order: {', '.join(b['frames'])}. Preserve the exact supplied sheet aspect ratio, equal cells, common native scale, all empty margins, and each frame's position. Empty cells remain empty. No recentering or silhouette size fitting.
{detail}
Preserve the original dark green and ochre-brown segmented domed shell, angular black plate seams, long swept-back charcoal horns and shell spikes, charcoal/olive-gray neck and flippers with pale subtle veins, tapered tail, yellow eye and pale tan/cream cheek and jaw. Keep the original spiny aquatic dragon-turtle anatomy, four flippers and long dragon head. Retain dark shadow weight and native material boundaries. Refine coherent shell grain, restrained scaly skin and horn detail; do not invent a different turtle, bright emerald shell, decorative patterns, mammal feet, wings, extra horns, armor, glossy toy finish or added lighting.
Use perfectly flat magenta RGB(255,0,255) only outside the artwork, with no magenta bounce or spill. No text, labels, grid, checkerboard, cast ground shadow, environment or border. Keep thin horns, flipper tips and tail entirely in their assigned cells. Render useful high-resolution detail, ideally at least the supplied sheet dimensions, with the SAME framing and aspect ratio.
'''
 if key!='identity':prompt+='Input 2 is the accepted restored identity reference for material and detail consistency only. Input 1 remains the sole authority for every pose, view and relative placement.\n'
 (ROOT/f'prompts/{key}_v1.txt').write_text(prompt)
p=ROOT.parent/'mm8_remaining/progress.json';ledger=json.loads(p.read_text());ledger['families']['m580'].update(status='partial',processed_frames=0,resume='Generate and accept the five-view identity. Restore 120 unique frames in 26 sheets, reuse 15 exact pixel aliases, derive palettes 582/583 deterministically from enhanced-art masks, then export and validate all 135 native files.');ledger['summary']={state:sum(f['status']==state for f in ledger['families'].values()) for state in ['pending','partial','validated','blocked']};p.write_text(json.dumps(ledger,indent=2)+'\n')
print('Prepared all 26 Dragon Turtle references and prompts.')
