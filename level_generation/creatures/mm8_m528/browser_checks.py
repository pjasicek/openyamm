from pathlib import Path
import json,subprocess,tempfile,re,html
ROOT=Path(__file__).resolve().parent
s=(ROOT/'viewer.html').read_text()
js=r'''<pre id="verification">pending</pre><script>
window.addEventListener('load',async()=>{
 try {
 const paths=M.pages.flatMap(p=>[p.base,p.mask]);
 await Promise.all(paths.map(p=>new Promise((resolve,reject)=>{let im=image(p);if(im.complete&&im.naturalWidth)resolve();else{im.onload=resolve;im.onerror=()=>reject(p)}})));
 let rendered=0;
 for(const n of Object.keys(M.frames))for(const pal of [528]){let c=atlasFrame(n,pal);if(!c||c.width!==M.frames[n].atlas_xywh[2]||c.height!==M.frames[n].atlas_xywh[3])throw Error('Atlas decode '+n);rendered++}
 let tracks=0,samples=0;playing=false;params.delete('t');$('stored').value='';
 for(const [id,d] of Object.entries(M.animations)){
  $('descriptor').value=id;actions();
  for(const [action,g] of Object.entries(d.actions))for(const [view,steps] of Object.entries(g.views)){
   $('action').value=action;$('view').value=view;let elapsed=0;
   for(let i=0;i<steps.length;i++){params.set('t',String(elapsed+.01));render(0);if(selected!==i)throw Error('Timing '+id+' '+action+' '+view+' '+i);elapsed+=steps[i].duration_ms;samples++}
   params.set('t',String(elapsed+1));render(0);if(selected!==(g.playback==='loop'?0:steps.length-1))throw Error('Loop/hold '+action);tracks++;
  }
 }
 params.delete('t');let stored=0;
 for(const n of Object.keys(DATA.sources)){$('stored').value=n;render(0);if(!$('caption').textContent.includes(n)||!$('caption').textContent.includes('no assigned playback timing'))throw Error('Stored pose '+n);stored++}
 $('verification').textContent=JSON.stringify({status:'passed',atlas_variant_decodes:rendered,tracks,timing_boundary_samples:samples,stored_poses:stored});
 }catch(e){$('verification').textContent=JSON.stringify({status:'failed',error:String(e),stack:e.stack})}
});</script>'''
(ROOT/'review/browser_harness.html').write_text(s.replace('<head>','<head><base href="../">') if '<head>' in s else '<base href="../">'+s+js)
# Fresh profile, no user browser state, no network (wrapper namespace).
with tempfile.TemporaryDirectory(prefix='mm8-browser-') as work:
 command=['google-chrome','--headless','--no-sandbox','--disable-gpu','--disable-dev-shm-usage','--allow-file-access-from-files','--disable-background-networking','--user-data-dir='+work,'--virtual-time-budget=20000','--dump-dom',(ROOT/'review/browser_harness.html').as_uri()]
 result=subprocess.run(command,capture_output=True,text=True,timeout=60)
 matches=re.findall(r'<pre id="verification">(.*?)</pre>',result.stdout,re.S)
 if not matches:raise RuntimeError(result.stderr[-2000:])
 report=json.loads(html.unescape(matches[-1]));(ROOT/'review/browser_checks.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
 assert report['status']=='passed',report
