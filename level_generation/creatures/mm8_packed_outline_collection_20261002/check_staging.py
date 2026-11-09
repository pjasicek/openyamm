"""Smoke-check the existing browser editor against MM8 using temporary review state."""
from pathlib import Path
import base64
import json
import select
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request

import websocket

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SERVER = REPO / 'level_generation/creatures/mm6_remaining/acceptance_viewer/serve.py'
COLLECTION = HERE / 'collection.json'


def http_json(url):
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.load(response)


def main():
    expected = json.loads(COLLECTION.read_text())
    checks = []
    with tempfile.TemporaryDirectory(prefix='openyamm-mm8-viewer-check-') as directory:
        temporary = Path(directory)
        server = subprocess.Popen([sys.executable, '-B', str(SERVER), '--collection', str(COLLECTION),
            '--state-dir', str(temporary / 'state'), '--port', '0'],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        chrome = connection = None
        try:
            deadline = time.monotonic() + 90
            while time.monotonic() < deadline:
                if not select.select([server.stdout], [], [], 1)[0]:
                    continue
                line = server.stdout.readline()
                if line.startswith('Open http:'):
                    url = line.split()[1]
                    break
                if server.poll() is not None:
                    raise RuntimeError(line + server.stdout.read())
            else:
                raise RuntimeError('Temporary viewer startup timed out')
            queue = http_json(url + 'api/families')
            assert len(queue['families']) == 61 and not queue['excluded']
            assert queue['collection']['id'] == expected['collection_id']
            assert all(f['decision'] is None and f['fixups_revision'] == 0 for f in queue['families'])
            assert {f['id']: f['artifact_sha256'] for f in queue['families']} == {
                f['creature'].replace(':', '_'): f['artifact_sha256'] for f in expected['families']}
            log = (temporary / 'chrome.log').open('w')
            chrome = subprocess.Popen([shutil.which('google-chrome'), '--headless=new', '--no-sandbox',
                '--disable-gpu', '--disable-dev-shm-usage', '--remote-debugging-port=0',
                '--remote-allow-origins=*', '--window-size=1800,1200',
                '--user-data-dir=' + str(temporary / 'profile'), url], stdout=log, stderr=log)
            port_file = temporary / 'profile/DevToolsActivePort'
            deadline = time.monotonic() + 30
            while not port_file.exists():
                if chrome.poll() is not None or time.monotonic() > deadline:
                    raise RuntimeError((temporary / 'chrome.log').read_text()[-2000:])
                time.sleep(.1)
            port = int(port_file.read_text().splitlines()[0])
            page = next(p for p in http_json(f'http://127.0.0.1:{port}/json/list') if p['type'] == 'page')
            connection = websocket.create_connection(page['webSocketDebuggerUrl'], timeout=30)
            call_id = 0

            def call(method, parameters=None):
                nonlocal call_id
                call_id += 1
                connection.send(json.dumps({'id': call_id, 'method': method, 'params': parameters or {}}))
                while True:
                    answer = json.loads(connection.recv())
                    if answer.get('id') == call_id:
                        assert 'error' not in answer, answer
                        return answer['result']

            def evaluate(expression):
                result = call('Runtime.evaluate', {'expression': expression,
                    'awaitPromise': True, 'returnByValue': True})
                assert 'exceptionDetails' not in result, result
                return result['result'].get('value')

            def wait(expression):
                deadline = time.monotonic() + 30
                while not evaluate(expression):
                    if time.monotonic() > deadline:
                        raise AssertionError('Timed out: ' + expression)
                    time.sleep(.1)

            def ready():
                wait('typeof state!=="undefined" && !!state.manifest && !state.switching && !$("play").disabled')
                wait('state.images.size>=2 && Array.from(state.images.values()).every(i=>i.complete&&i.naturalWidth>0)')

            ready()
            assert evaluate('document.title') == expected['title']
            for stem in ['m400', 'm504', 'm508', 'm624', 'm636', 'm656']:
                identifier = 'mm8_' + stem
                evaluate('showFamily(state.families.findIndex(f=>f.id===' + json.dumps(identifier) + '))')
                ready()
                assert evaluate('currentFamily().id') == identifier
                assert evaluate('$("masterFrame").options.length===Object.keys(state.manifest.frames).length')
                palettes = evaluate('Object.keys(state.manifest.variants)')
                for palette in palettes:
                    evaluate('$("palette").value=' + json.dumps(palette) +
                             '; $("palette").dispatchEvent(new Event("change"))')
                    ready()
                checks.append({'family': identifier, 'palettes_loaded': palettes,
                               'frames': evaluate('Object.keys(state.manifest.frames).length')})
                print(identifier, 'browser loaded', len(palettes), 'palettes', flush=True)
            evaluate('showFamily(state.families.findIndex(f=>f.id==="mm8_m400"))')
            ready()
            evaluate('$("action").value="walk"; $("action").dispatchEvent(new Event("change")); '
                     '$("view").value="5"; $("view").dispatchEvent(new Event("change"))')
            ready()
            assert evaluate('currentStep().mirrored') is True
            evaluate('window.startFrame=state.frameIndex; $("play").click()')
            wait('state.playing && state.frameIndex!==window.startFrame')
            evaluate('$("play").click()')
            evaluate('showFamily(state.families.findIndex(f=>f.id==="mm8_m504"))')
            ready()
            family = evaluate('currentFamily()')
            frame = evaluate('currentStep().frame')
            evaluate('$("centerGuide").checked=false; renderStage(); '
                     'window.nativeBefore=$("native").toDataURL(); $("restored").focus()')
            call('Input.dispatchKeyEvent', {'type': 'keyDown', 'key': 'ArrowRight', 'code': 'ArrowRight'})
            call('Input.dispatchKeyEvent', {'type': 'keyUp', 'key': 'ArrowRight', 'code': 'ArrowRight'})
            evaluate('changeScale(1.03); flushFixups()')
            assert evaluate('frameFixup(currentStep().frame).offset_px') == [1, 0]
            assert evaluate('$("native").toDataURL()===window.nativeBefore')
            evaluate('saveDecision("accepted",false)')
            data = json.loads((temporary / 'state/decisions.json').read_text())
            decision = data['decisions'][family['id']][family['artifact_sha256']]
            assert decision['fixups_snapshot'][frame]['offset_px'] == [1, 0]
            assert decision['fixups_snapshot'][frame]['scale_factor'] == 1.03
            call('Page.reload')
            ready()
            evaluate('showFamily(state.families.findIndex(f=>f.id==="mm8_m504"))')
            ready()
            assert evaluate('frameFixup(' + json.dumps(frame) + ').offset_px') == [1, 0]
            assert evaluate('frameFixup(' + json.dumps(frame) + ').scale_factor') == 1.03
            assert evaluate('currentFamily().decision.decision') == 'accepted'
            evaluate('showFamily(state.families.findIndex(f=>f.id==="mm8_m636"))')
            ready()
            screenshot = call('Page.captureScreenshot', {'format': 'png', 'captureBeyondViewport': False})
            (HERE / 'browser_smoke.png').write_bytes(base64.b64decode(screenshot['data']))
            mm6 = http_json('http://127.0.0.1:8767/api/families')
            before = json.loads((HERE / 'mm6_server_snapshot_before.json').read_text())
            assert mm6['collection'] == before['collection']
            assert {f['id']: f['artifact_sha256'] for f in mm6['families']} == before['artifacts']
            result = {'status': 'passed', 'families': 61, 'frames': expected['frame_count'],
                      'browser_families': checks, 'native_mirrored_view_checked': True,
                      'native_duration_playback_advances': True,
                      'offset_size_and_acceptance_persist_after_reload': True,
                      'original_reference_unchanged_by_edits': True,
                      'test_state': 'Temporary directory removed after check; no user review edits saved',
                      'mm6_server_artifacts_unchanged': True, 'screenshot': 'browser_smoke.png'}
            (HERE / 'browser_check.json').write_text(json.dumps(result, indent=2) + '\n')
            print('PASS: MM8 browser, mirrored playback, palettes, isolated edits, persistence; MM6 untouched', flush=True)
        finally:
            if connection:
                connection.close()
            if chrome:
                chrome.terminate()
                chrome.wait(timeout=15)
            server.terminate()
            server.wait(timeout=15)


if __name__ == '__main__':
    main()
