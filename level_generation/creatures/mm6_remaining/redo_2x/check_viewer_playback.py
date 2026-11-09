"""Exercise staged native-time browser playback. Mechanical evidence, not visual acceptance."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import shutil
import subprocess
import tempfile
import time
import urllib.request

import websocket


def check(project, viewer='review.html', output='review/browser_playback.json'):
    root = Path(project).resolve()
    if not (root / 'manifest.json').exists() or not (root / viewer).exists():
        root /= 'redo_2x'
    with tempfile.TemporaryDirectory(prefix='mm6-sprite-playback-', dir='/tmp') as work:
        log = open(Path(work) / 'chrome.log', 'w')
        process = subprocess.Popen([shutil.which('google-chrome'), '--headless', '--no-sandbox', '--disable-gpu',
            '--disable-dev-shm-usage', '--allow-file-access-from-files', '--disable-background-networking',
            '--no-first-run', '--remote-debugging-port=0', '--remote-allow-origins=*',
            '--user-data-dir='+work, (root/viewer).as_uri()+'?frame=0'], stdout=log, stderr=log,
            start_new_session=True)
        socket = None
        try:
            port_file = Path(work) / 'DevToolsActivePort'
            deadline = time.monotonic()+15
            while not port_file.exists():
                if process.poll() is not None or time.monotonic()>deadline:
                    raise RuntimeError((Path(work)/'chrome.log').read_text()[-3000:])
                time.sleep(.05)
            port = int(port_file.read_text().splitlines()[0])
            targets = json.load(urllib.request.urlopen('http://127.0.0.1:%d/json/list'%port))
            target = next(t for t in targets if t['type']=='page')
            socket = websocket.create_connection(target['webSocketDebuggerUrl'], timeout=240)
            call_id = 0
            def evaluate(expression, wait=False):
                nonlocal call_id
                call_id += 1
                socket.send(json.dumps(dict(id=call_id,method='Runtime.evaluate',params=dict(
                    expression=expression,awaitPromise=wait,returnByValue=True))))
                while True:
                    result = json.loads(socket.recv())
                    if result.get('id')==call_id:
                        assert 'error' not in result, result
                        result = result['result']
                        assert 'exceptionDetails' not in result, result
                        return result['result'].get('value')
            deadline=time.monotonic()+15
            while not evaluate("typeof manifest !== 'undefined' && typeof seq === 'function'"):
                assert time.monotonic()<deadline
                time.sleep(.05)
            current_manifest = json.loads((root/'manifest.json').read_text())
            embedded_manifest = json.loads(evaluate('JSON.stringify(manifest)'))
            assert embedded_manifest == current_manifest, 'Viewer embeds a stale manifest; rebuild the placement viewer'
            selectable_actions = set(evaluate("Array.from($('action').options).map(o=>o.value)"))
            assert selectable_actions <= set(current_manifest['animations'])
            alias_bindings = []
            for palette, actions in current_manifest['animations_by_palette'].items():
                for action, animation in actions.items():
                    if action in selectable_actions:
                        continue
                    canonical = next((name for name in selectable_actions
                        if actions[name]['views'] == animation['views']), None)
                    assert canonical is not None, f'{palette}/{action}: unselectable action has unique frames'
                    alias_bindings.append(dict(palette=palette, action=action, canonical=canonical))
            expression = r'''(async()=>{
                playing=false;
                const output=[], signatures=new Set();
                for(const palette of Object.keys(manifest.variants)){
                    $('palette').value=palette;
                    for(const action of Array.from($('action').options).map(o=>o.value)){
                        $('action').value=action;
                        if($('action').value!==action) throw Error('Missing action control: '+action);
                        for(let view=0;view<8;view++){
                            $('view').value=String(view);
                            const steps=seq(), signature=palette+JSON.stringify(steps);
                            if(signatures.has(signature))continue;
                            signatures.add(signature);
                            const paths=steps.map(s=>`native_variants/${s.frame}_${palette}.png`);
                            for(const s of steps)paths.push(manifest.pages[manifest.frames[s.frame].page].variant_previews[palette]);
                            await Promise.all([...new Set(paths)].map(p=>img(p).decode()));
                            reset();last=performance.now();playing=true;$('loop').checked=true;
                            const total=steps.reduce((n,s)=>n+s.duration_ms,0), start=performance.now(), seen=[];
                            await new Promise(resolve=>{
                                function sample(now){
                                    const s=steps[frame];
                                    if(s && (!seen.length || seen[seen.length-1].index!==frame))
                                        seen.push({index:frame,frame:s.frame,time_ms:now-start,mirrored:s.mirrored});
                                    if(now-start>=Math.max(100,total*2+60)){resolve();return;}
                                    requestAnimationFrame(sample);
                                }
                                requestAnimationFrame(sample);
                            });
                            playing=false;
                            const missing=steps.map((s,i)=>i).filter(i=>!seen.some(s=>s.index===i));
                            if(missing.length)throw Error(`${action}/${view}/${palette}: missing ${missing}`);
                            output.push({action,view,palette,sequence_ms:total,observed:seen,all_frames_seen:true});
                        }
                    }
                }
                $('action').value='walk';$('view').value='6';reset();playing=false;
                return output;
            })()'''
            rows = evaluate(expression, True)
            result = dict(method='Real requestAnimationFrame playback, two native-duration cycles per distinct palette/sequence/mirror binding',
                manifest_sha256=hashlib.sha256((root/'manifest.json').read_bytes()).hexdigest(),
                bindings=rows, aliases_verified_by_exact_metadata_sequence=alias_bindings,
                visual_acceptance=False, status='passed')
            result['viewer_sha256'] = hashlib.sha256((root/viewer).read_bytes()).hexdigest()
            (root/output).write_text(json.dumps(result,indent=2)+'\n')
            print(json.dumps(dict(distinct_bindings=len(rows),status='passed',visual_acceptance=False)))
        finally:
            if socket:
                try:
                    socket.send(json.dumps(dict(id=999999, method='Browser.close')))
                except websocket.WebSocketException:
                    pass  # A closing browser may already have closed the page connection.
                socket.close()
            try:process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            # Chrome children can outlive the launcher and still write the profile.
            # Own and stop the entire browser group before TemporaryDirectory cleanup.
            try:os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:pass
            log.close()


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('project')
    parser.add_argument('--viewer', default='review.html')
    parser.add_argument('--output', default='review/browser_playback.json')
    args=parser.parse_args()
    check(args.project, args.viewer, args.output)
