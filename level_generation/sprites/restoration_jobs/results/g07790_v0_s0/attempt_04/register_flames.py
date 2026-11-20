from pathlib import Path
import json
from PIL import Image
p=Path(__file__).resolve().parent
checks=json.loads((p/'checks.json').read_text())
# Shared flame transform about native rim y=48, never fitted per-frame.
for key in checks['frames']:
    dst=p/(key+'.png'); backup=p/(key+'.before_flame_registration.png')
    if not backup.exists(): backup.write_bytes(dst.read_bytes())
    im=Image.open(backup).convert('RGBA')
    flame=im.crop((0,0,im.width,96)).convert('RGBa').resize((im.width,77),Image.Resampling.LANCZOS).convert('RGBA')
    im.paste((0,0,0,0),(0,0,im.width,96)); im.paste(flame,(0,19))
    im.save(dst)
(p/'flame_registration.json').write_text(json.dumps({'native_rim_y':48,'source_region_height_2x':96,'destination_region_height_2x':77,'shared_offset_2x':19,'reason':'All six generated flames systematically too tall with correctly placed fixed support; one common rim-anchored transform preserves relative phase differences.'},indent=2)+'\n')
