"""Restore three native MM8 liquid cycles with bounded, motion-registered AI detail."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import importlib.util
import json
import shutil
import cv2
from scipy.ndimage import gaussian_filter
from PIL import ImageDraw
from common import *

F=Path(__file__).resolve().parent
FAMILIES=dict(water=('hdwtr','wtrtyl'),lava=('hdlav','lavtyl'),tar=('hwoil','tartyl'))
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
    return result
v2=module('native_water_detail',T/'mm6_new_sorpigal_water/restoration_v2/build.py')
v3=module('native_water_seams',T/'mm6_new_sorpigal_water/restoration_v3/build.py')
YY,XX=np.mgrid[:256,:256].astype('float32')


def registered(source,target,values,repeat=True):
    grey=lambda a:cv2.cvtColor(seams.byte(a),cv2.COLOR_RGB2GRAY)
    a,b=grey(source),grey(target)
    if repeat:a,b=np.tile(a,(3,3)),np.tile(b,(3,3))
    flow=cv2.calcOpticalFlowFarneback(a,b,None,.5,3,21,5,7,1.5,0)
    if repeat:flow=flow[256:512,256:512]
    return cv2.remap(values.astype('float32'),XX+flow[:,:,0],YY+flow[:,:,1],
                     cv2.INTER_LINEAR,borderMode=cv2.BORDER_WRAP)


def metrics(frames):
    m=v3.local_seams(frames)
    m['passed']=m['boundary_p95']<1.25*m['interior_p95'] and m['boundary_max']<1.25*m['interior_p999']
    return m


def main():
    receipt_path=F/'generation_receipts.json'
    receipts=json.loads(receipt_path.read_text())
    for r in receipts['outputs']:
        for key in ('raw','prompt','reference'):assert sha(ROOT/r[key])==r[key+'_sha256'],r[key]
    reports={}
    for family,(prefix,base) in FAMILIES.items():
        folder=F/family;folder.mkdir(exist_ok=True)
        atlas=Image.open(F/'raw'/(family+'_atlas.png')).convert('RGB')
        native=[read(P/'references'/('%s%03d.png'%(prefix,i)),256) for i in range(14)]
        deltas=[];raw_frames=[]
        for i,original in enumerate(native):
            x,y=i%4,i//4
            ai=np.asarray(atlas.crop((round(x*atlas.width/4),round(y*atlas.height/4),
                    round((x+1)*atlas.width/4),round((y+1)*atlas.height/4)))
                    .resize((256,256),Image.Resampling.LANCZOS),float)
            raw_frames.append(ai)
            ai=registered(original,ai,ai,repeat=False)
            delta=ai-original
            delta-=gaussian_filter(delta,(3,3,0),mode='wrap')
            deltas.append(v2.periodic_residual(np.clip(.5*delta,-12,12)))
        frames=[]
        for i,original in enumerate(native):
            neighbours=[registered(original,native[j],deltas[j]) for j in ((i-1)%14,(i+1)%14)]
            frames.append(seams.byte(v2.periodic_residual(original+.5*deltas[i]+.25*neighbours[0]+.25*neighbours[1])))
        frame_array=np.asarray(frames)
        np.save(folder/'before_repair.npy',frame_array)
        if (folder/'seam_repair_raw.png').exists():
            # Reviewed MM6/MM7 cross insertion; retain every interior pixel.
            v3.P=folder
            repaired=v3.repair(frame_array.astype(float))
            distance=np.minimum.reduce([XX,YY,255-XX,255-YY]);t=np.clip((24-distance)/8,0,1)
            weight=(t*t*(3-2*t))[:,:,None]
            frames=[]
            for i,frame in enumerate(repaired):
                neighbours=[registered(frame,repaired[j],repaired[j]) for j in ((i-1)%14,(i+1)%14)]
                frames.append(seams.byte(frame+weight*(.25*neighbours[0]+.25*neighbours[1]-.5*frame)))
            assert np.array_equal(np.asarray(frames)[:,24:-24,24:-24],frame_array[:,24:-24,24:-24])
        records=[]
        for i,frame in enumerate(frames):
            name='%s%03d.png'%(prefix,i);path=F/'runtime'/name;save(path,frame)
            records.append(dict(name=name,sha256=sha(path),mean_rgb_shift=(frame.mean((0,1))-native[i].mean((0,1))).tolist(),
                broad_correlation=float(np.corrcoef(gaussian_filter(frame.astype(float),(3,3,0)).ravel(),
                gaussian_filter(native[i],(3,3,0)).ravel())[0,1]),seams=metrics([frame])))
        shutil.copy2(F/'runtime'/(prefix+'000.png'),F/'runtime'/(base+'.png'))
        records.append(dict(name=base+'.png',sha256=sha(F/'runtime'/(base+'.png')),source_frame=prefix+'000'))
        for label,images in [('native',native),('raw',raw_frames),('restored',frames)]:
            views=[Image.fromarray(np.tile(seams.byte(a),(3,3,1))) for a in images]
            views[0].save(folder/(label+'_repeat.png'))
            views[0].save(folder/(label+'_loop.webp'),save_all=True,append_images=views[1:],duration=117,loop=0,lossless=True)
            sheet=Image.new('RGB',(7*256,2*280),'#202933');draw=ImageDraw.Draw(sheet)
            for i,a in enumerate(images):
                draw.text((i%7*256+4,i//7*280+4),label+' '+str(i),fill='white')
                sheet.paste(Image.fromarray(np.roll(seams.byte(a),(128,128),(0,1))),(i%7*256,i//7*280+24))
            sheet.save(folder/(label+'_offsets.png'))
        steps=lambda arrays:[float(np.abs(arrays[(i+1)%14].astype(float)-arrays[i]).mean()) for i in range(14)]
        original_steps=steps(native);restored_steps=steps(frames)
        reports[family]=dict(files=records,frame_ticks=15,ticks_per_second=128,
            native_steps=original_steps,restored_steps=restored_steps,
            loop_step_ratio=restored_steps[-1]/np.mean(restored_steps),
            native_loop_step_ratio=original_steps[-1]/np.mean(original_steps),
            before_seams=metrics(frame_array),seams=metrics(frames),
            repaired=(folder/'seam_repair_raw.png').exists(),
            source_files={n:sha(P/'references'/(n+'.png')) for n in [prefix+'%03d'%i for i in range(14)]+[base]})
        print(family,reports[family]['seams'],'loop ratio',reports[family]['loop_step_ratio'],flush=True)
    report=dict(status='liquid_candidates_not_installed',runtime_size=256,
        size_note='Native hardware animation frames are already256px;128px static fallbacks become256px, matching x2 land array.',
        fallback_note='Static liquid fallbacks use restored frame0, matching accepted MM6/MM7 workflow.',
        families=reports,receipts_sha256=sha(receipt_path),script_sha256=sha(Path(__file__)),
        material_registry_sha256=sha(ROOT/'assets_dev/engine/rendering/surface_materials.yml'),
        helper_hashes={str(path.relative_to(T)):sha(path) for path in
        [T/'mm6_new_sorpigal_water/restoration_v2/build.py',T/'mm6_new_sorpigal_water/restoration_v3/build.py']})
    (F/'build.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
