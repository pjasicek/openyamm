"""Exercise real frame edits in Chrome using temporary checkpoint/decision storage.

Run with a Python environment containing Pillow and websocket-client.
No production review files or sprite packages are modified.
"""

import argparse
import base64
import json
import os
from pathlib import Path
import select
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

import websocket


HERE = Path(__file__).resolve().parent


def run(collection=None, collection_smoke=False):
    with tempfile.TemporaryDirectory(prefix='mm6-editor-check-') as directory:
        temporary = Path(directory)
        server_arguments = [sys.executable, '-B', str(HERE / 'serve.py'), '--port', '0',
                            '--state-dir', str(temporary / 'state')]
        if collection:
            server_arguments.extend(['--collection', str(collection.resolve())])
        server = subprocess.Popen(server_arguments,
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        chrome = None
        socket = None
        try:
            deadline = time.monotonic() + 60
            while True:
                if time.monotonic() > deadline:
                    raise RuntimeError('Server startup timed out')
                if not select.select([server.stdout], [], [], 1)[0]:
                    continue
                line = server.stdout.readline()
                if line.startswith('Open http:'):
                    url = line.split()[1]
                    break
                if server.poll() is not None:
                    raise RuntimeError(line + server.stdout.read())
            log = (temporary / 'chrome.log').open('w')
            chrome = subprocess.Popen([
                shutil.which('google-chrome'), '--headless', '--no-sandbox', '--disable-gpu',
                '--disable-dev-shm-usage', '--remote-debugging-port=0', '--remote-allow-origins=*',
                '--window-size=1800,1200', '--user-data-dir=' + str(temporary / 'profile'), url,
            ], stdout=log, stderr=log, start_new_session=True)
            port_file = temporary / 'profile/DevToolsActivePort'
            deadline = time.monotonic() + 20
            while not port_file.exists():
                if chrome.poll() is not None or time.monotonic() > deadline:
                    raise RuntimeError((temporary / 'chrome.log').read_text()[-2000:])
                time.sleep(.05)
            port = int(port_file.read_text().splitlines()[0])
            targets = json.load(urllib.request.urlopen(f'http://127.0.0.1:{port}/json/list'))
            page = next(target for target in targets if target['type'] == 'page')
            socket = websocket.create_connection(page['webSocketDebuggerUrl'], timeout=30)
            call_id = 0

            def call(method, params=None):
                nonlocal call_id
                call_id += 1
                socket.send(json.dumps({'id': call_id, 'method': method, 'params': params or {}}))
                while True:
                    result = json.loads(socket.recv())
                    if result.get('id') == call_id:
                        assert 'error' not in result, result
                        return result['result']

            def evaluate(expression):
                result = call('Runtime.evaluate', {'expression': expression, 'awaitPromise': True,
                                                  'returnByValue': True})
                assert 'exceptionDetails' not in result, result
                return result['result'].get('value')

            def wait(expression):
                deadline = time.monotonic() + 20
                while not evaluate(expression):
                    if time.monotonic() > deadline:
                        raise AssertionError(f'Timed out: {expression}')
                    time.sleep(.05)

            def key(name, shift=False):
                event = {'key': ' ' if name == 'Space' else name, 'code': name, 'modifiers': 8 if shift else 0}
                call('Input.dispatchKeyEvent', {'type': 'keyDown', **event})
                call('Input.dispatchKeyEvent', {'type': 'keyUp', **event})

            def drag(x, y, dx, dy):
                call('Input.dispatchMouseEvent', {'type': 'mousePressed', 'x': x, 'y': y,
                                                 'button': 'left', 'clickCount': 1})
                call('Input.dispatchMouseEvent', {'type': 'mouseMoved', 'x': x + dx, 'y': y + dy,
                                                 'button': 'left', 'buttons': 1})
                call('Input.dispatchMouseEvent', {'type': 'mouseReleased', 'x': x + dx, 'y': y + dy,
                                                 'button': 'left', 'clickCount': 1})

            def ready():
                wait('typeof state !== "undefined" && !!state.manifest && !state.switching && !$("play").disabled')

            ready()
            assert evaluate('state.families.length') == 60
            assert evaluate('$("masterFrame").options.length === Object.keys(state.manifest.frames).length')
            if collection_smoke:
                expected = json.loads(collection.read_text())
                queue = json.load(urllib.request.urlopen(url + 'api/families'))
                assert queue['collection']['id'] == expected['collection_id']
                assert not queue['excluded']
                assert {f['id']: f['artifact_sha256'] for f in queue['families']} == {
                    f['creature'].replace(':', '_'): f['artifact_sha256'] for f in expected['families']}
                assert evaluate('document.title') == expected['title']
                assert all(f['decision'] is None for f in queue['families'])
                for identifier in ['mm6_arc1', 'mm6_goblin', 'mm6_wdm', 'mm6_natm', 'mm6_ckt']:
                    evaluate(f'showFamily(state.families.findIndex(f=>f.id==={json.dumps(identifier)}))')
                    ready()
                    assert evaluate('currentFamily().id') == identifier
                    assert evaluate('$("masterFrame").options.length === Object.keys(state.manifest.frames).length')
                    assert evaluate('$("native").width>0 && $("restored").width>0')
                assert 'video ESRGAN' in evaluate('currentFamily().source')
                family = evaluate('currentFamily()')
                name = evaluate('currentStep().frame')
                evaluate('$("centerGuide").checked=false; renderStage(); '
                         'window.collectionNative=$("native").toDataURL(); $("restored").focus()')
                key('ArrowRight')
                evaluate('changeScale(1.03); flushFixups()')
                assert evaluate('frameFixup(currentStep().frame).offset_px') == [1, 0]
                assert evaluate('frameFixup(currentStep().frame).scale_factor') == 1.03
                assert evaluate('$("native").toDataURL()===window.collectionNative')
                evaluate('saveDecision("accepted",false)')
                decision = json.loads((temporary / 'state/decisions.json').read_text())['decisions']
                saved = decision[family['id']][family['artifact_sha256']]
                assert saved['fixups_snapshot'][name]['scale_factor'] == 1.03
                assert saved['fixups_snapshot'][name]['offset_px'] == [1, 0]
                call('Page.reload')
                time.sleep(.3)
                ready()
                evaluate('showFamily(state.families.findIndex(f=>f.id==="mm6_ckt"))')
                ready()
                assert evaluate(f'frameFixup({json.dumps(name)}).scale_factor') == 1.03
                assert evaluate(f'frameFixup({json.dumps(name)}).offset_px') == [1, 0]
                assert evaluate('currentFamily().decision.decision') == 'accepted'
                # Landmark annotations must persist separately from placement.
                evaluate('showFamily(state.families.findIndex(f=>f.id==="mm6_arc1"))')
                ready()
                evaluate('pauseForEdit(); $("landmarkPanel").open=true; $("editLandmarks").checked=true; '
                         '$("showLandmarks").checked=true; $("landmarkKind").value="eye1"; renderStage()')
                assert evaluate('!!landmarkPoint(currentStep().frame,"original","head")')
                canvas_point = evaluate('(() => { const c=$("restored"),r=c.getBoundingClientRect(); '
                    'const p=landmarkScreenPoint(currentStep(),"restored",[210.25,70.5]); '
                    'return [r.x+p[0]*r.width/c.width,r.y+p[1]*r.height/c.height]; })()')
                drag(canvas_point[0], canvas_point[1], 0, 0)
                evaluate('flushFixups()')
                assert evaluate('landmarkPoint(currentStep().frame,"restored","eye1").xy') == [210.25, 70.5]
                assert evaluate('frameFixup(currentStep().frame).offset_px') == [0, 0]
                key('ArrowRight')
                assert evaluate('landmarkPoint(currentStep().frame,"restored","eye1").xy') == [210.75, 70.5]
                assert evaluate('frameFixup(currentStep().frame).offset_px') == [0, 0]
                evaluate('$("landmarkUndo").click(); flushFixups()')
                evaluate('$("landmarkKind").value="eye2"; $("landmarkSide").value="restored"; '
                         '$("landmarkAbsent").click(); flushFixups()')
                assert evaluate('landmarkPoint(currentStep().frame,"restored","eye2").xy') is None
                name = evaluate('currentStep().frame')
                call('Page.reload')
                time.sleep(.3)
                ready()
                assert evaluate(f'landmarkPoint({json.dumps(name)},"restored","eye1").xy') == [210.25, 70.5]
                assert evaluate(f'landmarkPoint({json.dumps(name)},"restored","eye2").xy') is None
                exported = json.load(urllib.request.urlopen(url + 'api/landmarks/export'))
                archer = next(f for f in exported['families'] if f['id'] == 'mm6_arc1')
                point = archer['frames'][name]['points']['restored']['eye1']
                assert point['logical_xy'] == [210.25, 70.5] and point['status'] == 'recorded'
                assert 'atlas_local_xy' in point and 'generated_sheet_xy' in point
                evaluate('saveDecision("accepted",false)')
                records = json.loads((temporary / 'state/decisions.json').read_text())['decisions']
                family = evaluate('currentFamily()')
                snapshot = records[family['id']][family['artifact_sha256']]['landmarks_snapshot']
                assert snapshot[name]['restored'] == {'eye1': [210.25, 70.5], 'eye2': None}
                # One-click helpers must honor existing scale, fractional anchors and a mirrored view.
                assert evaluate('!!landmarkPoint(currentStep().frame,"original","head_top") && '
                                '!!landmarkPoint(currentStep().frame,"restored","head_top")')
                evaluate('$("editLandmarks").checked=false; '
                         'changeFrame(currentStep().frame,{offset_px:[14,-8],scale_factor:1.07,scale_anchor:"top"}); '
                         '$("headCenterGuide").click()')
                assert evaluate('Math.abs(guideScreenX(currentStep())-'
                    'landmarkScreenPoint(currentStep(),"original",landmarkPoint(currentStep().frame,"original","head").xy)[0])<1e-7')
                assert evaluate('frameFixup(currentStep().frame).offset_px') == [14, -8]
                evaluate('$("headAlignX").click()')
                assert evaluate('frameFixup(currentStep().frame).offset_px[1]') == -8
                assert evaluate('frameFixup(currentStep().frame).scale_factor') == 1.07
                assert evaluate('Math.abs(landmarkActorPoint(currentStep().frame,"restored",'
                    'landmarkPoint(currentStep().frame,"restored","head").xy)[0]-'
                    'landmarkPoint(currentStep().frame,"original","head").xy[0])<=.25')
                before_fit_x = evaluate('landmarkActorPoint(currentStep().frame,"restored",'
                    'landmarkPoint(currentStep().frame,"restored","head").xy)[0]')
                evaluate('$("headFitFeet").click()')
                assert evaluate('frameFixup(currentStep().frame).scale_anchor') == 'bottom'
                assert evaluate('Math.abs(heightBounds(currentStep()).native[1]-'
                                'heightBounds(currentStep()).restored[1])<=.25')
                assert evaluate('Math.abs(landmarkActorPoint(currentStep().frame,"restored",'
                    'landmarkPoint(currentStep().frame,"restored","head_top").xy)[1]-'
                    'landmarkPoint(currentStep().frame,"original","head_top").xy[1])<=.25')
                assert abs(evaluate('landmarkActorPoint(currentStep().frame,"restored",'
                    'landmarkPoint(currentStep().frame,"restored","head").xy)[0]') - before_fit_x) <= .25
                fitted = evaluate('frameFixup(currentStep().frame)')
                evaluate('$("headFitFeet").click()')
                assert evaluate('frameFixup(currentStep().frame)') == fitted
                evaluate('$("headTopGuide").click()')
                assert evaluate('Math.abs(guideScreenY(currentStep())-'
                    'landmarkScreenPoint(currentStep(),"original",landmarkPoint(currentStep().frame,"original","head_top").xy)[1])<1e-7')
                # Turning a stored step into its mirrored alias must not change its saved proposal.
                evaluate('state.manualStep={...currentStep(),mirrored:true}; renderStage(); $("headCenterGuide").click()')
                assert evaluate('Math.abs(guideScreenX(currentStep())-'
                    'landmarkScreenPoint(currentStep(),"original",landmarkPoint(currentStep().frame,"original","head").xy)[0])<1e-7')
                evaluate('$("headAlignX").click()')
                assert evaluate('frameFixup(currentStep().frame)') == fitted
                evaluate('$("landmarkUndoGuide").click(); $("landmarkUndoPlacement").click(); flushFixups()')
                # Restore a representative Harpy frame to show the actual requested sidebar in the screenshot.
                evaluate('state.manualStep=null; showFamily(state.families.findIndex(f=>f.id==="mm6_hrp"))')
                ready()
                assert evaluate('!$("headFitFeet").disabled')
                # Clip shortcuts win over point/placement nudging and skip mirrored-only views.
                evaluate('state.action="walk"; state.view="1"; manualClip()')
                ready()
                evaluate('$("editLandmarks").checked=true; $("restored").focus()')
                untouched = evaluate('JSON.stringify([state.fixups.frames,state.fixups.landmarks])')
                key('ArrowLeft', shift=True)
                ready()
                assert evaluate('[state.action,state.view]') == ['walk', '0']
                assert evaluate('JSON.stringify([state.fixups.frames,state.fixups.landmarks])') == untouched
                for view in range(1, 5):
                    key('ArrowRight', shift=True)
                    ready()
                    assert evaluate('[state.action,state.view]') == ['walk', str(view)]
                for expected_clip in [['attack', '0'], ['hit', '0']]:
                    key('ArrowRight', shift=True)
                    ready()
                    assert evaluate('[state.action,state.view]') == expected_clip
                key('ArrowLeft', shift=True)
                ready()
                assert evaluate('[state.action,state.view]') == ['attack', '0']
                key('ArrowLeft', shift=True)
                ready()
                assert evaluate('[state.action,state.view]') == ['walk', '4']
                evaluate('state.action="walk"; state.view="0"; manualClip()')
                ready()
                key('ArrowLeft', shift=True)
                ready()
                assert evaluate('[state.action,state.view]') == ['corpse', '0']
                key('ArrowRight', shift=True)
                ready()
                assert evaluate('[state.action,state.view]') == ['walk', '0']
                assert evaluate('JSON.stringify([state.fixups.frames,state.fixups.landmarks])') == untouched
                # Combined alignment is one undo step and retains notes/flags.
                evaluate('changeFrame(currentStep().frame,{offset_px:[14,-8],scale_factor:1.07,scale_anchor:"top",'
                         'regenerate:true,note:"Keep this note"}); $("restored").focus()')
                before_shortcut = evaluate('frameFixup(currentStep().frame)')
                undo_count = evaluate('state.undo.get(currentStep().frame).length')
                key('Space', shift=True)
                assert evaluate('!state.playing && state.undo.get(currentStep().frame).length') == undo_count + 1
                assert evaluate('frameFixup(currentStep().frame).scale_anchor') == 'bottom'
                assert evaluate('frameFixup(currentStep().frame).note') == 'Keep this note'
                assert evaluate('frameFixup(currentStep().frame).regenerate')
                assert evaluate('Math.abs(landmarkActorPoint(currentStep().frame,"restored",'
                    'landmarkPoint(currentStep().frame,"restored","head").xy)[0]-'
                    'landmarkPoint(currentStep().frame,"original","head").xy[0])<=.25')
                assert evaluate('Math.abs(heightBounds(currentStep()).native[1]-'
                                'heightBounds(currentStep()).restored[1])<=.25')
                assert evaluate('Math.abs(landmarkActorPoint(currentStep().frame,"restored",'
                    'landmarkPoint(currentStep().frame,"restored","head_top").xy)[1]-'
                    'landmarkPoint(currentStep().frame,"original","head_top").xy[1])<=.25')
                evaluate('$("landmarkUndoPlacement").click()')
                assert evaluate('frameFixup(currentStep().frame)') == before_shortcut
                # Missing landmarks allow just one action, or leave the frame unchanged if neither is available.
                evaluate('changeLandmark(currentStep().frame,"restored","head_top",null); $("restored").focus()')
                key('Space', shift=True)
                x_only = evaluate('frameFixup(currentStep().frame)')
                assert x_only['offset_px'][1] == -8 and x_only['scale_factor'] == 1.07
                assert x_only['offset_px'][0] != 14
                evaluate('$("landmarkUndoPlacement").click(); '
                         'changeLandmark(currentStep().frame,"restored","head_top",null,false,true); '
                         'changeLandmark(currentStep().frame,"restored","head",null); $("restored").focus()')
                key('Space', shift=True)
                assert evaluate('frameFixup(currentStep().frame).scale_anchor') == 'bottom'
                assert evaluate('Math.abs(heightBounds(currentStep()).native[1]-'
                                'heightBounds(currentStep()).restored[1])<=.25')
                evaluate('changeLandmark(currentStep().frame,"restored","head_top",null); $("restored").focus()')
                unavailable = evaluate('[frameFixup(currentStep().frame),state.edits]')
                key('Space', shift=True)
                assert evaluate('[frameFixup(currentStep().frame),state.edits]') == unavailable
                assert 'No paired' in evaluate('$("landmarkActionStatus").textContent')
                evaluate('$("frameNote").focus()')
                key('ArrowRight', shift=True)
                key('Space', shift=True)
                assert evaluate('[state.action,state.view]') == ['walk', '0']
                assert evaluate('[frameFixup(currentStep().frame),state.edits]') == unavailable
                evaluate('changeLandmark(currentStep().frame,"restored","head",null,false,true); '
                         'changeLandmark(currentStep().frame,"restored","head_top",null,false,true); '
                         '$("restored").focus(); flushFixups()')
                held_key_edits = evaluate('state.edits')
                evaluate('$("restored").dispatchEvent(new KeyboardEvent("keydown",'
                         '{key:" ",code:"Space",shiftKey:true,repeat:true,bubbles:true}))')
                assert evaluate('state.edits') == held_key_edits
                assert evaluate('(() => { const bar=document.querySelector(".landmark-bar").getBoundingClientRect(); '
                    'const viewport=document.querySelector(".viewport").getBoundingClientRect(); '
                    'return bar.width>=150 && bar.right<=viewport.left+1 && Math.abs(bar.top-viewport.top)<1; })()')
                screenshot = call('Page.captureScreenshot', {'format': 'png', 'captureBeyondViewport': False})
                Path('/tmp/mm6-packed-outline-collection.png').write_bytes(base64.b64decode(screenshot['data']))
                print('PASS: exact 60-family collection, selected video/outline/Goblin art, '
                      'landmark persistence/export, sidebar, head alignment/scale, Shift shortcuts, partial references, '
                      'one-step undo, mirroring, isolated state; '
                      'screenshot /tmp/mm6-packed-outline-collection.png')
                return
            evaluate('$("centerGuide").checked=false; renderStage(); '
                     'window.originalBefore=$("native").toDataURL(); window.restoredBefore=$("restored").toDataURL(); '
                     'window.layoutBefore=JSON.stringify(state.layout); $("restored").focus()')
            key('ArrowRight')
            assert evaluate('frameFixup(currentStep().frame).offset_px') == [1, 0]
            assert evaluate('$("native").toDataURL() === window.originalBefore')
            assert evaluate('$("restored").toDataURL() !== window.restoredBefore')
            assert evaluate('JSON.stringify(state.layout) === window.layoutBefore')
            key('ArrowDown')
            assert evaluate('frameFixup(currentStep().frame).offset_px') == [1, 1]
            evaluate('$("undoFrame").click()')
            assert evaluate('frameFixup(currentStep().frame).offset_px') == [1, 0]

            # Drag reference top down by six atlas pixels. Both canvases must render at the same Y.
            evaluate('$("centerGuide").checked=true; renderStage()')
            initial_guides = evaluate('({...state.fixups.guides})')
            geometry = evaluate('(() => { const r=$("native").getBoundingClientRect(); '
                                'return [r.x+25,r.y+guideScreenY(currentStep()), '
                                'Number($("zoom").value)/tier()]; })()')
            drag(geometry[0], geometry[1], 0, 6 * geometry[2])
            assert evaluate('state.fixups.guides.y') == initial_guides['y'] + 3
            lines = evaluate('(() => { const result=[]; for(const id of ["native","restored"]) { '
                             'const c=$(id).getContext("2d"); const old=c.moveTo; const ys=[]; '
                             'c.moveTo=function(x,y){ if(x===0) ys.push(y); return old.call(this,x,y); }; '
                             'drawCanvas($(id),currentStep(),id==="native"); c.moveTo=old; result.push(ys); } '
                             'return result; })()')
            assert lines[0][0] == lines[1][0], lines
            evaluate('$("native").focus()')
            key('ArrowUp')
            assert evaluate('state.fixups.guides.y') == initial_guides['y'] + 2.5
            # Move the center guide without moving either sprite; a drag is one undo step.
            geometry = evaluate('(() => { const r=$("native").getBoundingClientRect(); '
                                'return [r.x+guideScreenX(currentStep()),r.y+30, '
                                'Number($("zoom").value)/tier()]; })()')
            drag(geometry[0], geometry[1], 8 * geometry[2], 0)
            assert evaluate('state.fixups.guides.x') == initial_guides['x'] + 4
            evaluate('$("undoGuides").click()')
            assert evaluate('state.fixups.guides.x') == initial_guides['x']
            drag(geometry[0], geometry[1], 8 * geometry[2], 0)
            key('ArrowLeft')
            assert evaluate('state.fixups.guides.x') == initial_guides['x'] + 3.5
            assert evaluate('frameFixup(currentStep().frame).offset_px') == [1, 0]
            assert evaluate('(() => { renderStage(); const x=Math.floor(guideScreenX(currentStep())); '
                            'const a=$("native").getContext("2d").getImageData(x,0,2,$("native").height).data; '
                            'const b=$("restored").getContext("2d").getImageData(x,0,2,$("restored").height).data; '
                            'return a.every((value,i)=>value===b[i]); })()')
            # Check the guide's opaque pixel colors against independently rendered full sprite layers.
            assert evaluate('(() => { const step=currentStep(), x=Math.floor(guideScreenX(step)); '
                            'const w=$("native").width,h=$("native").height; const masks=[true,false].map(original=>{ '
                            'const c=document.createElement("canvas");c.width=w;c.height=h; '
                            'const ctx=c.getContext("2d");drawSprite(ctx,step,original); '
                            'return ctx.getImageData(x,0,1,h).data;}); '
                            'const output=$("native").getContext("2d").getImageData(x,0,2,h).data; '
                            'const colors=[[0,255,0,255],[255,0,0,255],[255,105,180,255]]; '
                            'for(let y=0;y<h;y++){const bits=(masks[0][y*4+3]>0?1:0)|(masks[1][y*4+3]>0?2:0); '
                            'for(let lane=0;lane<2;lane++){const expected=colors[bits===3?lane+1:bits]; '
                            'if(expected.some((v,i)=>output[(y*2+lane)*4+i]!==v))return false;}}return true; })()')
            evaluate('$("regenerate").click(); $("frameNote").value="Check head scale"; '
                     '$("frameNote").dispatchEvent(new Event("input")); flushFixups()')
            family = evaluate('currentFamily()')
            name = evaluate('currentStep().frame')
            checkpoint = json.loads((temporary / 'state/frame_fixups.json').read_text())
            record = checkpoint['families'][family['id']][family['artifact_sha256']]['frames'][name]
            assert record['offset_px'] == [1, 0]
            saved_guides = evaluate('({...state.fixups.guides})')
            assert checkpoint['families'][family['id']][family['artifact_sha256']]['guides'] == saved_guides
            assert record['regenerate'] and record['note'] == 'Check head scale'
            assert record['original_crop_origin_px'] == evaluate('state.manifest.frames[currentStep().frame].crop_origin_px')

            # Guides are family references: they must not follow animated silhouette bounds.
            assert evaluate('(() => { const original=[guideScreenX(currentStep()),guideScreenY(currentStep())]; '
                            'for(let i=0;i<steps().length;i++){chooseClipFrame(i); '
                            'if(guideScreenX(currentStep())!==original[0] || '
                            'guideScreenY(currentStep())!==original[1])return false;} '
                            'chooseClipFrame(0); return true; })()')

            # Reload restores frame edits and the shared guide checkpoint.
            call('Page.reload')
            time.sleep(.3)
            ready()
            assert evaluate('({...state.fixups.guides})') == saved_guides
            assert evaluate('frameFixup(currentStep().frame).offset_px') == [1, 0]
            assert evaluate('$("regenerate").checked')

            # Canonical stored X reverses for mirrored screen movement, including drag at another zoom.
            evaluate('state.view=Object.entries(action().views).find(([v,s])=>s[0]?.mirrored)[0]; '
                     '$("view").value=state.view; manualClip()')
            ready()
            assert evaluate('({...state.fixups.guides})') == saved_guides
            evaluate('window.drawSizes=()=>{const sizes=[];for(const id of ["native","restored"]){ '
                     'const c=$(id).getContext("2d"),old=c.drawImage; '
                     'c.drawImage=function(...args){sizes.push(args.slice(-2));return old.apply(this,args);}; '
                     'drawCanvas($(id),currentStep(),id==="native");c.drawImage=old;}return sizes;}; '
                     'window.guideContent=()=>[(guideScreenX(currentStep())-state.layout.originX)/Number($("zoom").value),'
                     '(guideScreenY(currentStep())-state.layout.originY)/Number($("zoom").value)]')
            sizes_before = evaluate('drawSizes()')
            guide_content = evaluate('guideContent()')
            evaluate('$("zoom").value="4"; configureCanvas(); $("restored").focus()')
            assert evaluate('drawSizes()') == [[value * 2 for value in size] for size in sizes_before]
            assert all(abs(a-b) < 1e-9 for a, b in zip(guide_content, evaluate('guideContent()')))
            assert evaluate('$("zoom").selectedOptions[0].textContent') == '400%'
            before = evaluate('frameFixup(currentStep().frame).offset_px')
            key('ArrowRight')
            assert evaluate('frameFixup(currentStep().frame).offset_px') == [before[0] - 1, before[1]]
            geometry = evaluate('(() => { const r=$("restored").getBoundingClientRect(); '
                                'return [r.x+30,r.y+30,Number($("zoom").value)*frameScale(currentStep())/tier()]; })()')
            drag(geometry[0], geometry[1], 3 * geometry[2], 2 * geometry[2])
            assert evaluate('frameFixup(currentStep().frame).offset_px') == [before[0] - 4, before[1] + 2]
            evaluate('$("native").focus()')
            center_before = evaluate('state.fixups.guides.x')
            key('ArrowRight')
            assert evaluate('state.fixups.guides.x') == center_before + .5
            evaluate('flushFixups()')

            # Auto top affects only the guide; reset offset retains flags/notes.
            evaluate('showFamily(0)')
            ready()
            assert evaluate('$("zoom").value') == '4'
            evaluate('$("resetGuide").click(); $("resetCenter").click(); $("resetFrame").click(); flushFixups()')
            assert evaluate('state.fixups.guides.y === automaticGuidePosition(currentStep(),"y")')
            assert evaluate('state.fixups.guides.x === automaticGuidePosition(currentStep(),"x")')
            assert evaluate('frameFixup(currentStep().frame).regenerate')
            assert evaluate('frameFixup(currentStep().frame).offset_px') == [0, 0]
            evaluate('$("play").click()')
            elapsed = evaluate('state.elapsed')
            stationary = evaluate('[guideScreenX(currentStep()),guideScreenY(currentStep())]')
            time.sleep(.3)
            assert evaluate('state.elapsed') > elapsed
            assert evaluate('[guideScreenX(currentStep()),guideScreenY(currentStep())]') == stationary
            evaluate('pauseForEdit(); $("masterFrame").selectedIndex=$("masterFrame").options.length-1; '
                     '$("masterFrame").onchange()')
            ready()
            assert evaluate('currentStep().frame === $("masterFrame").value && !!state.manualStep')
            assert evaluate('[guideScreenX(currentStep()),guideScreenY(currentStep())]') == stationary

            # Stale tab revisions and mismatching artifact hashes must never overwrite checkpoints.
            def post_status(body):
                request = urllib.request.Request(url + 'api/fixups', data=json.dumps(body).encode(),
                                                 headers={'Content-Type': 'application/json'})
                try:
                    return urllib.request.urlopen(request).status
                except urllib.error.HTTPError as error:
                    return error.code

            payload = {'family': family['id'], 'manifest_sha256': family['manifest_sha256'],
                       'artifact_sha256': family['artifact_sha256'], 'revision': 0, 'frames': {}}
            assert post_status(payload) == 409
            payload['artifact_sha256'] = 'stale'
            assert post_status(payload) == 409
            assert not (temporary / 'state/decisions.json').exists()

            # Acceptance snapshots exactly the preview's checkpoint and becomes stale after another edit.
            evaluate('saveDecision("accepted",false)')
            decisions = json.loads((temporary / 'state/decisions.json').read_text())
            accepted = decisions['decisions'][family['id']][family['artifact_sha256']]
            assert accepted['fixups_revision'] == evaluate('state.fixups.revision')
            assert accepted['fixups_snapshot'][name]['regenerate']
            assert accepted['guides_snapshot'] == evaluate('({...state.fixups.guides})')
            evaluate('nudge(0,1); flushFixups()')
            assert evaluate('!decisionMatchesFixups(currentFamily())')

            # A save conflict retains the local draft and blocks family navigation.
            evaluate('state.fixups.revision=0; nudge(1,0); showFamily(1)')
            assert evaluate('state.familyIndex') == 0
            assert evaluate('state.edits !== state.savedEdits && !$("exportUnsaved").hidden')
            evaluate('state.fixups.revision=state.manifest.review_fixups.revision; '
                     'state.savedEdits=state.edits')  # Discard isolated test draft before screenshot.
            evaluate('showFamily(0)')
            ready()
            # Per-frame scale trials preserve placement and the original, and survive checkpoint reload.
            evaluate('showFamily(state.families.findIndex(f=>f.id==="mm6_cle"))')
            ready()
            evaluate('$("masterFrame").value="clewald0"; $("masterFrame").onchange()')
            ready()
            evaluate('$("centerGuide").checked=false; renderStage(); '
                     'window.nativeBeforeScale=$("native").toDataURL(); '
                     'window.layoutBeforeScale=JSON.stringify(state.layout); '
                     'window.beforeScale=restoredGeometry(currentStep().frame); $("applyScaleHint").click()')
            factor = 1.0256477123075118
            assert abs(evaluate('frameFixup("clewald0").scale_factor') - factor) < 1e-12
            assert evaluate('$("native").toDataURL()===window.nativeBeforeScale')
            assert evaluate('JSON.stringify(state.layout)===window.layoutBeforeScale')
            assert evaluate('frameFixup("clewald0").offset_px') == [0, 0]
            assert abs(evaluate('restoredGeometry("clewald0").height/window.beforeScale.height') - factor) < 1e-12
            evaluate('$("applyScaleHint").click()')
            assert abs(evaluate('frameFixup("clewald0").scale_factor') - factor) < 1e-12
            evaluate('window.scalePosition=restoredGeometry("clewald0"); nudge(1,0)')
            assert abs(evaluate('restoredGeometry("clewald0").x-window.scalePosition.x') - 1) < 1e-12
            evaluate('$("previewScale").checked=false; renderStage()')
            assert evaluate('restoredGeometry("clewald0").scale') == 1
            assert evaluate('frameFixup("clewald0").offset_px') == [1, 0]
            evaluate('$("previewScale").checked=true; $("resetScale").click()')
            assert evaluate('frameFixup("clewald0").scale_factor') == 1
            evaluate('$("undoFrame").click()')
            assert abs(evaluate('frameFixup("clewald0").scale_factor') - factor) < 1e-12
            evaluate('$("scaleAnchor").value="top"; $("scaleAnchor").onchange(); flushFixups()')
            bounds = evaluate('heightBounds(currentStep()).restored')
            evaluate('$("previewScale").checked=false; renderStage()')
            assert abs(evaluate('heightBounds(currentStep()).restored[0]') - bounds[0]) < 1e-12
            evaluate('$("previewScale").checked=true; renderStage()')
            call('Page.reload')
            time.sleep(.3)
            ready()
            assert abs(evaluate('frameFixup("clewald0").scale_factor') - factor) < 1e-12
            assert evaluate('frameFixup("clewald0").scale_anchor') == 'top'
            assert evaluate('frameFixup("clewald0").offset_px') == [1, 0]
            evaluate('state.manualStep=null; state.action="walk"; state.view="7"; manualClip()')
            ready()
            evaluate('changeScale(1.03); window.mirroredOffset=frameFixup(currentStep().frame).offset_px[0]; nudge(1,0)')
            assert evaluate('frameFixup(currentStep().frame).offset_px[0]') == evaluate('window.mirroredOffset') - 1
            evaluate('$("masterFrame").value="clewald0"; $("masterFrame").onchange()')
            ready()
            evaluate('changeScale(1.5); $("scaleAnchor").value="bottom"; $("scaleAnchor").onchange()')
            assert evaluate('scalePreviewClipped() && !$("fitScale").disabled')
            evaluate('$("fitScale").click()')
            assert not evaluate('scalePreviewClipped()')
            evaluate(f'changeScale({factor}); $("scaleAnchor").value="top"; $("scaleAnchor").onchange(); '
                     'configureCanvas(true)')
            evaluate('flushFixups()')
            evaluate('$("zoom").value="2"; configureCanvas(); $("restored").blur()')

            # Family matching uses each original pose, exact center anchoring and absolute export bounds.
            fixture = dict(pixels_per_logical_pixel=2, anchor='center', logical_canvas=[100, 100],
                           frames={'a': dict(source_canvas=[100, 93], crop_origin_px=[10, 20])},
                           review_native_bounds={'a': [0, 20, 20, 60]},
                           review_restored_bounds={'a': [0, 10, 40, 110]})
            assert evaluate(f'familyHeightMatch({json.dumps(fixture)}, "a")') == dict(factor=.8, offsetY=-17)
            fixture['anchor'] = 'bottom-center'
            assert evaluate(f'familyHeightMatch({json.dumps(fixture)}, "a")') == dict(factor=.8, offsetY=-10)
            fixture['review_restored_bounds']['a'] = None
            assert evaluate(f'familyHeightMatch({json.dumps(fixture)}, "a").skip') == 'empty silhouette'
            fixture['review_restored_bounds']['a'] = [0, 10, 40, 20]
            assert evaluate(f'familyHeightMatch({json.dumps(fixture)}, "a").skip') == 'outside size range'
            fixture['review_restored_bounds']['a'] = [0, 10, 40, 210]
            assert evaluate(f'familyHeightMatch({json.dumps(fixture)}, "a").skip') == 'outside size range'
            fixture['review_restored_bounds']['a'] = [0, 10, 40, 110]
            fixture['frames']['a']['crop_origin_px'][1] = 20000
            assert evaluate(f'familyHeightMatch({json.dumps(fixture)}, "a").skip') == 'outside offset range'

            evaluate('showFamily(state.families.findIndex(f=>f.id==="mm6_cob"))')
            ready()
            evaluate('window.familyFrame=currentStep().frame; '
                     'changeFrame(window.familyFrame,{offset_px:[7,43],scale_factor:1.1,scale_anchor:"top", '
                     'regenerate:true,note:"family match review"}); flushFixups()')
            before_store = json.loads((temporary / 'state/frame_fixups.json').read_text())['families']
            evaluate('window.beforeFamilyMatch=structuredClone(state.fixups.frames); '
                     'window.familyGuidesBefore=JSON.stringify(state.fixups.guides); '
                     'window.familyLayoutBefore=JSON.stringify(state.layout); '
                     '$("centerGuide").checked=false; renderStage(); '
                     'window.nativeBeforeMatch=$("native").toDataURL(); '
                     '$("previewFixups").checked=false; $("previewScale").checked=false; $("matchFamily").click()')
            assert evaluate('$("previewFixups").checked && $("previewScale").checked && !state.playing')
            assert evaluate('$("native").toDataURL()===window.nativeBeforeMatch')
            assert evaluate('JSON.stringify(state.fixups.guides)===window.familyGuidesBefore')
            assert evaluate('JSON.stringify(state.layout)===window.familyLayoutBefore')
            assert evaluate('frameFixup(window.familyFrame).offset_px[0]') == 7
            assert evaluate('frameFixup(window.familyFrame).regenerate')
            assert evaluate('frameFixup(window.familyFrame).note') == 'family match review'
            assert evaluate('!$("undoFamilyMatch").disabled && state.familyMatchUndo.size > 1')

            def check_matched_family():
                bounds = evaluate('Object.keys(state.manifest.frames).filter(name=> '
                                  '!familyHeightMatch(state.manifest,name).skip).map(name=>heightBounds({frame:name}))')
                assert len(bounds) > 1
                bottom_tolerance = .5 / evaluate('tier()') + 1e-9
                for bound in bounds:
                    original, restored = bound['native'], bound['restored']
                    assert abs((original[1] - original[0]) - (restored[1] - restored[0])) < 1e-9
                    assert abs(original[1] - restored[1]) <= bottom_tolerance

            check_matched_family()
            evaluate('window.familyAfterMatch=JSON.stringify(state.fixups.frames); window.matchEdits=state.edits; '
                     '$("matchFamily").click()')
            assert evaluate('JSON.stringify(state.fixups.frames)===window.familyAfterMatch && '
                            'state.edits===window.matchEdits')
            assert evaluate('!$("undoFamilyMatch").disabled')
            # Undo the whole match while retaining later horizontal nudges, flags and notes.
            evaluate('changeFrame(window.familyFrame,{offset_px:[9,frameFixup(window.familyFrame).offset_px[1]], '
                     'note:"later family note"}); $("undoFamilyMatch").click()')
            assert evaluate('frameFixup(window.familyFrame).offset_px') == [9, 43]
            assert evaluate('frameFixup(window.familyFrame).scale_factor') == 1.1
            assert evaluate('frameFixup(window.familyFrame).scale_anchor') == 'top'
            assert evaluate('frameFixup(window.familyFrame).regenerate && '
                            'frameFixup(window.familyFrame).note==="later family note" && '
                            '$("undoFamilyMatch").disabled')
            assert evaluate('Object.keys(state.manifest.frames).every(name=> { '
                            'const before=window.beforeFamilyMatch[name]||{}, now=frameFixup(name); '
                            'return now.scale_factor===(before.scale_factor??1) && '
                            'now.scale_anchor===(before.scale_anchor??"bottom") && '
                            'now.offset_px[1]===(before.offset_px?.[1]??0); })')
            evaluate('$("matchFamily").click(); flushFixups()')
            after_store = json.loads((temporary / 'state/frame_fixups.json').read_text())['families']
            assert {k: v for k, v in before_store.items() if k != 'mm6_cob'} == {
                k: v for k, v in after_store.items() if k != 'mm6_cob'}
            saved_match = after_store['mm6_cob'][evaluate('currentFamily().artifact_sha256')]['frames']
            call('Page.reload')
            time.sleep(.3)
            ready()
            assert evaluate('state.fixups.frames') == saved_match
            assert evaluate('$("undoFamilyMatch").disabled')
            check_matched_family()
            evaluate('state.action="walk"; state.view="7"; manualClip()')
            ready()
            assert evaluate('currentStep().mirrored')
            check_matched_family()
            evaluate('$("palette").selectedIndex=$("palette").options.length-1; $("palette").onchange()')
            ready()
            check_matched_family()
            evaluate('$("editMode").checked=false; $("editMode").onchange()')
            assert evaluate('$("matchFamily").disabled && $("undoFamilyMatch").disabled')
            evaluate('$("editMode").checked=true; $("editMode").onchange()')
            screenshot = call('Page.captureScreenshot', {'format': 'png'})
            Path('/tmp/mm6-family-height-match.png').write_bytes(base64.b64decode(screenshot['data']))
            print('PASS: family silhouette height/bottom matching; all masters, palettes and mirrored views; '
                  'center anchoring; empty/range skips; non-compounding apply; batch undo preserves notes/X; '
                  'checkpoint reload; other families unchanged. Screenshot: /tmp/mm6-family-height-match.png')

            # Color controls use actual sprite/mask pixels, persist per palette, and leave native art intact.
            evaluate('showFamily(state.families.findIndex(f=>f.id==="mm6_wdm"))')
            ready()
            evaluate('$("centerGuide").checked=false; $("topGuides").checked=false; renderStage(); '
                     'window.nativeBeforeColor=$("native").toDataURL(); '
                     'window.layoutBeforeColor=JSON.stringify(state.layout); '
                     '$("saturation").value="0"; $("saturation").oninput()')
            wait('state.colorCache.size > 0')
            assert evaluate('$("native").toDataURL()===window.nativeBeforeColor')
            assert evaluate('JSON.stringify(state.layout)===window.layoutBeforeColor')
            assert evaluate('colorSettings().saturation') == 0
            # Inspect full-coverage versus protected pixels; no alpha can change.
            result = evaluate("""(() => {
              const f=state.manifest.frames[currentStep().frame], [x,y,w,h]=f.atlas_xywh;
              const c=document.createElement('canvas'); c.width=w;c.height=h;
              const ctx=c.getContext('2d',{willReadFrequently:true});
              ctx.drawImage(getImage(state.manifest.pages[f.page].variant_previews[state.palette]),x,y,w,h,0,0,w,h);
              const base=ctx.getImageData(0,0,w,h).data;
              const changed=coloredSprite(getImage(state.manifest.pages[f.page].variant_previews[state.palette]),f)
                .getContext('2d').getImageData(0,0,w,h).data;
              ctx.clearRect(0,0,w,h);ctx.drawImage(getImage(colorMaskPath(f.page)),x,y,w,h,0,0,w,h);
              const mask=ctx.getImageData(0,0,w,h).data;
              let protectedCount=0,changedCount=0,alphaErrors=0,protectedErrors=0;
              for(let i=0;i<base.length;i+=4){
                if(base[i+3]!==changed[i+3])alphaErrors++;
                if(base[i+3]<250)continue;
                const diff=Math.max(...[0,1,2].map(k=>Math.abs(base[i+k]-changed[i+k])));
                if(mask[i]===0){protectedCount++;if(diff>1)protectedErrors++;}
                if(mask[i]>200&&diff>10)changedCount++;
              }
              return {protectedCount,changedCount,alphaErrors,protectedErrors};
            })()""")
            assert result['protectedCount'] > 0 and result['changedCount'] > 0, result
            assert result['alphaErrors'] == result['protectedErrors'] == 0, result
            evaluate('$("brightness").value="115"; $("brightness").oninput(); flushFixups()')
            call('Page.reload')
            time.sleep(.3)
            ready()
            assert evaluate('colorSettings().saturation') == 0
            assert evaluate('colorSettings().brightness') == 1.15
            evaluate('window.colorPalette=state.palette; '
                     '$("palette").value=Object.keys(state.manifest.variants).find(p=>p!==state.palette); '
                     '$("palette").onchange()')
            ready()
            assert evaluate('colorSettings().saturation') == 1
            evaluate('$("palette").value=window.colorPalette; $("palette").onchange()')
            ready()
            assert evaluate('colorSettings().saturation') == 0
            evaluate('$("previewColor").checked=false; $("previewColor").onchange()')
            assert evaluate('colorSettings().enabled') is False
            evaluate('$("resetColor").click(); flushFixups()')
            assert evaluate('colorSettings().saturation===1 && colorSettings().brightness===1')
            print('PASS: color sliders, protected material pixels, exact alpha, native/placement unchanged, '
                  'palette-specific persistence, preview toggle and reset.')
            screenshot = call('Page.captureScreenshot', {'format': 'png'})
            Path('/tmp/mm6-frame-editor.png').write_bytes(base64.b64decode(screenshot['data']))
            print('PASS: 60 families; keyboard and mirrored drag; fixed guides across frames/views/playback; '
                  '400% zoom of both views; guide undo/reset; '
                  'notes/flags; checkpoint reload; playback; all masters; conflict protection. '
                  'Cleric measured scale trial; non-compounding apply; scale undo/reset/toggle; mirrored scale edits. '
                  'Screenshot: /tmp/mm6-frame-editor.png')
        finally:
            if socket:
                socket.close()
            if chrome:
                try:
                    os.killpg(chrome.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                chrome.wait(timeout=10)
            server.terminate()
            server.wait(timeout=10)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--collection', type=Path)
    parser.add_argument('--collection-smoke', action='store_true',
                        help='Check the complete selected collection with temporary offset/size/acceptance edits')
    arguments = parser.parse_args()
    if arguments.collection_smoke and not arguments.collection:
        parser.error('--collection-smoke requires --collection')
    run(arguments.collection, arguments.collection_smoke)
