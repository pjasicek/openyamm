"""Frozen native material color distributions applied on enhanced RGB, without spatial color transfer."""
import json
import numpy as np
from PIL import Image
from process import ROOT, queue, save, fix
from material_support import support, protect

LUMA=np.array([.2126,.7152,.0722])

def classify(rgb):
    r,g,b=np.moveaxis(np.asarray(rgb,dtype=float),-1,0)
    out=np.zeros(r.shape,dtype=np.uint8)
    out[(r-b>12)&(r>g*1.02)]=1
    out[(b-r>2)&(g-r>2)]=2
    out[(g-r>8)&(g-b>10)]=3
    return out

def sample(images):
    a=np.concatenate([np.asarray(im).reshape(-1,4) for im in images])
    return a[a[:,3]>240,:3].astype(float)

def make_settings():
    batches=json.loads((ROOT/'batches.json').read_text())
    names=batches['identity']['frames']
    native=sample([queue.native(ROOT,n) for n in names])
    enhanced=sample([Image.open(ROOT/f'registered_2x/{n}.png') for n in names])
    ni=classify(native);ei=classify(enhanced);tables=[]
    for material in range(4):
        n=native[ni==material];e=enhanced[ei==material]
        assert len(n)>10 and len(e)>10,(material,len(n),len(e))
        nl=n@LUMA;el=e@LUMA;sorted_el=np.sort(el)
        result=[]
        for value in range(256):
            quantile=np.clip(np.searchsorted(sorted_el,value)/len(el),.005,.995)
            target=float(np.quantile(nl,quantile))
            nw=np.exp(-.5*((nl-target)/8)**2);ew=np.exp(-.5*((el-value)/8)**2)
            if ew.sum()<1e-8:ew=np.exp(-.5*((el-np.clip(value,el.min(),el.max()))/8)**2)
            nc=(n*nw[:,None]).sum(axis=0)/max(nw.sum(),1e-8)
            ec=(e*ew[:,None]).sum(axis=0)/max(ew.sum(),1e-8)
            # Preserve every enhanced pixel's fine detail; only material-conditioned color offsets vary with luma.
            result.append((.8*(nc-ec)).tolist())
        tables.append(result)
    return {'method':'Identity-frozen material-conditioned native quantile color offset, strength 0.8.',
            'classes':['neutral feathers and darks','warm skin/leather/beak','cool metal accents','green equipment'],
            'classifier':'RGB8: warm R-B>12 and R>1.02G; cool B-R>2 and G-R>2; green G-R>8 and G-B>10 overrides.',
            'reference_frames':names,'luma':[.2126,.7152,.0722],'color_bandwidth':8,
            'spatial_native_transfer':False,'offset_tables':tables}

def run():
    path=ROOT/'material_tone_settings.json'
    config=json.loads(path.read_text()) if path.exists() else make_settings()
    save(path,config);tables=np.asarray(config['offset_tables'])
    reg=json.loads((ROOT/'calibration_registration.json').read_text());(ROOT/'toned_2x').mkdir(exist_ok=True)
    for name in reg:
        im=Image.open(ROOT/f'registered_2x/{name}.png').convert('RGBA');a=np.array(im);rgb=a[:,:,:3].astype(float)
        lum=np.clip(rgb@LUMA,0,255);lo=np.floor(lum).astype(int);hi=np.minimum(lo+1,255);t=(lum-lo)[:,:,None];ids=classify(rgb)
        offset=tables[ids,lo]*(1-t)+tables[ids,hi]*t
        a[:,:,:3]=np.round(rgb+offset).clip(0,255).astype(np.uint8)
        unprotected=fix(Image.fromarray(a),name)
        (ROOT/'material_support_2x').mkdir(exist_ok=True)
        Image.fromarray(np.round(support(unprotected,name)*255).astype(np.uint8)).save(ROOT/f'material_support_2x/{name}.png')
        out=fix(protect(unprotected,name),name);assert np.array_equal(np.asarray(out)[:,:,3],np.asarray(im)[:,:,3])
        out.save(ROOT/f'toned_2x/{name}.png')
    save(ROOT/'tone_refinement.json',{'operation':config['method'],'settings':'material_tone_settings.json',
         'reason':'Spatial native coarse color crossed enhanced material boundaries near side-view head and wing root. Frozen enhanced-RGB material classes preserve boundaries and native tonal distributions.',
         'fixed_across_all_frames':True,'alpha_and_geometry_unchanged':True,'spatial_native_color_or_mask_transfer':False,'frames':len(reg),'input':'registered_2x','output':'toned_2x','protected_material_cleanup':'Enhanced green components >45 RGB8, >=30px, 6px support plus 4px feather; reviewed enhanced-only equipment permission rectangles; protected green excess neutralized to +2 with preserved luma.'})
    print('Restored frozen native material tone for',len(reg),'frames')

if __name__=='__main__':run()
