"""Pack original attack frames without altering their pose, scale or relative anchor."""
from pathlib import Path
import json,hashlib
from PIL import Image
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[3]
KEY=(255,0,255)
sheet=Image.new('RGB',(1152,640),KEY)
records=[]
for i,letter in enumerate('abcdef'):
    source=REPO/'assets_dev/engine/sprites'/f'gobat{letter}0.bmp'
    with Image.open(source) as image:
        assert image.mode=='P' and image.size==(355,289)
        mask=Image.frombytes('L',image.size,bytes(255 if n else 0 for n in image.tobytes()))
        x=(i%3)*384+14;y=(i//3)*320+15
        sheet.paste(image.convert('RGB'),(x,y),mask)
        records.append({'frame':i,'source':str(source.relative_to(REPO)),
            'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'cell':[i%3,i//3],'original_canvas_origin_in_cell':[14,15],'original_canvas_size':[355,289]})
sheet.resize((2304,1280),Image.Resampling.NEAREST).save(ROOT/'original_attack_3x2_magenta.png')
(ROOT/'source_layout.json').write_text(json.dumps({'layout':[3,2],'cell_size_before_reference_scale':[384,320],
    'reference_scale':2,'background_rgb':KEY,'frames':records},indent=2)+'\n')
