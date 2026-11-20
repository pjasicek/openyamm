"""Crop and preview the direct AI experiment; no per-frame alignment or synthetic redraw."""
from pathlib import Path
import json,math
from PIL import Image,ImageDraw
import numpy as np
ROOT=Path(__file__).resolve().parent
KEY=(255,0,255)
source=Image.open(ROOT/'original_attack_3x2_magenta.png').convert('RGB')
restored=Image.open(ROOT/'attack_restored_v1.png').convert('RGB')
# Equal grid partition, with the SAME extra margin around every cell to preserve minor AI grid spill.
# Preserve the raw sheet and original crop coordinates. Do not hide pose/alignment drift by recentering.
w,h=restored.size
cw=math.ceil(w/3);ch=math.ceil(h/2);pad=20
frames=[];native=[];records=[]
(ROOT/'frames_magenta').mkdir(exist_ok=True)
(ROOT/'frames_rgba_preview').mkdir(exist_ok=True)
for i in range(6):
    x=round((i%3)*w/3);y=round((i//3)*h/2)
    box=(x-pad,y-pad,x+cw+pad,y+ch+pad)
    frame=Image.new('RGB',(cw+2*pad,ch+2*pad),KEY)
    # Seam in empty space separates the frame-e sword spill from frame d.
    # Canvas origins stay on the equal grid; these limits only exclude neighboring figures.
    xseams=[0,530,round(2*w/3),w];yseams=[0,round(h/2),h]
    col=i%3;row=i//3
    clipped=(max(xseams[col],box[0]),max(yseams[row],box[1]),
        min(xseams[col+1],box[2]),min(yseams[row+1],box[3]))
    frame.paste(restored.crop(clipped),(clipped[0]-box[0],clipped[1]-box[1]))
    frame.save(ROOT/'frames_magenta'/f'gobat{"abcdef"[i]}0_ai.png')
    # Experimental key extraction only; retain opaque originals as authoritative outputs.
    a=np.array(frame).astype(np.float32)
    r,g,b=a[:,:,0],a[:,:,1],a[:,:,2]
    dominance=np.minimum(r,b)-g
    strength=np.clip((dominance-35)/100,0,1)
    alpha=1-strength
    rgba=np.dstack([a,np.round(alpha*255)]).astype('uint8')
    rgba[alpha==0,:3]=0
    cutout=Image.fromarray(rgba)
    cutout.save(ROOT/'frames_rgba_preview'/f'gobat{"abcdef"[i]}0_ai.png')
    matte=Image.new('RGBA',cutout.size,(47,50,49,255));matte.alpha_composite(cutout)
    frames.append(matte.convert('RGB'))
    nx=(i%3)*768;ny=(i//3)*640
    original=source.crop((nx,ny,nx+768,ny+640))
    normalized=Image.new('RGB',(cw+2*pad,ch+2*pad),KEY)
    normalized.paste(original.resize((cw,ch),Image.Resampling.NEAREST),(pad,pad))
    native.append(normalized)
    records.append({'source':f'gobat{"abcdef"[i]}0.bmp','crop_box_in_generated_sheet':box,'content_extraction_box':clipped,
        'keyed_alpha_bounds':cutout.getchannel('A').getbbox(),'duration_seconds':.125})
# Each preview cell has the same fixed scale and crop, with no independent foot/face alignment.
comparison=[]
for i in range(6):
    row=Image.new('RGB',(900,450),(47,50,49))
    left=native[i].resize((450,375),Image.Resampling.NEAREST)
    right=frames[i].resize((450,375),Image.Resampling.LANCZOS)
    row.paste(left,(0,45));row.paste(right,(450,45))
    d=ImageDraw.Draw(row);d.text((10,12),f'Original gobat{"abcdef"[i]}0',fill='white')
    d.text((460,12),'AI sheet crop / experimental key',fill='white')
    comparison.append(row)
delays=[120,130,120,130,120,130]
comparison[0].save(ROOT/'comparison_playback.gif',save_all=True,append_images=comparison[1:],duration=delays,loop=0)
frames[0].save(ROOT/'attack_playback.gif',save_all=True,append_images=frames[1:],duration=delays,loop=0)
contact=Image.new('RGB',(900,450*6),(47,50,49))
for i,frame in enumerate(comparison):contact.paste(frame,(0,450*i))
contact.save(ROOT/'comparison_all_frames.png')
# Preserve keyed crops in one unlabeled six-frame strip for further experiments.
strip=Image.new('RGBA',((cw+2*pad)*6,ch+2*pad))
for i in range(6):
    with Image.open(ROOT/'frames_rgba_preview'/f'gobat{"abcdef"[i]}0_ai.png') as f:strip.paste(f,(i*(cw+2*pad),0))
strip.save(ROOT/'attack_rgba_preview_1x6.png')
(ROOT/'preview_manifest.json').write_text(json.dumps({'generated_size':[w,h],'requested_size':[3456,1920],
    'crop_cell_size':[cw+2*pad,ch+2*pad],'common_padding_px':pad,'frames':records,
    'alpha':'Approximate chroma-key extraction for review, not native generated alpha or certified clean matte.',
    'alignment':'Equal sheet cells plus common padding. No per-frame pose normalization.',
    'gif_durations_ms':delays},indent=2)+'\n')
print(json.dumps({'generated_size':[w,h],'crop_size':[cw+40,ch+40],'frames':records},indent=2))
