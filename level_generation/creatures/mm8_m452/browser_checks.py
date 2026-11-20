"""Exercise the actual offline viewer's native timing and decode every delivered frame."""
from pathlib import Path
import json,subprocess,tempfile,re,html
ROOT=Path(__file__).resolve().parent
script=r'''<pre id="verification">pending</pre><script>
window.addEventListener('load',async()=>{try{
 playing=false;params.delete('t');
 const load=path=>new Promise((resolve,reject)=>{const im=image(path);if(im.complete&&im.naturalWidth)resolve(im);else{im.onload=()=>resolve(im);im.onerror=()=>reject(Error(path))}});
 let decoded=0,tracks=0,boundaries=0,stored=0;
 const expectedPalettes=Object.keys(M.variants.palette_deltas).sort();
 if(JSON.stringify([...$('palette').options].map(o=>o.value).sort())!==JSON.stringify(expectedPalettes))throw Error('Palette menu mismatch');
 for(const pal of expectedPalettes){$('palette').value=pal;if($('palette').value!==pal)throw Error('Palette selection '+pal);render(0)}
 $('palette').value=String(M.variants.base_palette);
 for(const page of M.pages){const b=await load(page.base),m=await load(page.mask);if(b.width!==m.width||b.height!==m.height)throw Error('Page mismatch')}
 for(const [name,f] of Object.entries(M.frames)){
  const base=await load('runtime_aligned_2x/'+name+'.png');await load('runtime_masks_2x/'+name+'.png');
  for(const pal of [452]){const v=await load('previews/'+name+'_'+pal+'.png');await load('native_variants/'+name+'_'+pal+'.png');if(v.width!==base.width||v.height!==base.height)throw Error('Variant geometry '+name);decoded++}
  $('stored').value=name;render(0);if(!$('caption').textContent.includes(name))throw Error('Stored frame '+name);stored++;
 }
 $('stored').value='';
 for(const [actor,d] of Object.entries(M.animations)){
  $('actor').value=actor;actions();
  for(const [action,g] of Object.entries(d.actions))for(const [view,steps] of Object.entries(g.views)){
   $('action').value=action;$('view').value=view;let time=0;
   for(let i=0;i<steps.length;i++){
    if(steps[i].duration_ms>0){params.set('t',String(time+.001));render(0);if(selected!==i)throw Error('Timing '+actor+' '+action+' '+view+' '+i);boundaries++}
    time+=steps[i].duration_ms;
   }
   params.set('t',String(time+1));render(0);
   if(selected!==(g.playback==='loop'?0:steps.length-1))throw Error('Loop/hold '+actor+' '+action+' '+view);
   tracks++;
  }
 }
 params.delete('t');playing=false;
 const presentation=[];
 for(const [action,view,index] of [['attack','0',5],['walk','6',3],['corpse','2',0]]){
  $('action').value=action;if(!$('action').value)continue;$('view').value=view;$('frame').value=index;
  render(0);const step=M.animations[$('actor').value].actions[action].views[view][selected];
  const im=await load('runtime_aligned_2x/'+step.frame+'.png');
  const expected=document.createElement('canvas');expected.width=576;expected.height=576;
  const c=expected.getContext('2d');c.fillStyle=$('background').value;c.fillRect(0,0,576,576);
  if(step.mirrored){c.translate(576,0);c.scale(-1,1)}c.drawImage(im,0,0);
  const wanted=c.getImageData(0,0,576,576).data;
  const actual=$('canvas').getContext('2d').getImageData(576,0,576,576).data;
  for(let i=0;i<wanted.length;i++)if(actual[i]!==wanted[i])throw Error('Restored panel clipping/placement '+action+' '+view+' pixel '+i);
  presentation.push({action,view,frame:step.frame,mirrored:step.mirrored});
 }
 if(presentation.length<2)throw Error('Presentation coverage missing');
 $('verification').textContent=JSON.stringify({status:'passed',variant_decodes:decoded,tracks,timing_boundary_samples:boundaries,stored_poses:stored,presentation_exact: presentation});
}catch(e){$('verification').textContent=JSON.stringify({status:'failed',error:String(e),stack:e.stack})}});
</script>'''
(ROOT/'review/browser_harness.html').write_text((ROOT/'viewer.html').read_text().replace('<head>','<head><base href="../">')+script)
with tempfile.TemporaryDirectory(prefix='mm8-wererat-rat-viewer-') as work:
    command=['google-chrome','--headless','--no-sandbox','--disable-gpu','--disable-dev-shm-usage',
             '--allow-file-access-from-files','--disable-background-networking','--user-data-dir='+work,
             '--virtual-time-budget=30000','--dump-dom',(ROOT/'review/browser_harness.html').as_uri()]
    result=subprocess.run(command,capture_output=True,text=True,timeout=90)
    matches=re.findall(r'<pre id="verification">(.*?)</pre>',result.stdout,re.S)
    if not matches:raise RuntimeError(result.stderr[-2000:])
    report=json.loads(html.unescape(matches[-1]))
    (ROOT/'review/browser_checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report));assert report['status']=='passed',report
