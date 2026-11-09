"""Package diagnostic renders into labeled contact sheets and GIFs; these are not delivery sprites."""
from pathlib import Path
import argparse
import json
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parent

def build(folder):
    records=json.loads((folder/'frames.json').read_text())
    manifest=json.loads((ROOT/'animations/manifest.json').read_text())
    for clip in manifest['clips']:
        frames=[r for r in records if r['clip']==clip]
        if not frames:continue
        images=[Image.open(ROOT/r['file']).convert('RGB') for r in frames]
        total_cs=round(manifest['clips'][clip]['duration_seconds']*100)
        delays=[10*(round((i+1)*total_cs/len(images))-round(i*total_cs/len(images))) for i in range(len(images))]
        if len(images)==1:delays=[500]
        images[0].save(folder/(clip.lower()+'.gif'),save_all=True,append_images=images[1:],duration=delays,loop=0)
        sheet=Image.new('RGB',(1080,830),(46,49,50));draw=ImageDraw.Draw(sheet)
        for i in range(6):
            index=round(i*(len(images)-1)/5);im=images[index].resize((360,390),Image.Resampling.LANCZOS)
            x=(i%3)*360;y=(i//3)*415
            sheet.paste(im,(x,y+25));draw.text((x+8,y+7),f"{clip} | phase {frames[index]['phase']:.3f}",fill='white')
        sheet.save(folder/(clip.lower()+'_contact.png'))
    (folder/'README.md').write_text(
        '# Diagnostic motion playback\n\n'
        'Perspective renders on a neutral floor, plus labeled contact sheets and looping GIFs. '
        'These are working motion reviews, not accepted final sprites.\n\n'
        '`frames.json` records exact sampled action phases. GIF timing is quantized to centiseconds; '
        'non-looping contact samples include both endpoints and are distributed over the clip duration for review. '
        'Use the Blender actions for exact continuous motion; Corpse is held for 500 ms in its preview.\n')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('folder',type=Path)
    build(parser.parse_args().folder)
