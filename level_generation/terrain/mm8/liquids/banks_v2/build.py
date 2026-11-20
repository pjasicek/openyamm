"""Round native key contours and dematte tar's partial-magenta palette pixels."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import json
import shutil
from scipy.ndimage import gaussian_filter, distance_transform_edt, label
from PIL import ImageDraw
from common import *
from build_transitions import reduce_float,recovery

F=Path(__file__).resolve().parent


def rounded_coverage(alpha):
    mask=np.pad(alpha>.5,16,mode='edge')
    sdf=distance_transform_edt(mask)-distance_transform_edt(~mask)
    sdf=gaussian_filter(sdf,2,mode='nearest')[16:-16,16:-16]
    result=np.clip(.5+sdf/1.6,0,1)
    original=alpha>.5;current=original.copy();wanted=result>.5
    # A local flip may round an edge, but may not remove/create an island,
    # merge separate islands, or open/close a liquid hole. Keep the native
    # coverage at blocked points instead of hiding them at half opacity.
    yy,xx=np.where(current!=wanted)
    order=np.argsort(-abs(result[yy,xx]-.5))
    for index in order:
        y,x=yy[index],xx[index]
        if not (0<y<511 and 0<x<511):continue
        neighbours=current[y-1:y+2,x-1:x+2].copy();neighbours[1,1]=False
        inverse=~current[y-1:y+2,x-1:x+2];inverse[1,1]=False
        if label(neighbours)[1]==1 and label(inverse)[1]==1:
            current[y,x]=wanted[y,x]
    blocked=current!=wanted
    result[blocked]=alpha[blocked]
    assert label(result>.5)[1]==label(original)[1]
    assert label(result<=.5)[1]==label(~original)[1]
    return result


def dematte(original,base):
    key=np.array([255.,0.,255.])
    exact=(original[:,:,0]>240)&(original[:,:,1]<10)&(original[:,:,2]>240)
    near=distance_transform_edt(~exact)<=2
    purple=(np.minimum(original[:,:,0],original[:,:,2])-original[:,:,1])>8
    candidate=near&purple&~exact
    interior=~near&purple&~exact
    bb=(base*base).sum(2);bk=(base*key).sum(2);ok=(original*key).sum(2);ob=(original*base).sum(2)
    fraction=np.clip((ok*bb-ob*bk)/np.maximum((key*key).sum()*bb-bk*bk,1),0,.99)
    fraction[~candidate]=0
    alpha=(~exact).astype(float)*(1-fraction)
    corrected=original.copy()
    corrected[candidate]=(original[candidate]-fraction[candidate,None]*key)/(1-fraction[candidate,None])
    # Isolated purple palette specks also occur inside opaque grey soil. They
    # are not holes: keep their opacity and brightness, using the native base's
    # chroma rather than transferring the magenta tint to the restored master.
    brightness=original.mean(2)/np.maximum(base.mean(2),1)
    corrected[interior]=base[interior]*brightness[interior,None]
    return alpha,np.clip(corrected,0,255),candidate|interior


def main():
    source=json.loads((P/'transitions/build.json').read_text());records=[]
    bases=dict(dirt='dirttyl',grey_dirt='gdtyl',plains='plntyl')
    for record in source['tiles']:
        if not record['overlay']:continue
        n=record['name'];family=record['family'];land=record['binding']['land']
        old_path=P/'transitions/fields'/(n+'.npz');assert sha(old_path)==record['field_sha256']
        old=np.load(old_path);alpha=old['coverage'].astype(float);shade=old['shade'].astype(float)
        old_alpha=alpha.copy();corrected_count=0
        if family in ('shore_dirt','lava_dirt'):
            alpha=rounded_coverage(alpha)
        if family=='tar_grey':
            original=read(P/'references'/(n+'.png'));base=read(P/'references'/(bases[land]+'.png'))
            native_alpha,corrected,selected=dematte(original,base);corrected_count=int(selected.sum())
            # Apply only the inferred partial-key correction; retain the established
            # shared-edge coverage and all unrelated native bank pixels.
            old_native=((original[:,:,0]<=240)|(original[:,:,1]>=10)|(original[:,:,2]<=240)).astype(float)
            delta=np.clip(recovery.up(old_native-native_alpha),0,1)
            alpha=np.clip(alpha-delta,0,1)
            ratio=corrected/np.maximum(base,1);bank=(native_alpha>0)&(np.max(abs(corrected-base),axis=2)>4)
            ratio[~bank]=1;ratio=np.clip(ratio,.45,1.35)
            clean=np.stack([recovery.up(gaussian_filter(ratio[:,:,c],.6)) for c in range(3)],axis=2)
            dirty_ratio=original/np.maximum(base,1);dirty_bank=(old_native>0)&(np.max(abs(original-base),axis=2)>4)
            dirty_ratio[~dirty_bank]=1;dirty_ratio=np.clip(dirty_ratio,.45,1.35)
            dirty=np.stack([recovery.up(gaussian_filter(dirty_ratio[:,:,c],.6)) for c in range(3)],axis=2)
            correction=clean-dirty
            # Shared profiles are untouched; correct only the source-specific core.
            yy,xx=np.mgrid[:512,:512];edge_distance=np.minimum.reduce([xx,yy,511-xx,511-yy])
            weight=np.clip((edge_distance-8)/24,0,1)
            shade+=correction*weight[:,:,None]
        master=read(M/'materials'/(land+'.png'))
        coverage=seams.pad(alpha,'edge');rgb=seams.pad(master,'wrap')*seams.pad(shade,'edge')
        premul=reduce_float(rgb*coverage[:,:,None]);out_alpha=np.clip(reduce_float(coverage),0,1)
        out_rgb=reduce_float(rgb);visible=out_alpha>1e-6;out_rgb[visible]=premul[visible]/out_alpha[visible,None]
        runtime=F/'runtime'/(n+'.png');save(runtime,np.dstack([out_rgb,out_alpha*255]))
        save(F/'masks'/(n+'.png'),alpha*255)
        (F/'fields').mkdir(exist_ok=True);np.savez_compressed(F/'fields'/(n+'.npz'),coverage=alpha.astype('float32'),shade=shade.astype('float32'))
        if family not in ('shore_dirt','lava_dirt') and corrected_count==0:
            shutil.copy2(OUT/(n+'.png'),runtime)
            shutil.copy2(old_path,F/'fields'/(n+'.npz'))
        item=dict(record);item.update(runtime_sha256=sha(runtime),field_sha256=sha(F/'fields'/(n+'.npz')),
            original_components=label(old_alpha>.5)[1],components=label(alpha>.5)[1],
            original_void_components=label(old_alpha<=.5)[1],void_components=label(alpha<=.5)[1],
            corrected_native_pixels=corrected_count,max_alpha_change=float(abs(alpha-old_alpha).max()))
        records.append(item)
    for family in sorted({r['family'] for r in records}):
        members=[r for r in records if r['family']==family]
        sheet=Image.new('RGB',(1024,280*len(members)),'#202933');draw=ImageDraw.Draw(sheet)
        liquid=read(P/'liquids/v1/runtime'/({'water':'hdwtr000','lava':'hdlav000','tar':'hwoil000'}[members[0]['binding']['liquid']]+'.png'))
        for row,r in enumerate(members):
            n=r['name']
            for col,path in enumerate((OUT/(n+'.png'),F/'runtime'/(n+'.png'))):
                rgba=np.asarray(Image.open(path).convert('RGBA'),float);a=rgba[:,:,3:4]/255
                image=Image.fromarray(seams.byte(rgba[:,:,:3]*a+liquid*(1-a)))
                sheet.paste(image,(col*512,row*280+24))
                # Enlarge a fixed central outline neighbourhood for corner review.
                sheet.paste(image.crop((64,64,192,192)).resize((256,256)),(col*512+256,row*280+24))
                draw.text((col*512+4,row*280+4),n+(' old' if col==0 else ' candidate'),fill='white')
        sheet.save(F/(family+'_comparison.png'))
    report=dict(status='bank_candidates_require_visual_and_phase_review',tiles=records,
        source_build_sha256=sha(P/'transitions/build.json'),script_sha256=sha(Path(__file__)),
        masters={g:sha(M/'materials'/(g+'.png')) for g in bases})
    (F/'build.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Built',len(records),'banks; corrected',sum(r['corrected_native_pixels'] for r in records),'native partial-key pixels')
    print('Topology changes',[(r['name'],r['original_components'],r['components'],r['original_void_components'],r['void_components']) for r in records if r['original_components']!=r['components'] or r['original_void_components']!=r['void_components']])


if __name__=='__main__':main()
