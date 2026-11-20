"""Extract compact sheets, register one anatomical scale, and preserve native motion landmarks."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image,ImageDraw
from scipy.optimize import minimize
from scipy import ndimage as ndi

F=Path(__file__).resolve().parent;R=F.parent
sys.path.insert(0,str(R));import process,calibrate,tone
sys.path.insert(0,str(R/'front_attack_grid_trial'));from foot_alignment import translate,feet
from tonal_curve import grade

def landmark(im,action):
    a=np.asarray(im)[:,:,3]>=128
    ys,xs=np.where(a);bottom=int(ys.max())+1
    # Upright/contact samples use lower legs, retaining moving native support positions.
    # Prone samples use the body component rather than a separate dropped weapon.
    if action=='d' and bottom-int(ys.min())<150:
        a=ndi.binary_opening(a,structure=np.ones((7,7)))
        labels,_=ndi.label(a);sizes=np.bincount(labels.ravel());sizes[0]=0
        ys,xs=np.where(labels==int(np.argmax(sizes)))
        return [(float(xs.min())+float(xs.max())+1)/2,float(ys.max()+1)]
    band=80 if action in ['w','n','d'] else 20
    ys,xs=np.where(a[max(0,bottom-band):bottom])
    return [(float(xs.min())+float(xs.max())+1)/2,float(bottom)]

def run(key):
    data=json.loads((F/'jobs.json').read_text());j=data['jobs'][key]
    rawpath=F/j.get('selected_raw','raw/'+key+'_v1.png');raw=Image.open(rawpath)
    cols,rows=j['columns'],j['rows'];crop=j['crop_native'];w,h=crop[2]-crop[0],crop[3]-crop[1]
    cw,ch=raw.width/cols,raw.height/rows;rx,ry=2*w/cw,2*h/ch
    assert abs(rx/ry-1)<.025,('Changed grid aspect',key,raw.size)
    ratio=(rx+ry)/2;arts=[];natives=[];records=[]
    for i,n in enumerate(j['frames']):
        rect=[round(i%cols*cw),round(i//cols*ch),round((i%cols+1)*cw),round((i//cols+1)*ch)]
        origin=rect[:2];rect=j.get('extraction_overrides',{}).get(n,rect)
        clean=process.extract(raw.crop(rect),n);bb=clean.getbbox()
        assert bb and bb[0]>0 and bb[1]>0 and bb[2]<clean.width and bb[3]<clean.height,(key,n,'cell edge',bb,clean.size)
        clean.save(F/'cleaned'/(n+'.png'))
        im=clean.convert('RGBa').resize((round(clean.width*ratio),round(clean.height*ratio)),Image.Resampling.LANCZOS).convert('RGBA')
        canvas=Image.new('RGBA',(576,576));offset=[32+crop[k]*2+round((rect[k]-origin[k])*ratio) for k in range(2)];canvas.paste(im,tuple(offset));arts.append(canvas)
        native=Image.new('RGBA',(576,576));native.paste(process.queue.native(R,n).resize((512,512),Image.Resampling.NEAREST),(32,32));natives.append(native)
        records.append({'raw_cell':rect,'raw_bbox':bb,'normalization_scale':ratio})
    am=[calibrate.body(im) for im in arts];nm=[calibrate.body(im) for im in natives]
    def objective(v):
        num=den=0
        for i,(a,b) in enumerate(zip(am,nm)):
            row=i//cols;c=calibrate.warp(a,[v[0],v[1+row*2],v[2+row*2]])
            num+=2*(c*b).sum();den+=(c*c+b*b).sum()
        return 1-num/max(den,1e-6)+.025*(v[0]-1)**2
    values=j.get('frozen_calibration')
    if values is None:values=minimize(objective,[1]+[0]*(rows*2),method='Powell',bounds=[(.78,1.08)]+[(-24,24)]*(rows*2),options={'maxiter':50,'xtol':.0002}).x.tolist()
    scale=values[0];sampling=2/(ratio*scale);assert sampling>=2,(key,sampling)
    sheet=Image.new('RGB',(len(j['frames'])*256,3*280),(35,35,35));draw=ImageDraw.Draw(sheet)
    reg=json.loads((F/'registration.json').read_text()) if (F/'registration.json').exists() else {}
    for i,(n,art,native,rec) in enumerate(zip(j['frames'],arts,natives,records)):
        row=i//cols;dx,dy=values[1+row*2],values[2+row*2]
        out=process.fix(art.convert('RGBa').transform((576,576),Image.Transform.AFFINE,(1/scale,0,288-(288+4.5*dx)/scale,0,1/scale,288-(288+4.5*dy)/scale),Image.Resampling.BICUBIC).convert('RGBA'),n)
        source_landmark=landmark(native,j['action']);art_landmark=landmark(out,j['action'])
        if j['action']=='a' and j['view']==0:
            a,b=feet(native),feet(out)
            source_landmark=[a['stance_center_x'],a['sole_y']];art_landmark=[b['stance_center_x'],b['sole_y']]
        if n in j.get('contact_roi',{}):
            roi=j['contact_roi'][n]
            source_landmark[1]=int(np.where(np.asarray(native.crop(roi))[:,:,3]>=128)[0].max())+1+roi[1]
            art_landmark[1]=int(np.where(np.asarray(out.crop(roi))[:,:,3]>=128)[0].max())+1+roi[1]
        offset=[int(np.rint(a-b)) for a,b in zip(source_landmark,art_landmark)]
        offset=j.get('landmark_override',{}).get(n,offset)
        out=translate(out,offset);bb=out.getbbox();assert bb[0]>3 and bb[1]>3 and bb[2]<573 and bb[3]<573,(n,bb)
        out.save(F/'registered_2x'/(n+'.png'))
        final=grade(out,n);assert np.array_equal(np.array(final)[:,:,3],np.array(out)[:,:,3]);final.save(F/'toned_2x'/(n+'.png'))
        assert process.spill(final,n)['max_score']==0
        reg[n]={**rec,'job':key,'raw':str(rawpath.relative_to(F)),'shared_calibration':values,'generated_pixels_per_native_pixel':sampling,'native_landmark':source_landmark,'generated_landmark_before':art_landmark,'integer_translation_2x':offset,'canvas_origin_px':[-32,-32],'aligned_size_px':[576,576],'logical_size':[256,256],'status':'processed_unreviewed'}
        overlay=np.zeros((576,576,4),np.uint8);overlay[:,:,0]=np.array(native)[:,:,3];overlay[:,:,1]=np.array(final)[:,:,3];overlay[:,:,3]=255
        for r,pic in enumerate([native,final,Image.fromarray(overlay)]):
            bg=Image.new('RGBA',pic.size,(35,35,35,255));bg.alpha_composite(pic);sheet.paste(bg.resize((256,256)).convert('RGB'),(i*256,r*280+24));draw.text((i*256+3,r*280+4),n+' '+['native','enhanced 2x','native red / art green'][r],fill='white')
    sheet.save(F/'review'/(key+'_registration.png'));process.save(F/'registration.json',reg)
    j.update(status='processed_unreviewed',selected_raw=str(rawpath.relative_to(F)),calibration=values,actual_size=list(raw.size),sampling=sampling,generation={'raw':{'path':str(rawpath.relative_to(F)),'sha256':process.queue.sha(rawpath)},'prompt':{'path':j['prompt'],'sha256':process.queue.sha(F/j['prompt'])},'references':[{'path':p,'sha256':process.queue.sha(F/p)} for p in j['references']]})
    process.save(F/'jobs.json',data);print(key,len(j['frames']),'frames;',round(sampling,2),'generated/native;',len(reg),'sequence frames processed',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('jobs',nargs='+');a=p.parse_args()
    for key in a.jobs:run(key)
