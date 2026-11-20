"""Deterministic 2x m400 atlas export and offline native/variant animation review.

Incomplete work exports draft_manifest.json only. Completion requires all native
frames plus explicit visual acceptance; file existence cannot pass the gate.
"""
from pathlib import Path
import json,math
import numpy as np
from PIL import Image
from scipy import ndimage
from process import ROOT,queue,spill
from materials import masks,fit,recolor

def save(path,data):path.write_text(json.dumps(data,indent=2)+'\n')

def run():
    inv=json.loads((ROOT/'sources.json').read_text());reg=json.loads((ROOT/'registration.json').read_text())
    settings=fit();save(ROOT/'material_settings.json',settings)
    for folder in ('atlas','trimmed_2x','trimmed_masks_2x','native_variants','previews','review'):(ROOT/folder).mkdir(exist_ok=True)
    frames={};tiles={};masktiles={};edges={};all_native=set(inv['sources'])
    missing=sorted(all_native-set(reg))
    for n,r in reg.items():
        source=inv['sources'][n]
        assert queue.sha(queue.REPO/source['path'])==source['sha256'],n
        im=Image.open(ROOT/f'aligned_2x/{n}.png').convert('RGBA');w=masks(im,n)
        rgba=np.array(im);solid=rgba[:,:,3]>0
        dist,nearest=ndimage.distance_transform_edt(~solid,return_indices=True)
        ring=(dist<=3)&~solid
        rgba[:,:,:3][~solid]=0
        rgba[:,:,:3][ring]=rgba[nearest[0],nearest[1],:3][ring]
        w[ring]=w[nearest[0],nearest[1]][ring]
        im=Image.fromarray(rgba);im.save(ROOT/f'aligned_2x/{n}.png')
        mask=Image.fromarray(np.dstack([w,np.zeros(w.shape[:2],np.uint8)]),'RGB')
        (ROOT/'masks_2x').mkdir(exist_ok=True);mask.save(ROOT/f'masks_2x/{n}.png')
        bb=im.getchannel('A').getbbox();bb=[max(0,bb[0]-4),max(0,bb[1]-4),min(im.width,bb[2]+4),min(im.height,bb[3]+4)]
        tile=im.crop(bb);mt=mask.crop(bb)
        reconstructed=Image.new('RGBA',im.size);reconstructed.paste(tile,bb[:2])
        assert np.array_equal(reconstructed,im),n
        reconstructed_mask=Image.new('RGB',im.size);reconstructed_mask.paste(mt,bb[:2])
        assert np.array_equal(reconstructed_mask,mask),n
        tile.save(ROOT/f'trimmed_2x/{n}.png');mt.save(ROOT/f'trimmed_masks_2x/{n}.png')
        tiles[n]=tile;masktiles[n]=mt
        frames[n]=dict(source=n+'.bmp',source_canvas=source['size'],logical_size=source['size'],
                       crop_origin_px=[bb[0]+r['canvas_origin_px'][0],bb[1]+r['canvas_origin_px'][1]],
                       crop_in_aligned_px=bb,aligned_canvas_origin_px=r['canvas_origin_px'],
                       aligned_canvas_size_px=r['aligned_size_px'],referenced=source['referenced'])
        edges[n]={'cleaned':spill(Image.open(ROOT/f'cleaned/{n}.png').convert('RGBA')),'aligned':spill(im)}
        for pal in (401,402,403):
            variant=recolor(im,w,pal,settings)
            assert np.array_equal(np.asarray(variant)[:,:,3],np.asarray(im)[:,:,3]),n
            if pal==401:assert np.array_equal(variant,im),n
            zero=w.sum(axis=2)==0
            assert np.array_equal(np.asarray(variant)[zero],np.asarray(im)[zero]),n
            variant.save(ROOT/f'previews/{n}_{pal}.png')
    # Native palette references stay distinct from enhanced output; all source frames remain visible in the reviewer.
    for n in all_native:
        for pal in (401,402,403):
            p=ROOT/f'native_variants/{n}_{pal}.png'
            if not p.exists():queue.native(ROOT,n,pal).save(p)
    pages=[];layouts=[];page=[];x=y=rowh=0;limit=2048;gutter=16
    for n,tile in sorted(tiles.items(),key=lambda item:-item[1].height):
        width=math.ceil((tile.width+gutter*2)/16)*16;height=math.ceil((tile.height+gutter*2)/16)*16
        assert width<=limit and height<=limit,n
        if x+width>limit:x=0;y+=rowh;rowh=0
        if y+height>limit:
            layouts.append(page);page=[];x=y=rowh=0
        page.append((n,x,y,width,height));x+=width;rowh=max(rowh,height)
    if page:layouts.append(page)
    for index,layout in enumerate(layouts):
        width=max(x+w for n,x,y,w,h in layout);height=max(y+h for n,x,y,w,h in layout)
        base=Image.new('RGBA',(width,height));mask=Image.new('RGB',(width,height))
        for n,x,y,w,h in layout:
            tx,ty=x+gutter,y+gutter;tile=tiles[n];mt=masktiles[n]
            base.paste(tile,(tx,ty));mask.paste(mt,(tx,ty))
            rect=[tx,ty,tile.width,tile.height]
            frames[n].update(page=index,atlas_xywh=rect)
            # Each tile includes 3px matching hidden color/mask bleed; outer gutters remain transparent.
        basepath=f'atlas/base_{index}.png';maskpath=f'atlas/mask_{index}.png'
        base.save(ROOT/basepath);mask.save(ROOT/maskpath)
        pages.append(dict(base=basepath,mask=maskpath,size=[width,height],base_format='RGBA8',mask_format='RGB8',
                          base_color_space='sRGB',mask_color_space='linear coverage',gutter_px=gutter,mipmaps=False))
        for n,x,y,w,h in layout:
            r=frames[n]['atlas_xywh'];bb=(r[0],r[1],r[0]+r[2],r[1]+r[3])
            extracted=base.crop(bb)
            assert np.array_equal(extracted,tiles[n]),n
            assert np.array_equal(mask.crop(bb),masktiles[n]),n
            edges[n]['atlas_extracted']=spill(extracted)
    manifest=dict(schema_version=1,creature='mm8:m400',status='draft' if missing else 'awaiting_visual_acceptance',
                  pixels_per_logical_pixel=2,pivot_rule='Per-step Center flag: canvas center; otherwise bottom center. Mirror around logical pivot.',
                  frames=frames,pages=pages,animations=inv['bindings'],regions=settings['regions'],variants=settings,
                  filter_policy='Premultiplied-alpha Lanczos; 3px matching hidden RGB/mask bleed, 16px gutters; mipmaps disabled',
                  missing_frames=missing)
    save(ROOT/'draft_manifest.json',manifest)
    footprint={'base_rgba8':sum(p['size'][0]*p['size'][1]*4 for p in pages),
               'mask_rgb8':sum(p['size'][0]*p['size'][1]*3 for p in pages),
               'tight_rgba_plus_mask':sum(im.width*im.height*7 for im in tiles.values())}
    footprint['total_base_mask_packing']=footprint['base_rgba8']+footprint['mask_rgb8']
    footprint['packing_overhead']=footprint['total_base_mask_packing']-footprint['tight_rgba_plus_mask']
    checks=dict(source_files=len(all_native),restored_frames=len(frames),missing_frames=missing,
                source_hashes_unchanged=True,exact_crop_reconstruction=True,exact_atlas_extraction=True,
                mask_weight_sums_valid=True,variant_alpha_unchanged=True,zero_mask_unchanged=True,base_bypass_exact=True,
                full_coverage=not missing,visual_review_complete=False,animation_review_complete=False,
                memory_bytes=footprint)
    save(ROOT/'review/export_checks.json',checks);save(ROOT/'review/edge_audit.json',edges)
    build_viewer(manifest,inv,reg)
    print(json.dumps({'frames':len(frames),'missing':len(missing),'pages':len(pages),'memory':footprint},indent=2))

def build_viewer(manifest,inv,reg):
    data=json.dumps({'manifest':manifest,'sources':inv['sources'],'registration':reg})
    html='''<!doctype html><meta charset="utf-8"><title>MM8 Lizardman restoration review</title>
<style>body{font:16px system-ui;margin:24px;background:#202424;color:#eee}select,button,input{font:inherit;margin:6px;padding:5px}canvas{max-width:100%;border:1px solid #667}a{color:#9cf}.bar{display:flex;gap:12px;flex-wrap:wrap}label{display:inline-block}small{color:#bcb}#state{color:#fda}</style>
<h1>MM8 Lizardman</h1><p id="state"></p><div class="bar">
<label>Variant <select id="descriptor"></select></label><label>Action <select id="action"></select></label>
<label>View <select id="view"></select></label><label>Background <select id="bg"><option value="#292c2c">Dark</option><option value="#ededed">Light</option></select></label>
<button id="play">Pause</button><label>Frame <input id="frame" type="range" min="0" value="0"></label></div>
<p id="caption"></p><canvas id="canvas" width="1100" height="600"></canvas>
<p>Native palette reference (left) and restored artwork at the same logical scale (right). Red guides show the native pivot. Unused stored poses are retained separately without invented playback timing.</p>
<p><a href="review/export_checks.json">Export checks</a> · <a href="review/edge_audit.json">Edge audit</a> · <a href="draft_manifest.json">Placement and animation metadata</a></p>
<script>const DATA=__DATA__;
const M=DATA.manifest,$=id=>document.getElementById(id),params=new URLSearchParams(location.search);
const cache=new Map();function image(path){if(!cache.has(path)){let im=new Image();im.src=path;cache.set(path,im)}return cache.get(path)}
for(const [id,d] of Object.entries(M.animations))$('descriptor').add(new Option(d.label,id));
for(let i=0;i<8;i++)$('view').add(new Option(String(i),String(i)));
let playing=!params.has('t'),start=performance.now(),selected=0;
function reset(){start=performance.now();selected=0;$('frame').value=0}
function actions(){let old=$('action').value;$('action').innerHTML='';for(const a of Object.keys(M.animations[$('descriptor').value].actions))$('action').add(new Option(a,a));$('action').value=old||'standing';reset()}
$('descriptor').onchange=actions;actions();
if(params.has('descriptor')){$('descriptor').value=params.get('descriptor');actions()}
if(params.has('action'))$('action').value=params.get('action');if(params.has('view'))$('view').value=params.get('view');
$('action').onchange=reset;$('view').onchange=reset;$('frame').oninput=()=>{playing=false;selected=+$('frame').value;$('play').textContent='Play'};
$('play').onclick=()=>{playing=!playing;reset();$('play').textContent=playing?'Pause':'Play'};
$('state').textContent=Object.keys(M.frames).length+' / '+Object.keys(DATA.sources).length+' native frames restored — '+M.status;
function render(now){let d=M.animations[$('descriptor').value],g=d.actions[$('action').value],steps=g.views[$('view').value];
let t=params.has('t')?+params.get('t'):now-start,total=steps.reduce((s,f)=>s+f.duration_ms,0);
if(playing||params.has('t')){t=g.playback==='loop'?t%total:Math.min(t,Math.max(0,total-.001));selected=0;while(selected<steps.length-1&&t>=steps[selected].duration_ms){t-=steps[selected].duration_ms;selected++}}
selected=Math.min(selected,steps.length-1);$('frame').max=steps.length-1;$('frame').value=selected;
let step=steps[selected],n=step.frame,c=$('canvas').getContext('2d');c.fillStyle=$('bg').value;c.fillRect(0,0,1100,600);c.fillStyle='#999';c.font='18px system-ui';c.fillText('Native',30,28);c.fillText('Restored 2×',570,28);
if(n){let s=DATA.sources[n],f=M.frames[n],pivot=[s.size[0]/2,step.anchor==='center'?s.size[1]/2:s.size[1]],zoom=2;
for(let col=0;col<2;col++){let px=275+550*col,py=550;c.strokeStyle='#a55';c.beginPath();c.moveTo(px-12,py);c.lineTo(px+12,py);c.moveTo(px,py-12);c.lineTo(px,py+12);c.stroke();
let path=col===0?'native_variants/'+n+'_'+step.palette+'.png':f?'previews/'+n+'_'+step.palette+'.png':null;
if(!path){c.fillStyle='#eaa';c.fillText('Restoration pending',px-90,250);continue}let im=image(path);if(!im.complete||!im.naturalWidth)continue;
let origin=col===0?[0,0]:DATA.registration[n].canvas_origin_px.map(v=>v/2),tier=col===0?1:2;
c.save();c.translate(px,py);if(step.mirrored)c.scale(-1,1);c.drawImage(im,(origin[0]-pivot[0])*zoom,(origin[1]-pivot[1])*zoom,im.width/tier*zoom,im.height/tier*zoom);c.restore();}
}$('caption').textContent=(n||'Native empty frame')+' · frame '+(selected+1)+'/'+steps.length+' · '+step.duration_ms+' ms'+(step.mirrored?' · mirrored':'');requestAnimationFrame(render)}
requestAnimationFrame(render);</script>'''
    (ROOT/'viewer.html').write_text(html.replace('__DATA__',data))

if __name__=='__main__':run()
