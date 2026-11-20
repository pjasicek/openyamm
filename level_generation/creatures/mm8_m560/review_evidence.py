"""All-frame contacts and magnified final atlas contours on dark and light backgrounds."""
import json
import numpy as np
from scipy import ndimage as ndi
from PIL import Image,ImageDraw
from process import ROOT,queue,save,spill

def bg(im,color):
    out=Image.new('RGBA',im.size,(*color,255));out.alpha_composite(im);return out.convert('RGB')

def run():
    m=json.loads((ROOT/'draft_manifest.json').read_text())
    batches=json.loads((ROOT/'batches.json').read_text())
    pages=[Image.open(ROOT/p['base']).convert('RGBA') for p in m['pages']]
    candidates=[]
    for key,batch in batches.items():
        sheet=Image.new('RGB',(256*len(batch['frames']),560),(35,35,35));draw=ImageDraw.Draw(sheet)
        for i,name in enumerate(batch['frames']):
            f=m['frames'][name];x,y,w,h=f['atlas_xywh'];tile=pages[f['page']].crop((x,y,x+w,y+h))
            aligned=Image.new('RGBA',f['aligned_canvas_size_px']);aligned.paste(tile,f['crop_in_aligned_px'][:2])
            native=Image.new('RGBA',aligned.size);native.paste(queue.native(ROOT,name).resize((512,512),Image.Resampling.NEAREST),(32,32))
            sheet.paste(bg(native.resize((256,256),Image.Resampling.LANCZOS),(35,35,35)),(i*256,24))
            thumb=aligned.convert('RGBa').resize((256,256),Image.Resampling.LANCZOS).convert('RGBA')
            sheet.paste(bg(thumb,(235,235,235)),(i*256,300));draw.text((i*256+4,4),name,fill='white')
            a=np.asarray(tile);rgb=a[:,:,:3].astype(float);alpha=a[:,:,3]/255
            band=(alpha>0)&(ndi.distance_transform_edt(alpha>=.98)<=4)
            score=np.maximum(np.minimum(rgb[:,:,0],rgb[:,:,2])-rgb[:,:,1]-9,np.minimum(rgb[:,:,1],rgb[:,:,2])-rgb[:,:,0]-9)*alpha
            score[~band]=-1e9
            yy,xx=np.unravel_index(np.argmax(score),score.shape)
            candidates.append((float(score[yy,xx]),name,tile,(int(xx),int(yy))))
        sheet.save(ROOT/f'review/{key}_final.png')
    candidates.sort(key=lambda item:-item[0])
    chosen=candidates[:12]
    sheet=Image.new('RGB',(6*250,2*530),(35,35,35));draw=ImageDraw.Draw(sheet)
    for i,(score,name,tile,(x,y)) in enumerate(chosen):
        col=i%6;row=i//6;crop=tile.crop((x-20,y-20,x+21,y+21))
        draw.text((col*250+3,row*530+3),name+' matte '+str(round(score,1)),fill='white')
        for j,color in enumerate([(18,18,18),(235,235,235)]):
            sheet.paste(bg(crop,color).resize((246,246),Image.Resampling.NEAREST),(col*250+2,row*530+28+j*250))
    sheet.save(ROOT/'review/worst_edges.png')
    save(ROOT/'review/edge_candidates.json',{'selection':'Actual magenta/cyan excess beyond measured native allowance 9 on visible final contour, even below rejection score; no empty transparent samples.',
        'patches':[{'frame':name,'excess':score,'xy':list(pos)} for score,name,tile,pos in chosen]})
    print('Prepared',len(batches),'complete native/final contacts and 12 worst contour patches')

if __name__=='__main__':run()
