"""Read-only functional check of the reused self-contained MM7 reviewer."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import urllib.request

import websocket

import session_workflow as workflow


def run():
    with tempfile.TemporaryDirectory(prefix='mm7-session06-browser-') as temp:
        directory=Path(temp)
        with (directory/'chrome.log').open('w') as log:
            process=subprocess.Popen([shutil.which('google-chrome'),'--headless','--no-sandbox',
                '--disable-gpu','--disable-dev-shm-usage','--remote-debugging-port=0','--remote-allow-origins=*',
                '--user-data-dir='+str(directory/'profile'),'about:blank'],stdout=log,stderr=log)
            connection=None
            try:
                port_file=directory/'profile/DevToolsActivePort'
                deadline=time.monotonic()+20
                while not port_file.exists():
                    if process.poll() is not None or time.monotonic()>deadline:
                        raise RuntimeError((directory/'chrome.log').read_text()[-1800:])
                    time.sleep(.05)
                port=int(port_file.read_text().splitlines()[0])
                targets=json.load(urllib.request.urlopen(f'http://127.0.0.1:{port}/json/list'))
                page=next(target for target in targets if target['type']=='page')
                connection=websocket.create_connection(page['webSocketDebuggerUrl'],timeout=30)
                counter=0

                def call(method,params=None):
                    nonlocal counter
                    counter+=1
                    connection.send(json.dumps(dict(id=counter,method=method,params=params or {})))
                    while True:
                        result=json.loads(connection.recv())
                        if result.get('id')==counter:
                            assert 'error' not in result,result
                            return result['result']

                def evaluate(expression):
                    result=call('Runtime.evaluate',dict(expression=expression,awaitPromise=True,returnByValue=True))
                    assert 'exceptionDetails' not in result,result
                    return result['result'].get('value')

                for number in workflow.FAMILIES:
                    root=workflow.SESSION/f'mm7_m{number}'
                    call('Page.navigate',dict(url=(root/'viewer.html').as_uri()+'?frame=0'))
                    deadline=time.monotonic()+30
                    ready=('document.readyState==="complete" && typeof m!=="undefined" && '
                           f'Object.keys(m.frames)[0].startsWith("m{number}") && !!window.reviewFrame')
                    while not evaluate(ready):
                        if time.monotonic()>deadline:
                            raise RuntimeError(evaluate('document.getElementById("status").textContent'))
                        time.sleep(.05)
                    checks=evaluate('''(async()=>{
                        const next=()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
                        playing=false;let cases=0,mirrors=0,empty=0;
                        for(const [descriptor,actions] of Object.entries(m.descriptor_animations)){
                            $('descriptor').value=descriptor;
                            for(const [action,animation] of Object.entries(actions)){
                                $('action').value=action;
                                for(const [view,steps] of Object.entries(animation.directions)){
                                    $('view').value=view;fixed=0;await next();
                                    if(animation.empty){if(!window.reviewFrame.empty)throw Error('Empty native action');empty++;continue;}
                                    const f=steps[0],actual=window.reviewFrame;
                                    if(actual.name!==f.frame||actual.mirror!==f.mirror||actual.palette!==f.palette_id||actual.scale!==f.scale)
                                        throw Error(JSON.stringify({descriptor,action,view,actual,f}));
                                    if(!m.frames[f.frame])throw Error('Missing exported frame');
                                    cases++;mirrors+=Number(f.mirror);
                                }
                            }
                        }
                        for(const image of [...Object.values(native).flatMap(x=>Object.values(x)),
                            ...Object.values(appearances).flat(),...overlays])
                            if(!image.complete||image.naturalWidth===0)throw Error('Image decode failed');
                        $('action').value='standing';$('view').value='0';fixed=0;
                        for(const background of ['#292b29','#eaeaea']){
                            $('background').value=background;
                            for(const overlay of [false,true]){$('overlay').checked=overlay;await next();
                                const rgba=$('canvas').getContext('2d').getImageData(0,0,1200,700).data;
                                if(!rgba.some((v,i)=>i%4===3&&v===255))throw Error('Empty canvas');}
                        }
                        return {status:'passed',cases,mirrors,empty,loaded_images:true,
                            backgrounds_and_mask_overlay:true,status_banner:!!$('session-status')};
                    })()''')
                    assert checks['status_banner'] and checks['status']=='passed'
                    checks.update(family=f'mm7_m{number}',viewer_sha256=workflow.sha(root/'viewer.html'),
                                  scope='Functional browser checks; does not grant visual animation acceptance.')
                    workflow.write(root/'review/browser_check.json',checks)
                    print(json.dumps(checks),flush=True)
            finally:
                if connection:
                    connection.close()
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill();process.wait()


if __name__=='__main__':
    run()
