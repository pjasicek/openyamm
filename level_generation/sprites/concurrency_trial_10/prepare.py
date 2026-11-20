from pathlib import Path
import json,hashlib
from PIL import Image
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
inventory=json.loads((HERE.parent/'inventory.json').read_text())
selected=[f for f in inventory['files'] if f['classification']=='referenced_non_creature'][:10]
for d in ['native','references','prompts','raw','enhanced','review']:(HERE/d).mkdir(exist_ok=True)
jobs=[]
for f in selected:
 name=f['name'];source=REPO/f['path'];native=Image.open(source);palettes={p for g in inventory['groups'] for n,p in g['image_palette_pairs'] if n==name};assert len(palettes)==1,(name,palettes)
 pal=palettes.pop();palette_name=f'pal{pal:03d}.act'
 candidates=[REPO/'assets_dev/worlds/mm6/textures'/palette_name,REPO/'assets_dev/engine/textures'/palette_name]
 palette=next(p for p in candidates if p.exists());native.putpalette(palette.read_bytes()[:768]);rgba=native.convert('RGBA');rgba.putalpha(native.point(lambda i:0 if i==0 else 255,'L'));rgba.save(HERE/'native'/f'{name}.png')
 canvas=Image.new('RGBA',(1024,1024),(255,0,255,255));factor=800/max(native.size);scaled=rgba.resize((round(native.width*factor),round(native.height*factor)),Image.Resampling.NEAREST);canvas.alpha_composite(scaled,((1024-scaled.width)//2,(1024-scaled.height)//2));canvas.convert('RGB').save(HERE/'references'/f'{name}.png')
 hint=next(g['name'] for g in inventory['groups'] if name in g['existing_images'])
 prompt='''Use case: precise-object-edit. Asset type: faithful high-resolution restoration of an original Might and Magic VI ground-item billboard sprite for use in the actual game.
The input is the EDIT TARGET and exact shape, orientation, material, color and layout authority. Restore the same single depicted item, clarifying realistic fine detail inside its original shapes. Preserve its exact object identity, silhouette, component count, proportions, slant, perspective and lighting. Retain the original dark tonal weight and material color; do not redesign it, turn it upright, add parts, add magical effects or turn it into a cartoon, smooth plastic or a studio product photo. Preserve genuine holes and openings. Complete item, no cropped parts.
Keep the source-relative item size/position and generous empty margins in this square image. No text, labels, grids, borders, watermarks, extra objects, cast shadow or ground plane. Deliver one detailed square image, preferably at least 1024 pixels wide.
Backdrop: completely flat pure magenta RGB(255,0,255), including any holes in the item, without gradient, checkerboard, rim-light, colored spill/reflections or halo. This matte is removed deterministically afterward. Never mix its hue into foreground edges.
'''
 (HERE/'prompts'/f'{name}.txt').write_text(prompt)
 jobs.append(dict(id=name,prompt=prompt,reference=str(HERE/'references'/f'{name}.png'),source=f['path'],source_sha256=f['sha256'],native_size=list(native.size),native_bounds=list(rgba.getbbox()),palette_id=pal,palette=str(palette.relative_to(REPO)),palette_sha256=hashlib.sha256(palette.read_bytes()).hexdigest()))
(HERE/'jobs.json').write_text(json.dumps(jobs,indent=2)+'\n')
print(json.dumps([{k:j[k] for k in ['id','native_size','palette_id']} for j in jobs]))
