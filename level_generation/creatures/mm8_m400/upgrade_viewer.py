from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent
p=ROOT/'viewer.html';s=p.read_text()
s=s.replace('<label>View <select id="view"></select></label>','<label>View <select id="view"></select></label><label>Stored pose <select id="stored"><option value="">Native animation</option></select></label>')
s=s.replace("let playing=!params.has('t')", "for(const n of Object.keys(DATA.sources).sort())$('stored').add(new Option(n+(DATA.sources[n].referenced?'':' (unused)'),n));\nif(params.has('stored'))$('stored').value=params.get('stored');\nlet playing=!params.has('t')")
s=s.replace("$('state').textContent=", "$('play').textContent=playing?'Pause':'Play';\n$('stored').onchange=reset;\n$('state').textContent=")
s=s.replace("let step=steps[selected],n=step.frame", "let step=$('stored').value?{frame:$('stored').value,palette:d.actions.standing.views[0][0].palette,mirrored:false,anchor:'bottom_center',duration_ms:null}:steps[selected],n=step.frame")
s=s.replace("let path=col===0?'native_variants/'+n+'_'+step.palette+'.png':f?'previews/'+n+'_'+step.palette+'.png':null;", "let path=col===0?'native_variants/'+n+'_'+step.palette+'.png':f?'atlas':null;")
s=s.replace("let im=image(path);if(!im.complete||!im.naturalWidth)continue;", "let im=col===0?image(path):atlasFrame(n,step.palette);if(!im||(col===0&&(!im.complete||!im.naturalWidth)))continue;")
s=s.replace("DATA.registration[n].canvas_origin_px.map(v=>v/2)","f.crop_origin_px.map(v=>v/2)")
s=s.replace("(n||'Native empty frame')+' · frame '+(selected+1)+'/'+steps.length+' · '+step.duration_ms+' ms'+(step.mirrored?' · mirrored':'')", "(n||'Native empty frame')+($('stored').value?' · stored native pose; no assigned playback timing':' · frame '+(selected+1)+'/'+steps.length+' · '+step.duration_ms+' ms'+(step.mirrored?' · mirrored':''))")
extra='''
const atlasCache=new Map();
function atlasFrame(n,pal){
 let key=n+':'+pal;if(atlasCache.has(key))return atlasCache.get(key);
 let f=M.frames[n],page=M.pages[f.page],base=image(page.base),mask=image(page.mask);
 if(!base.complete||!mask.complete||!base.naturalWidth||!mask.naturalWidth)return null;
 let [x,y,w,h]=f.atlas_xywh,out=document.createElement('canvas');out.width=w;out.height=h;
 let ctx=out.getContext('2d',{willReadFrequently:true});ctx.drawImage(base,x,y,w,h,0,0,w,h);
 if(+pal!==M.variants.base_palette){
  let mc=document.createElement('canvas');mc.width=w;mc.height=h;let mx=mc.getContext('2d',{willReadFrequently:true});mx.drawImage(mask,x,y,w,h,0,0,w,h);
  let d=ctx.getImageData(0,0,w,h),m=mx.getImageData(0,0,w,h).data,coeff=M.variants.palettes[pal];
  for(let i=0;i<d.data.length;i+=4){let rgb=[d.data[i]/255,d.data[i+1]/255,d.data[i+2]/255],lum=rgb[0]*.2126+rgb[1]*.7152+rgb[2]*.0722,a=m[i]/255,b=m[i+1]/255;
   for(let ch=0;ch<3;ch++){let value=rgb[ch]*(1-a-b);for(let k=0;k<2;k++)value+=[a,b][k]*Math.max(0,Math.min(1,lum*coeff[k][0][ch]+coeff[k][1][ch]));d.data[i+ch]=Math.round(Math.max(0,Math.min(1,value))*255);}
  }ctx.putImageData(d,0,0);
 }atlasCache.set(key,out);return out;
}
'''
s=s.replace('function render(now){',extra+'\nfunction render(now){')
s=s.replace('Native palette reference (left) and restored artwork', 'Native palette reference (left) and recolored runtime atlas artwork')
p.write_text(s)
print('Viewer uses runtime atlas/mask pair and exposes all stored native poses')
