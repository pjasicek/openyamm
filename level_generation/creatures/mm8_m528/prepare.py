from pathlib import Path
import json
from PIL import Image
ROOT=Path(__file__).resolve().parent
batches=json.loads((ROOT/'batches.json').read_text())
for key,b in batches.items():
 im=Image.open(ROOT/f'references/{key}.png').convert('RGBA');bg=Image.new('RGBA',im.size,(255,0,255,255));bg.alpha_composite(im);bg.convert('RGB').save(ROOT/f'references/{key}_matte.png')
 prompt=f'''Use case: identity-preserve. Restore Might and Magic VIII Will-o'-Wisp native sprite artwork.
Input 1 is the exact native pose and layout authority: {b['columns']} columns × {b['rows']} rows, {len(b['frames'])} occupied cells, row-major frames {', '.join(b['frames'])}. Every supplied frame is required.
Preserve the original dark charcoal smoky core, its gold-white horizontal fiery slit/streak and irregular surrounding white-gold electrical wisps and tiny sparks. This is the SAME original compact floating magical effect. Keep its original colors, tonal weight, relative core size, outer silhouette, asymmetry and each frame's precise changing shape. Do not add a face, eyes, limbs, equipment, a chrome ball, ground shadow, large bloom or a new circular halo. Enhance coherent fine detail inside the original design without redesigning it or enlarging the core relative to the surrounding wisps.
Preserve equal cells and generous native empty margins, native relative placement and common scale. No recentering individual frames, normalizing silhouettes or adding duplicate figures. Keep all sparks intact inside the appropriate cell, with no crop or neighboring-cell crossing. No text, labels, grid lines or watermarks.
Background must be perfectly flat pure magenta RGB(255,0,255) in every empty pixel; no checkerboard, gradient, shadow or magenta bounce on the wisp. Preserve gold-white spark edge colors. Deliver clean high-resolution raster detail; runtime placement and size are handled offline from the recorded native layout.
'''
 if key!='identity':prompt+='Input 2 is the accepted restored identity reference. Match its material/detail treatment while input 1 remains the pose and silhouette authority.\n'
 (ROOT/f'prompts/{key}_v1.txt').write_text(prompt)
print('Prepared',len(batches),'native matte references and exact prompts')
