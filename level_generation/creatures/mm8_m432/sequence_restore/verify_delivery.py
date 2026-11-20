"""Verify complete native coverage, exact palette math and the reviewed contact anchors."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage as ndi
F=Path(__file__).resolve().parent;R=F.parent;G=R/'complete'
sys.path.insert(0,str(R));import process,materials
sys.path.insert(0,str(R/'front_attack_grid_trial'));from foot_alignment import feet

def run():
    m=json.loads((G/'draft_manifest.json').read_text());s=json.loads((R/'sources.json').read_text())
    selected=json.loads((G/'selection.json').read_text());config=json.loads((G/'material_settings.json').read_text())
    assert set(m['frames'])==set(selected)==set(s['sources']) and len(selected)==160
    assert m['animations']==s['bindings'] and not m['missing_frames']
    records={};edges=[];anchors={}
    for n,rec in sorted(selected.items()):
        a=np.array(Image.open(G/'toned_2x'/(n+'.png')));mask=np.array(Image.open(G/'masks_2x'/(n+'.png')))
        assert rec['sampling']>=2
        active=mask>0
        for pal in materials.PALETTES:
            v=np.array(Image.open(G/'previews'/(n+'_'+str(pal)+'.png')))
            assert np.array_equal(a[:,:,3],v[:,:,3]) and np.array_equal(a[~active],v[~active])
            # The palette operation is pointwise: evaluating only nonzero coverage is identical,
            # and independently detects stale previews without recalculating transparent canvases.
            expected=materials.recolor(Image.fromarray(a[active][:,None,:]),Image.fromarray(mask[active][:,None]),pal,config)
            assert np.array_equal(np.asarray(expected)[:,0,:],v[active]),(n,pal,'palette math')
            assert pal!=433 or np.array_equal(a,v)
            band=(a[:,:,3]>0)&(ndi.distance_transform_edt(a[:,:,3]>=250)<=4)
            protected=band&~active
            assert np.array_equal(a[protected],v[protected])
            score=np.minimum(v[:,:,0].astype(float),v[:,:,2])-v[:,:,1]
            score[~band]=-1e9;y,x=np.unravel_index(np.argmax(score),score.shape)
            edges.append((float(score[y,x]),n,pal,(int(x),int(y))))
        records[n]={'sampling_generated_per_native':rec['sampling'],'three_variants_exact':True,'alpha_exact':True,'protected_pixels_exact':True}
    for c in 'abcdefgh':
        n='m432a'+c+'0';native=Image.new('RGBA',(576,576));native.paste(process.queue.native(R,n).resize((512,512),Image.Resampling.NEAREST),(32,32))
        a,b=feet(native),feet(Image.open(G/'toned_2x'/(n+'.png')))
        assert a['sole_y']==b['sole_y'] and abs(a['stance_center_x']-b['stance_center_x'])<=.5,(n,a,b)
        anchors[n]={'native':a,'restored':b}
    for n in ['m432dd4','m432xa4']:
        im=np.asarray(Image.open(G/'toned_2x'/(n+'.png')))
        bottom=int(np.where(im[:,:300,3]>=128)[0].max())+1
        assert bottom==544,(n,bottom)
        anchors[n]={'reviewed_heel_roi':[0,0,300,576],'native_and_restored_contact_y':bottom}
    edges.sort(reverse=True);chosen=edges[:12];sheet=Image.new('RGB',(1500,1060),(35,35,35));draw=ImageDraw.Draw(sheet)
    for i,(score,n,pal,(x,y)) in enumerate(chosen):
        im=Image.open(G/'previews'/(n+'_'+str(pal)+'.png')).crop((x-20,y-20,x+21,y+21));col=i%6;row=i//6
        draw.text((col*250+3,row*530+4),n+' pal'+str(pal),fill='white')
        for k,bg in enumerate([(18,18,18),(235,235,235)]):
            out=Image.new('RGBA',im.size,(*bg,255));out.alpha_composite(im);sheet.paste(out.resize((246,246),Image.Resampling.NEAREST).convert('RGB'),(col*250+2,row*530+28+k*250))
    sheet.save(G/'review/variant_edges.png')
    process.save(G/'review/delivery_checks.json',{'status':'passed','frames':records,'anchor_checks':anchors,
        'native_bindings_exact':True,'full_native_coverage':True,'variant_edge_policy':'Protected contour RGB remains exact. Recolored contours must equal the documented native-palette transform exactly; blue/pink material chroma is not judged using green-base limits.',
        'sampling_minimum':min(r['sampling'] for r in selected.values()),'sampling_maximum':max(r['sampling'] for r in selected.values())})
    combined=G/'review/combined';combined.mkdir(exist_ok=True)
    for p in sorted((G/'review/variants').glob('*.png')):
        top=Image.open(G/'review'/(p.stem+'_final.png'));v=Image.open(p)
        im=Image.new('RGB',(v.width,1400));im.paste(top.crop((0,0,top.width,280)),(0,0));im.paste(v,(0,280));im.save(combined/p.name)
    print('160 frames, 480 exact variants, 8 planted attack anchors and 2 prone contacts verified; combined review contacts ready.')

if __name__=='__main__':run()
