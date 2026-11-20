"""Build offline master/atlas playback, overview, animated contacts and edge review."""
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from process import helpers

HERE = Path(__file__).resolve().parent


def main():
    manifest=json.loads((HERE/'manifest.json').read_text())
    html=(HERE/'viewer_template.html').read_text()
    for token,pattern in [('CONTACTS','contact_*.jpg'),('MASKS','masks_*.jpg')]:
        html=html.replace(token,''.join(f'<img src="review/{p.name}">' for p in sorted((HERE/'review').glob(pattern))))
    (HERE/'viewer.html').write_text(html.replace('MANIFEST',json.dumps(manifest)))
    for action in ['walk','attack','hit','fidget','death']:
        animation=manifest['animations'][action]
        if not all(e['frame'] in manifest['frames'] for seq in animation['views'].values() for e in seq):
            continue
        boards=[]
        count=len(animation['views']['0'])+(1 if action=='death' else 0)
        for i in range(count):
            board=Image.new('RGB',(1600,360),(41,46,53));draw=ImageDraw.Draw(board)
            for v in range(5):
                seq=animation['views'][str(v)]
                entry=seq[i] if i<len(seq) else manifest['animations']['corpse']['views'][str(v)][0]
                im=Image.open(HERE/f'aligned_2x/{entry["frame"]}.png')
                # Fixed common crop for playback; no pose-dependent fitting.
                im=im.crop((0,64,640,640)).resize((320,288),Image.Resampling.LANCZOS)
                board.paste(im,(v*320,32),im);draw.text((v*320+16,330),manifest['direction_labels'][v],fill='#d3c297')
            boards.append(board)
        durations=[round((i+1)*12.5)*10-round(i*12.5)*10 for i in range(count)]
        if action=='death':durations[-1]=1000
        boards[0].save(HERE/f'review/{action}.gif',save_all=True,append_images=boards[1:],loop=0,duration=durations,disposal=2)
    board=Image.new('RGB',(1800,650),(41,46,53));draw=ImageDraw.Draw(board)
    draw.text((20,18),'MM5 TROLL GRUNT  ->  USER-SELECTED MASTER A  ->  FIVE STORED VIEWS',fill='#dfcea6')
    original=Image.open(HERE.parent/'native/mm5_mon_0.png');original=original.crop(original.getbbox())
    original=original.resize((original.width*2,original.height*2),Image.Resampling.NEAREST)
    board.paste(original,(10,555-original.height),original);draw.text((20,590),'Original MM5 / 056.mon',fill='white')
    for v in range(5):
        im=Image.open(HERE/f'references/identity_{v}.png');box=im.getbbox()
        im=im.crop(box);im.thumbnail((285,510),Image.Resampling.LANCZOS)
        x=300+v*300;board.paste(im,(x+(285-im.width)//2,555-im.height),im)
        draw.text((x+20,590),manifest['direction_labels'][v]+(' / exact chosen A' if v==0 else ''),fill='white')
    draw.text((20,622),f'{manifest["coverage"]["exported"]}/160 sprites; full-resolution sources retained; staged 2x atlases.',fill='#b4bdc8')
    board.save(HERE/'review/overview.png')
    contacts=sorted((HERE/'review').glob('contact_*.jpg'))
    all_frames=Image.new('RGB',(2560,800*((len(contacts)+1)//2)),(45,47,51))
    for i,p in enumerate(contacts):all_frames.paste(Image.open(p),(i%2*1280,i//2*800))
    all_frames.save(HERE/'review/all_sprites.jpg',quality=95)
    audit=json.loads((HERE/'review/atlas_edges.json').read_text())
    worst=sorted(audit,key=lambda n:audit[n]['maximum'],reverse=True)[:8]
    edge=Image.new('RGB',(1024,512),(50,55,61));draw=ImageDraw.Draw(edge)
    for i,name in enumerate(worst):
        im=Image.open(HERE/f'aligned_2x/{name}.png');_,score=helpers.edge_candidates(np.array(im))
        yy,xx=np.unravel_index(score.argmax(),score.shape)
        if not score.max():xx,yy=im.width//2,im.getbbox()[1]
        crop=im.crop((xx-24,yy-24,xx+24,yy+24)).resize((128,128),Image.Resampling.NEAREST)
        x=i%4*256;y=i//4*256;draw.text((x+4,y+4),name,fill='white')
        edge.paste(helpers.composite(crop,(240,240,240)),(x,y+25));edge.paste(helpers.composite(crop,(12,12,12)),(x+128,y+25))
    edge.save(HERE/'review/edge_closeups.png')
    print('Built source/atlas viewer, overview, complete animation GIFs and edge review.')


if __name__=='__main__':main()
