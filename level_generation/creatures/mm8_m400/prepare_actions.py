"""Preserve the reviewed identity and prepare explicit magenta-matte action requests."""
from pathlib import Path
import json,hashlib
from PIL import Image
ROOT=Path(__file__).resolve().parent
batches=json.loads((ROOT/'batches.json').read_text())
sheet=Image.new('RGB',(1728,1152),(255,0,255))
for i,n in enumerate(batches['identity']['frames']):
    im=Image.open(ROOT/f'aligned_2x/{n}.png').convert('RGBA')
    sheet.paste(im,(i%3*576+32,i//3*576+32),im)
path=ROOT/'checkpoints/identity_accepted_v1.png'
if not path.exists():sheet.save(path)
notes={'status':'identity_checkpoint_accepted','scope':'Five standing views only; family remains partial.',
       'checks':{'native_view_order':True,'material_identity':True,'light_dark_edges':True,'variant_mask_overlay':True},
       'corrections':['Opaque checkerboard corrected using built-in imagegen.',
                      'Magenta edge unmixing before premultiplied downsampling.',
                      'One fixed exposure multiplier 0.8882325382437415.',
                      'Restricted warm-material mask to garment-adjacent trim after fins/claws/cuffs leakage.'],
       'limitations':['Enhanced surface detail is an interpretation; anatomy needs animation-wide consistency review.',
                      'No final runtime atlas, complete animation review or family validation yet.'],
       'references':['review/identity_native_restored.png','review/identity_edges.png','review/identity_variants_masks.png'],
       'identity_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
(ROOT/'checkpoints/identity_review.json').write_text(json.dumps(notes,indent=2)+'\n')
for key,b in batches.items():
    if key=='identity':continue
    original=Image.open(ROOT/f'references/{key}.png').convert('RGBA')
    reference=Image.new('RGB',original.size,(255,0,255));reference.paste(original,(0,0),original)
    reference.save(ROOT/f'references/{key}_matte.png')
    s=(ROOT/f'prompts/{key}.txt').read_text()
    start=s.index('Use a genuinely transparent PNG')
    end=s.index('\n',start)
    s=s[:start]+'''Background must be perfectly flat pure magenta RGB(255,0,255) in all empty pixels. No checkerboards, shadows, gradients, colored bounce or matte spill. Preserve clean foreground edge colors; magenta is absent from the creature. Retain native source-relative positioning and common body scale, including the original generous top padding; do not zoom characters up to fill cells. Deliver at least the reference dimensions if supported. Actual image dimensions are recorded separately from the 2x runtime tier.'''+s[end:]
    s+='\nKeep the exact reviewed identity: dark blue-teal scaly slender lizard humanoid, muted green sleeveless tunic, brown trim/belt/apron bands, pale gold/silver arm bands, white necklace and shin fringe, empty clawed hands. Match the accepted reference tonal weight. Every distinct supplied pose is required.\n'
    if b['action'].startswith('unbound'):
        s+='These are native stored poses without descriptor timing. Restore exactly what is shown; do not invent a generic replacement action.\n'
    (ROOT/f'prompts/{key}_v1.txt').write_text(s)
print('Reviewed identity preserved; prepared',len(batches)-1,'dependent requests')
