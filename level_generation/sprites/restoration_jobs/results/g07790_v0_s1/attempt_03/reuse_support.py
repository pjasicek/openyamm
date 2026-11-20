from pathlib import Path
from PIL import Image
import json,hashlib
p=Path(__file__).resolve().parent
seed=p.parents[1]/'g07790_v0_s0/attempt_04/a_5e5b2138591f6ac34f83.png'
support=Image.open(seed).convert('RGBA')
c=json.loads((p/'checks.json').read_text())
for key in c['frames']:
    dst=p/(key+'.png');backup=p/(key+'.before_support_reuse.png')
    if not backup.exists():backup.write_bytes(dst.read_bytes())
    im=Image.open(backup).convert('RGBA');im.paste(support.crop((0,98,128,256)),(0,98));im.save(dst)
(p/'support_reuse.json').write_text(json.dumps({'seed':str(seed),'sha256':hashlib.sha256(seed.read_bytes()).hexdigest(),'native_start_y':49,'evidence':'Native RGBA frames a-h differ only in rows 7 through 48; rows 49 through 127 pixel-identical. Copy reviewed rigid support below flame-contact row.'},indent=2)+'\n')
