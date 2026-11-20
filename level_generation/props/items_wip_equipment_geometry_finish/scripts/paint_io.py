"""Prepare exact paint/mask sheets or retain and split a raw built-in imagegen return without resampling."""
import hashlib,json,shutil,sys
from pathlib import Path
from PIL import Image
P=Path(__file__).resolve().parents[1]

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    command,icon=sys.argv[1:3];folder=P/'codex_tex'/('equipment_'+icon)
    if command=='guide':
        atlas=Image.open(folder/'guide_atlas.png');assert atlas.size==(1536,1024)
        sheet=Image.new('RGBA',(1536,2048));sheet.paste(atlas,(0,0));sheet.paste(atlas,(0,1024));sheet.save(folder/'paint_mask_guide.png')
    elif command=='retain':
        receipt=json.loads((folder/'generation_paint_mask.json').read_text());source=Path(receipt['source_output'])
        raw=folder/f'paint_mask_raw_v{receipt.get("revision",1)}.png';shutil.copy2(source,raw);image=Image.open(raw);w,h=image.size
        assert w%3==0 and h%4==0 and w//3==h//4,(icon,image.size)
        for kind,y in [('paint',0),('mask',h//2)]:image.crop((0,y,w,y+h//2)).save(folder/f'{kind}_atlas.png')
        receipt.update(raw_sha256=sha(raw),dimensions=[w,h],derivation='Unresized top/bottom half extraction; original retained byte-for-byte',input_sha256={s:sha(Path(s)) for s in receipt['inputs']},prepared_scene_sha256=sha(P/f'work/codex_tex/equipment_{icon}.blend'))
        (folder/'generation_paint_mask.json').write_text(json.dumps(receipt,indent=2)+'\n')
        print('Retained original',icon,image.size)
    else:raise ValueError(command)

if __name__=='__main__':main()
