import importlib.util,sys
from pathlib import Path
p=Path(__file__).with_name('session_pipeline.py');s=importlib.util.spec_from_file_location('session',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
stem=sys.argv[1];root=m.STAGE/('mm7_'+stem);out=root/'redo_2x';sources=m.read(root/'sources.json');reg=m.read(out/'registration.json')
names=sys.argv[2:]
if names and names[0].startswith("@"):
 report=m.read(out/"review"/(names.pop(0)[1:]+"_extraction.json"));reg={f["frame"]:f for f in report["frames"]}
for name in names:
 native=m.native_2x(sources['sources'][name],sources,sources['base_palette'])[0].resize(tuple(x*3 for x in sources['logical_canvas']),m.Image.Resampling.NEAREST)
 clean=m.Image.open(m.REPO/reg[name]['clean_path']).convert('RGBA');ims=[]
 for im,spacing,factor in [(native,10,3),(clean,40,1)]:
  bg=m.Image.new('RGB',im.size,(40,43,43));bg.paste(im,mask=im.getchannel('A'));d=m.ImageDraw.Draw(bg)
  for x in range(0,im.width,spacing*factor):d.line((x,0,x,im.height),fill=(65,80,80));d.text((x+1,15),str(x//factor),fill='white')
  for y in range(0,im.height,spacing*factor):d.line((0,y,im.width,y),fill=(65,80,80));d.text((0,y+1),str(y//factor),fill='white')
  ims.append(bg)
 page=m.Image.new('RGB',(sum(im.width for im in ims)+10,max(im.height for im in ims)+25),(30,30,30));d=m.ImageDraw.Draw(page);d.text((0,0),name+' NATIVE logical xy / CLEAN original pixel xy',fill='white');page.paste(ims[0],(0,25));page.paste(ims[1],(ims[0].width+10,25));page.save(out/'review'/('actual_features_'+name+'.png'))
 print(name,'clean size',clean.size)
