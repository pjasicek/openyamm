from pathlib import Path
import json
from PIL import Image
ROOT=Path(__file__).resolve().parent
batches=json.loads((ROOT/'batches.json').read_text())
for key,b in batches.items():
 im=Image.open(ROOT/f'references/{key}.png').convert('RGBA');bg=Image.new('RGBA',im.size,(255,0,255,255));bg.alpha_composite(im);bg.convert('RGB').save(ROOT/f'references/{key}_matte.png')
 if key=='identity':detail='Restore the FIVE distinct native stored standing angles in their exact given order. Front and quarter views have the native narrow dark mouth-like fissure; rear views retain only their original stone surfaces. Do not add eyes, a face, humanoid anatomy, arms or legs.'
 elif key.startswith('native_a'):detail='Preserve the native attack sequence: the rock opens its jagged dark mouth/cavity, pale gold-white magic flares inside in the exact frames and areas shown, then the mouth closes. Preserve every frame\'s individual jaw angle, mouth darkness and flare brightness/extent; do not put a flare in quiet frames or a closed mouth in open frames. The body stays the same stone color.'
 elif key.startswith('native_d'):detail='Preserve these native stored shattering poses and final low rubble pile exactly, including every separate airborne stone and its trajectory/placement. Do not reconstruct a full upright boulder where the native image is fragmented, tilted or collapsed. Preserve the low wide final rubble silhouette.'
 else:detail='Preserve the native changing jagged mouth opening, tilt and separate airborne pebble in each frame. Keep the native dark interior without inventing attack light. Do not omit the floating pebble or normalize the body poses.'
 prompt=f'''Use case: identity-preserve. Restore Might and Magic VIII Malevolent Boulder native creature sprites.
Input 1 is the exact native pose, silhouette, angle, color, tonal weight and layout authority. {b['columns']} columns by {b['rows']} rows of equal square cells, {len(b['frames'])} occupied cells in row-major order: {', '.join(b['frames'])}. Remaining cells stay empty. Preserve the full original margins and common scale, every frame's precise relative placement, and original bottom extent. No independent recentering, added ground or shadows. No clipping or neighboring-cell fragments.
{detail}
Keep the same asymmetrical lumpy roughly conical stone creature with a broad cluster of smaller rounded rocks around its base. Preserve its native cool gray/silvery stone, subtly violet charcoal shadows, dark fissures, pale ridged rock grain, original light direction and tonal weight. Reconstruct finer coherent striations and mineral grain instead of enlarged square pixel blocks; retain the native rock forms, cracks and proportions rather than inventing a different rock sculpture. Do not brighten it into chalk, turn it tan/brown, cover it with moss or add glowing eyes, crystals or lava.
Perfectly flat pure magenta RGB(255,0,255) background everywhere outside the artwork; no gradient, checkerboard, magenta bounce, grid, text or labels. Keep all original stone fragments inside their appropriate cells. Deliver high-detail artwork, preferably 2304 by 1536 or larger for a 3:2 sheet, with the exact supplied grid aspect ratio; no change in relative framing.
'''
 if key!='identity':prompt+='Input 2 is the accepted enhanced identity reference for material and detail consistency only; input 1 remains the authority for each action, direction, deformation and effect.\n'
 (ROOT/f'prompts/{key}_v1.txt').write_text(prompt)
p=ROOT.parent/'mm8_remaining/progress.json';ledger=json.loads(p.read_text());ledger['families']['m588'].update(status='partial',resume='Native reference sheets and exact prompts prepared. Generate and review identity first; all 95 unique native files remain required, including 53 unbound poses. One native palette 588; descriptors differ by scale.');ledger['summary']={state:sum(f['status']==state for f in ledger['families'].values()) for state in ['pending','partial','validated','blocked']};p.write_text(json.dumps(ledger,indent=2)+'\n')
print('Prepared 16 Malevolent Boulder sheets and prompts; 95 frames, single native palette 588.')
