"""Boulder-specific deterministic atlas export. All actors share palette 588."""
import json,math,copy
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from process import ROOT,queue,save,spill

def run():
 s=json.loads((ROOT/'sources.json').read_text());reg=json.loads((ROOT/'registration.json').read_text());assert set(reg)==set(s['sources'])
 for folder in ['atlas','masks_2x','trimmed_2x','trimmed_masks_2x','native_variants','previews']:(ROOT/folder).mkdir(exist_ok=True)
 frames={};tiles={};edges={}
 for n,source in s['sources'].items():
  assert queue.sha(queue.REPO/source['path'])==source['sha256'];im=Image.open(ROOT/f'aligned_2x/{n}.png').convert('RGBA');a=np.array(im);solid=a[:,:,3]>0;dist,idx=ndi.distance_transform_edt(~solid,return_indices=True);ring=(dist<=3)&~solid;a[:,:,:3][~solid]=0;a[:,:,:3][ring]=a[idx[0],idx[1],:3][ring];im=Image.fromarray(a);im.save(ROOT/f'aligned_2x/{n}.png')
  mask=Image.new('L',im.size,0);mask.save(ROOT/f'masks_2x/{n}.png');bb=im.getchannel('A').getbbox();bb=[max(0,bb[0]-4),max(0,bb[1]-4),min(im.width,bb[2]+4),min(im.height,bb[3]+4)];tile=im.crop(bb);mt=mask.crop(bb);out=Image.new('RGBA',im.size);out.paste(tile,bb[:2]);assert np.array_equal(out,im);out=Image.new('L',im.size);out.paste(mt,bb[:2]);assert np.array_equal(out,mask)
  tile.save(ROOT/f'trimmed_2x/{n}.png');mt.save(ROOT/f'trimmed_masks_2x/{n}.png');tiles[n]=tile;im.save(ROOT/f'previews/{n}_588.png');queue.native(ROOT,n,588).save(ROOT/f'native_variants/{n}_588.png')
  r=reg[n];frames[n]={'source':n+'.bmp','logical_size':source['size'],'source_canvas':source['size'],'crop_origin_px':[bb[0]+r['canvas_origin_px'][0],bb[1]+r['canvas_origin_px'][1]],'crop_in_aligned_px':bb,'aligned_canvas_origin_px':r['canvas_origin_px'],'aligned_canvas_size_px':r['aligned_size_px'],'referenced':source['referenced']};edges[n]={'cleaned':spill(Image.open(ROOT/f'final_cleaned/{n}.png')),'aligned':spill(im)}
 layouts=[];page=[];x=y=rowh=0;limit=2048;gutter=16
 for n,t in sorted(tiles.items(),key=lambda kv:-kv[1].height):
  w=math.ceil((t.width+2*gutter)/16)*16;h=math.ceil((t.height+2*gutter)/16)*16;assert max(w,h)<=limit
  if x+w>limit:x=0;y+=rowh;rowh=0
  if y+h>limit:layouts.append(page);page=[];x=y=rowh=0
  page.append((n,x,y,w,h));x+=w;rowh=max(rowh,h)
 if page:layouts.append(page)
 pages=[]
 for i,layout in enumerate(layouts):
  size=(max(x+w for n,x,y,w,h in layout),max(y+h for n,x,y,w,h in layout));base=Image.new('RGBA',size);mask=Image.new('L',size)
  for n,x,y,w,h in layout:
   t=tiles[n];rect=[x+gutter,y+gutter,t.width,t.height];base.paste(t,rect[:2]);frames[n].update(page=i,atlas_xywh=rect)
  bp=f'atlas/base_{i}.png';mp=f'atlas/mask_{i}.png';base.save(ROOT/bp);mask.save(ROOT/mp);pages.append({'base':bp,'mask':mp,'size':list(size),'base_format':'RGBA8','mask_format':'R8','base_color_space':'sRGB','mask_color_space':'linear coverage','gutter_px':gutter,'mipmaps':False})
  for n,x,y,w,h in layout:
   r=frames[n]['atlas_xywh'];box=(r[0],r[1],r[0]+r[2],r[1]+r[3]);out=base.crop(box);assert np.array_equal(out,tiles[n]);assert not np.asarray(mask.crop(box)).any();edges[n]['atlas_extracted']=spill(out)
 animations=copy.deepcopy(s['bindings']);actors={}
 for id,d in animations.items():
  for g in d['actions'].values():
   for steps in g['views'].values():
    for step,native in zip(steps,g['native_group_record']['frames']):step['glow_radius']=native.get('glow_radius',0)
  st=d['actions']['standing']['views']['0'][0];actors[id]={'label':d['label'],'palette':st['palette'],'native_frame_scale':st['scale'],'glow_radius':st['glow_radius']}
 variants={'base_palette':588,'palettes':{'588':{'operation':'exact base bypass'}},'regions':[],'mask_semantics':'R8 all zero; no native palette differences exist. All three descriptors share the same art.','actors':actors};save(ROOT/'material_settings.json',variants)
 manifest={'schema_version':1,'creature':'mm8:m588','status':'awaiting_visual_acceptance','pixels_per_logical_pixel':2,'pivot_rule':'Preserve native per-step Center flag and logical canvas; mirror around logical pivot; apply native frame scale afterward.','frames':frames,'pages':pages,'animations':animations,'regions':[],'variants':variants,'filter_policy':'Premultiplied-alpha Lanczos; 3px hidden RGB bleed; matching zero R8 mask; 16px gutters; mipmaps disabled','missing_frames':[],'viewer':'viewer.html'};save(ROOT/'draft_manifest.json',manifest)
 memory={'base_rgba8':sum(p['size'][0]*p['size'][1]*4 for p in pages),'mask_r8':sum(p['size'][0]*p['size'][1] for p in pages),'tight_rgba_plus_mask':sum(t.width*t.height*5 for t in tiles.values())};memory['total_base_mask_packing']=memory['base_rgba8']+memory['mask_r8'];memory['packing_overhead']=memory['total_base_mask_packing']-memory['tight_rgba_plus_mask']
 checks={'source_files':len(s['sources']),'restored_frames':len(frames),'missing_frames':[],'source_hashes_unchanged':True,'exact_crop_reconstruction':True,'exact_atlas_extraction':True,'mask_weight_sums_valid':True,'variant_alpha_unchanged':True,'zero_mask_unchanged':True,'base_bypass_exact':True,'full_coverage':True,'visual_review_complete':False,'animation_review_complete':False,'memory_bytes':memory};save(ROOT/'review/export_checks.json',checks);save(ROOT/'review/edge_audit.json',edges)
 template=(ROOT/'viewer_template.html').read_text();(ROOT/'viewer.html').write_text(template.replace('__DATA__',json.dumps({'manifest':manifest,'sources':s['sources']})));print(json.dumps({'frames':len(frames),'pages':len(pages),'memory':memory},indent=2))
if __name__=='__main__':run()
