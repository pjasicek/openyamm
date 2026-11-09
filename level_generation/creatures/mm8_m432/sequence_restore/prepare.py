"""Prepare coherent native action/view grids and resume the complete family from retained artwork."""
from pathlib import Path
import sys,json,math
from PIL import Image

F=Path(__file__).resolve().parent;R=F.parent
sys.path.insert(0,str(R))
import process

def run():
    if (F/'jobs.json').exists():
        print('Existing sequence queue retained');return
    for name in ['references','prompts','raw','review','registered_2x','toned_2x','cleaned']:
        (F/name).mkdir(parents=True,exist_ok=True)
    src=json.loads((R/'sources.json').read_text())
    jobs={}
    descriptions={'d':'collapse and final resting poses; the sword is released with an exposed metal/gold grip, never an extra hand',
                  'f':'idle fidget sequence', 'n':'brief hit-reaction sequence', 'w':'walking cycle with alternating planted and lifted feet'}
    for action,views in [('d',range(2,5)),('f',range(5)),('n',range(5)),('w',range(5))]:
        for view in views:
            names=sorted(n for n in src['sources'] if n.startswith('m432'+action) and n.endswith(str(view)))
            if action=='d':names+=sorted(n for n in src['sources'] if n.startswith('m432x') and n.endswith(str(view)))
            native=[process.queue.native(R,n) for n in names];bbs=[im.getbbox() for im in native]
            crop=[min(b[0] for b in bbs)-6,min(b[1] for b in bbs)-6,max(b[2] for b in bbs)+6,max(b[3] for b in bbs)+6]
            w,h=crop[2]-crop[0],crop[3]-crop[1];cols=4 if action=='w' else 3;rows=2
            sheet=Image.new('RGBA',(cols*w,rows*h),(255,0,255,255))
            for i,im in enumerate(native):sheet.alpha_composite(im.crop(crop),(i%cols*w,i//cols*h))
            key=action+'_v'+str(view);ref='references/'+key+'_native.png';sheet.convert('RGB').save(F/ref)
            identity='references/'+key+'_identity.png'
            name='m432sa'+str(view);path=R/'detail_upgrade/toned_2x'/(name+'.png')
            if not path.exists():path=R/'detail_upgrade/review'/(name+'_trial_2x.png')
            im=Image.open(path).convert('RGBA');bb=im.getbbox();im=im.crop((bb[0]-12,bb[1]-12,bb[2]+12,bb[3]+12))
            bg=Image.new('RGBA',im.size,(255,0,255,255));bg.alpha_composite(im);bg.convert('RGB').save(F/identity)
            prompt=f'''Use case: style-transfer. Restore native MM8 Dark Elf Warrior sprites into detailed, faithful game artwork.
Input 1 is the exact native pose and layout authority: {cols} columns by {rows} rows, row-major order {', '.join(names)}. {'Last cell must remain empty magenta.' if len(names)<cols*rows else 'Every cell occupied exactly once.'}
Restore this entire {descriptions[action]} for stored view {view} together in one coherent sheet. Input 2 is the accepted character/material identity in this view ONLY; do not substitute its standing pose for the native poses. Native input controls head direction, torso rotation, all limbs, sword angles/length/foreshortening and foot lifting. One character per occupied cell, no missing/extra/duplicate poses.
All cells use the same {w}x{h} native-coordinate crop with sword-inclusive motion extremes and six-pixel padding. Keep source-relative character positions, scale and equal cells. Sheet aspect must remain {cols*w}:{rows*h}; deliver the largest raster available at that aspect, with at least two actual generated pixels per native pixel. Do not stretch, recenter or equal-height fit individual figures; prone poses stay low, upright poses keep native height. Do not clip tips or feet.
Preserve dark reddish-brown elf skin, pointed ears, swept-back silver-white hair, near-black fitted armor/gloves/boots, round studded shoulder armor, restrained gold fittings, green sleeve bands, muted teal chest/back disk only where native visibility shows it, and ONE long narrow steel sword with gold hilt. No extra disks, fingers, hands, weapons or glowing eyes. Keep original dark tonal weight; refine coherent face/hair/material detail across the sequence.
Flat magenta RGB255,0,255 background, no gradients, shadows, spill, labels or grid lines. Generate base palette only.''' 
            pp='prompts/'+key+'_v1.txt';(F/pp).write_text(prompt+'\n')
            jobs[key]={'frames':names,'action':action,'view':view,'columns':cols,'rows':rows,'crop_native':crop,'references':[ref,identity],'prompt':pp,'status':'pending','estimated_sampling_at_observed_1572864_pixels':math.sqrt(1572864/(cols*rows*w*h))}
    process.save(F/'jobs.json',{'jobs':jobs,'minimum_sampling':2,'scope':'Complete m432; retain existing enhanced checkpoints and generate only uncovered sequences.'})
    print('Prepared',len(jobs),'sequence grids for',sum(len(j['frames']) for j in jobs.values()),'native frames')

if __name__=='__main__':run()
