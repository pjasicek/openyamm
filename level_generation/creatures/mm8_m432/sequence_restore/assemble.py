"""Assemble retained and new native frames into one reviewable package; no automatic acceptance."""
from pathlib import Path
import sys,json,shutil,argparse
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage as ndi

F=Path(__file__).resolve().parent;R=F.parent;G=R/'complete';D=R/'detail_upgrade';T=R/'front_attack_grid_trial'
sys.path.insert(0,str(R));import process,materials,package,review_evidence
from process_sequence import landmark
from tonal_curve import grade
sys.path.insert(0,str(T));from foot_alignment import translate

def run(partial=False,only=None):
    for folder in ['toned_2x','cleaned','masks_2x','previews','native_variants','review/variants']:
        (G/folder).mkdir(parents=True,exist_ok=True)
    for name in ['sources.json','batches.json','viewer_template.html','browser_checks.py']:
        shutil.copy2(R/name,G/name)
    src=json.loads((R/'sources.json').read_text());selected={}
    dr=json.loads((D/'registration.json').read_text());dj=json.loads((D/'jobs.json').read_text())['jobs']
    for key,j in dj.items():
        if j['status'] not in ['accepted_detail_and_placement','processed_unreviewed']:continue
        for n in j['frames']:
            selected[n]={'path':str((D/'toned_2x'/(n+'.png')).relative_to(R)),
                         'mask':str((D/'masks_2x'/(n+'.png')).relative_to(R)),
                         'sampling':dr[n]['generated_pixels_per_native_pixel'],'origin':'detail_upgrade','job':key}
    trial=json.loads((D/'review/registration.json').read_text())['identity_front_v1']
    selected['m432sa0']={'path':'detail_upgrade/review/m432sa0_trial_2x.png','mask':'detail_upgrade/masks_2x/m432sa0.png',
                          'sampling':2/(trial['shared_normalization_scale']*trial['shared_registration_values'][0]),'origin':'detail_identity_trial'}
    tm=json.loads((T/'manifest.json').read_text())
    for n,f in tm['frames'].items():
        selected[n]={'path':'front_attack_grid_trial/runtime_aligned_2x/'+n+'.png',
                     'mask':'front_attack_grid_trial/masks_2x/'+n+'.png','sampling':f['sampling_generated_per_native'],
                     'origin':'front_attack_grid_trial','foot_alignment_already_applied':True}
    fr=json.loads((F/'registration.json').read_text())
    fj=json.loads((F/'jobs.json').read_text())['jobs']
    for n,r in fr.items():
        if n not in fj[r['job']].get('deliver_frames',fj[r['job']]['frames']):continue
        selected[n]={'path':'sequence_restore/toned_2x/'+n+'.png','sampling':r['generated_pixels_per_native_pixel'],
                     'origin':'sequence_restore','job':r['job'],'foot_alignment_already_applied':True}
    assert partial or set(selected)==set(src['sources']),sorted(set(src['sources'])-set(selected))
    config=materials.settings();config['enhanced_support']={'seed':'coverage>165, G-R>10, G>=B-10, opaque distance>2, connected area>=12','falloff':'full to4 pixels, zero at6 pixels','source':'enhanced RGB and alpha only'}
    reg={}
    previous=json.loads((G/'selection.json').read_text()) if only else {}
    for n,rec in sorted(selected.items()):
        if only and n not in only:
            old=previous[n]
            assert old['path']==rec['path'] and old['sampling']==rec['sampling'],('Changed selection outside requested rebuild',n)
            assert process.queue.sha(R/old.get('ungraded_master',old['path']))==old['source_sha256'],('Changed source outside requested rebuild',n)
            selected[n]=old
            reg[n]={'canvas_origin_px':[-32,-32],'aligned_size_px':[576,576],'logical_size':[256,256],**old}
            continue
        source=R/rec['path'];im=Image.open(source).convert('RGBA');assert rec['sampling']>=2
        if rec['origin']=='front_attack_grid_trial':
            tj=json.loads((T/'registration.json').read_text())['selected'][n]
            source=T/tj['image'].replace('toned_2x/','registered_2x/')
            shift=json.loads((T/'foot_alignment.json').read_text())['frames'][n]['translation_2x_px']
            im=grade(translate(Image.open(source).convert('RGBA'),shift),n)
            rec['ungraded_master']=str(source.relative_to(R));rec['pregrade_integer_shift_2x']=shift
            rec.pop('mask',None)
        native=Image.new('RGBA',(576,576));native.paste(process.queue.native(R,n).resize((512,512),Image.Resampling.NEAREST),(32,32))
        maskpath=R/rec.get('mask','__absent__')
        if maskpath.exists():mask=Image.open(maskpath).convert('L')
        else:
            mask=materials.masks(im,config);a=np.asarray(im);r,g,b=np.moveaxis(a[:,:,:3].astype(float),-1,0)
            seed=(mask>165)&(g-r>10)&(g>=b-10)&(ndi.distance_transform_edt(a[:,:,3]>=250)>2)
            labels,_=ndi.label(seed);sizes=np.bincount(labels.ravel());sizes[0]=0;seed=sizes[labels]>=12
            support=np.clip((6-ndi.distance_transform_edt(~seed))/2,0,1) if seed.any() else np.zeros(seed.shape)
            mask=Image.fromarray(np.round(mask*support).astype(np.uint8))
        rec['source_sha256']=process.queue.sha(source)
        shift=[0,0]
        if not rec.get('foot_alignment_already_applied'):
            action='d' if n[4] in ['d','x'] else n[4]
            a,b=landmark(native,action),landmark(im,action);shift=[int(np.rint(x-y)) for x,y in zip(a,b)]
            im=translate(im,shift);mask=translate(mask,shift)
            rec['native_landmark']=a;rec['enhanced_landmark_before']=b
        rec['delivery_integer_shift_2x']=shift
        protection=json.loads((F/'mask_protection.json').read_text()) if (F/'mask_protection.json').exists() else {}
        if n in protection:
            brush=ImageDraw.Draw(mask)
            for polygon in protection[n]:brush.polygon([tuple(p) for p in polygon],fill=0)
        im=process.fix(im,n);assert process.spill(im,n)['max_score']==0
        im.save(G/'toned_2x'/(n+'.png'));im.save(G/'cleaned'/(n+'.png'));mask.save(G/'masks_2x'/(n+'.png'))
        for pal in materials.PALETTES:
            variant=materials.recolor(im,mask,pal,config);assert np.array_equal(np.asarray(variant)[:,:,3],np.asarray(im)[:,:,3]);assert pal!=433 or np.array_equal(variant,im)
            variant.save(G/'previews'/(n+'_'+str(pal)+'.png'));process.queue.native(R,n,pal).save(G/'native_variants'/(n+'_'+str(pal)+'.png'))
        reg[n]={'canvas_origin_px':[-32,-32],'aligned_size_px':[576,576],'logical_size':[256,256],**rec}
    process.save(G/'selection.json',selected);process.save(G/'calibration_registration.json',reg);process.save(G/'material_settings.json',config)
    package.ROOT=G;package.run(partial=partial);review_evidence.ROOT=G;review_evidence.run()
    batches=json.loads((G/'batches.json').read_text())
    for key,batch in batches.items():
        if not all(n in selected for n in batch['frames']):continue
        sheet=Image.new('RGB',(256*len(batch['frames']),4*280),(35,35,35));draw=ImageDraw.Draw(sheet)
        for i,n in enumerate(batch['frames']):
            im=Image.open(G/'toned_2x'/(n+'.png')).convert('RGBA');a=np.array(im);m=np.asarray(Image.open(G/'masks_2x'/(n+'.png')))/255
            a[:,:,:3]=np.round(a[:,:,:3]*(1-.65*m[:,:,None])+np.array([255,70,30])*.65*m[:,:,None]).astype(np.uint8)
            pics=[Image.open(G/'previews'/(n+'_'+str(p)+'.png')).convert('RGBA') for p in materials.PALETTES]+[Image.fromarray(a)]
            for row,pic in enumerate(pics):
                bg=Image.new('RGBA',pic.size,(35,35,35,255));bg.alpha_composite(pic);sheet.paste(bg.resize((256,256)).convert('RGB'),(i*256,row*280+24));draw.text((i*256+4,row*280+4),n+' '+str([433,434,435,'mask'][row]),fill='white')
        sheet.save(G/'review/variants'/(key+'.png'))
    ledgerpath=R.parent/'mm8_remaining/progress.json';ledger=json.loads(ledgerpath.read_text());ledger['families']['m432'].update(status='partial',active_approach='complete_native_sequence_restore',resume='Continue sequence_restore/jobs.json, preserving reviewed compact grids and reused detail_upgrade/front_attack_grid_trial checkpoints. Run sequence_restore/assemble.py after repairs, review complete/viewer.html and all contacts, then seal only after all family gates pass.')
    ledger['families']['m432']['complete_delivery']={'selected_frames':len(selected),'required_frames':160,'project':'mm8_m432/complete','queue':'mm8_m432/sequence_restore/jobs.json'};process.save(ledgerpath,ledger)
    print('Assembled',len(selected),'of160; final review pending')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--partial',action='store_true');p.add_argument('--frames',nargs='+');a=p.parse_args();run(a.partial,set(a.frames) if a.frames else None)
