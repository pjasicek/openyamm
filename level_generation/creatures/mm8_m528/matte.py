"""Deterministic chroma matting/decontamination of approved RGB art; no AI redraw or pose edits.

This is an estimated foreground reconstruction, not recovery of unknown original alpha.
Assumes this goblin has no intended magenta material. Keeps clean foreground RGB unchanged.
"""
from pathlib import Path
import json
import numpy as np
from scipy import ndimage
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'edge_cleanup'


def extract(rgb):
    c=np.array(rgb,dtype=np.float64)/255
    dominance=np.minimum(c[:,:,0],c[:,:,2])-c[:,:,1]
    # Confident natural foreground and actual local magenta background samples.
    core=dominance<=8/255+1e-9
    background=(dominance>210/255)&(c[:,:,0]>.9)&(c[:,:,2]>.9)
    distance,indices=ndimage.distance_transform_edt(~core,return_indices=True)
    _,bgindices=ndimage.distance_transform_edt(~background,return_indices=True)
    f=c[indices[0],indices[1]]
    b=c[bgindices[0],bgindices[1]]
    vector=f-b
    alpha=np.clip(np.sum((c-b)*vector,axis=2)/np.maximum(np.sum(vector*vector,axis=2),1e-8),0,1)
    alpha[core]=1
    # Suppress low-level variation in the generated matte far from any actual silhouette.
    alpha[distance>7]=0
    alpha[background]=0
    recovered=(c-(1-alpha[:,:,None])*b)/np.maximum(alpha[:,:,None],1/255)
    # Residual pink is perpendicular to the estimated composite line. Limit magenta excess
    # using the nearest trustworthy foreground chroma. Remove the shared red/blue component;
    # subtracting only blue fails when red is smaller, and can turn a pink fringe red.
    # Equal subtraction preserves the red-blue difference (warm/cool foreground shading).
    limit=np.minimum(f[:,:,0],f[:,:,2])-f[:,:,1]+2/255
    excess=np.maximum(0,np.minimum(recovered[:,:,0],recovered[:,:,2])-recovered[:,:,1]-limit)
    recovered[:,:,0]-=excess
    recovered[:,:,2]-=excess
    recovered=np.clip(recovered,0,1)
    recovered[core]=c[core]
    recovered[alpha==0]=0
    rgba=np.dstack([np.round(recovered*255),np.round(alpha*255)]).astype('uint8')
    return Image.fromarray(rgba),{'clean_core_pixels':int(core.sum()),
        'changed_visible_edge_pixels':int(((alpha>0)&~core).sum()),
        'alpha_pixels':int((rgba[:,:,3]>0).sum())}


def composite(im,color):
    bg=Image.new('RGBA',im.size,(*color,255));bg.alpha_composite(im);return bg.convert('RGB')


def build():
    OUT.mkdir(exist_ok=True);(OUT/'frames_rgba').mkdir(exist_ok=True)
    frames=[];old=[];report=[]
    for letter in 'abcdef':
        name=f'gobat{letter}0_ai.png'
        rgb=Image.open(ROOT/'frames_magenta'/name).convert('RGB')
        result,stats=extract(rgb)
        result.save(OUT/'frames_rgba'/name);frames.append(result)
        old.append(Image.open(ROOT/'frames_rgba_preview'/name).convert('RGBA'))
        box=result.getchannel('A').getbbox()
        assert box and 0<box[0]<box[2]<result.width and 0<box[1]<box[3]<result.height
        report.append({'file':name,'bounds':box,**stats})
    width,height=frames[0].size
    atlas=Image.new('RGBA',(width*6,height))
    for i,f in enumerate(frames):atlas.paste(f,(width*i,0))
    atlas.save(OUT/'attack_cleaned_1x6.png')
    sheet=Image.new('RGBA',(width*3,height*2))
    for i,f in enumerate(frames):sheet.paste(f,(width*(i%3),height*(i//3)))
    sheet.save(OUT/'attack_cleaned_3x2.png')
    # Never filter straight RGB carrying a key-color background. Filter premultiplied color and alpha together.
    small_width=width//2;small_height=height//2
    small=Image.new('RGBA',(small_width*6,small_height))
    for i,f in enumerate(frames):
        tile=f.convert('RGBa').resize((small_width,small_height),Image.Resampling.LANCZOS).convert('RGBA')
        small.paste(tile,(i*small_width,0))
    small.save(OUT/'attack_cleaned_half_size.png')
    delays=[120,130,120,130,120,130]
    playback=[composite(f,(47,50,49)) for f in frames]
    playback[0].save(OUT/'attack_cleaned.gif',save_all=True,append_images=playback[1:],duration=delays,loop=0)
    # Native-pixel close-up; enlarge with nearest neighbor solely for inspecting edge colors.
    box=(334,120,435,219)
    size=((box[2]-box[0])*5,(box[3]-box[1])*5)
    evidence=Image.new('RGB',(size[0]*3,size[1]*2+60),(40,40,40));draw=ImageDraw.Draw(evidence)
    for row,color in enumerate([(45,45,45),(235,235,235)]):
        rgb=Image.open(ROOT/'frames_magenta/gobatb0_ai.png').convert('RGB').crop(box)
        pictures=[rgb,composite(old[1].crop(box),color),composite(frames[1].crop(box),color)]
        for col,(title,pic) in enumerate(zip(['Generated RGB','Old alpha-only key','Color-unmixed RGBA'],pictures)):
            x=col*size[0];y=row*(size[1]+30)
            evidence.paste(pic.resize(size,Image.Resampling.NEAREST),(x,y+30));draw.text((x+8,y+8),title,fill='white')
    evidence.save(OUT/'guard_before_after.png')
    # All six full figures on both light and dark backgrounds at original crop resolution.
    for label,color in [('dark',(35,38,37)),('light',(235,235,235))]:
        composite(sheet,color).save(OUT/f'all_frames_{label}.png')
    (OUT/'validation.json').write_text(json.dumps({'method':'local two-color alpha estimate and edge RGB unmixing',
        'limitations':'Estimated matte; intended magenta would be removed. Thin details without uncontaminated cores can lose opacity.',
        'frames':report,'resize':'premultiplied-alpha Lanczos','original_art_modified':False},indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':build()
