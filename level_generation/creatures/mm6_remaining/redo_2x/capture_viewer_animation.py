"""Capture native/restored sequences from the final browser viewer as animated WebP."""

import argparse
import base64
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import time
import urllib.request

from PIL import Image
import websocket


def webp_durations(path):
    data = Path(path).read_bytes()
    assert data[:4] == b'RIFF' and data[8:12] == b'WEBP'
    durations = []
    pos = 12
    while pos + 8 <= len(data):
        kind = data[pos:pos + 4]
        size = int.from_bytes(data[pos + 4:pos + 8], 'little')
        if kind == b'ANMF':
            durations.append(int.from_bytes(data[pos + 20:pos + 23], 'little'))
        pos += 8 + size + (size & 1)
    return durations


def capture(project, action, view, output, palette=None, viewer='placement_review.html'):
    root = Path(project).resolve()
    if not (root / 'manifest.json').exists() or not (root / viewer).exists():
        root /= 'redo_2x'
    manifest_path = root / 'manifest.json'
    viewer_path = root / viewer
    manifest = json.loads(manifest_path.read_text())
    if palette is None:
        palette = next(key for key, value in manifest['variants'].items() if value.get('exact_base_bypass'))
    actions = manifest['animations_by_palette'][palette]
    if action == 'all':
        distinct = {}
        for action_name, animation in actions.items():
            for view_name, steps in animation['views'].items():
                if steps:
                    distinct.setdefault(json.dumps(steps, sort_keys=True), (action_name, int(view_name), steps))
        targets = [(name, direction, steps, Path(output) / f'browser_{name}_{direction}.webp')
                   for name, direction, steps in distinct.values()]
    else:
        sequence = actions[action]['views'][str(view)]
        if not sequence:
            raise ValueError(f'{action}/{view}/{palette} has no images')
        targets = [(action, view, sequence, Path(output))]

    with tempfile.TemporaryDirectory(prefix='mm6-sprite-capture-', dir='/tmp') as work:
        log = open(Path(work) / 'chrome.log', 'w')
        process = subprocess.Popen([
            shutil.which('google-chrome'), '--headless', '--no-sandbox', '--disable-gpu',
            '--disable-dev-shm-usage', '--allow-file-access-from-files', '--disable-background-networking',
            '--no-first-run', '--remote-debugging-port=0', '--remote-allow-origins=*',
            '--user-data-dir=' + work, viewer_path.as_uri() + '?frame=0',
        ], stdout=log, stderr=log, start_new_session=True)
        socket = None
        try:
            port_file = Path(work) / 'DevToolsActivePort'
            deadline = time.monotonic() + 15
            while not port_file.exists():
                if process.poll() is not None or time.monotonic() > deadline:
                    raise RuntimeError((Path(work) / 'chrome.log').read_text()[-3000:])
                time.sleep(.05)
            port = int(port_file.read_text().splitlines()[0])
            browser_targets = json.load(urllib.request.urlopen(f'http://127.0.0.1:{port}/json/list'))
            target = next(item for item in browser_targets if item['type'] == 'page')
            socket = websocket.create_connection(target['webSocketDebuggerUrl'], timeout=120)
            call_id = 0

            def evaluate(expression, wait=False):
                nonlocal call_id
                call_id += 1
                socket.send(json.dumps(dict(id=call_id, method='Runtime.evaluate', params=dict(
                    expression=expression, awaitPromise=wait, returnByValue=True))))
                while True:
                    result = json.loads(socket.recv())
                    if result.get('id') == call_id:
                        assert 'error' not in result, result
                        result = result['result']
                        assert 'exceptionDetails' not in result, result
                        return result['result'].get('value')

            deadline = time.monotonic() + 15
            while not evaluate("typeof manifest !== 'undefined' && typeof seq === 'function'"):
                if time.monotonic() > deadline:
                    page = evaluate('JSON.stringify({url:location.href,state:document.readyState,body:document.body?.innerText?.slice(0,400)})')
                    raise RuntimeError(f'Viewer did not load: {page}; browser log: {(Path(work) / "chrome.log").read_text()[-1200:]}')
                time.sleep(.05)
            assert json.loads(evaluate('JSON.stringify(manifest)')) == manifest, 'Viewer embeds a stale manifest'
            template = '''(async()=>{
                playing=false;
                $('palette').value=PALETTE;
                $('action').value=ACTION;
                $('view').value=VIEW;
                if ($('palette').value!==PALETTE || $('action').value!==ACTION || $('view').value!==VIEW)
                    throw Error('Viewer selection unavailable');
                const steps=seq();
                const paths=[];
                for(const s of steps){
                    paths.push(`native_variants/${s.frame}_${PALETTE}.png`);
                    const f=manifest.frames[s.frame];
                    paths.push(manifest.pages[f.page].variant_previews[PALETTE]);
                }
                await Promise.all([...new Set(paths)].map(p=>img(p).decode()));
                const combined=document.createElement('canvas');combined.width=1400;combined.height=600;
                const ctx=combined.getContext('2d'),output=[];
                for(const s of steps){
                    draw($('native'),s,true);draw($('enhanced'),s,false);
                    ctx.drawImage($('native'),0,0);ctx.drawImage($('enhanced'),700,0);
                    output.push(combined.toDataURL('image/png').split(',')[1]);
                }
                return output;
            })()'''
            captured = []
            manifest_hash = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
            viewer_hash = hashlib.sha256(viewer_path.read_bytes()).hexdigest()
            atlas_paths = {path for page in manifest['pages']
                           for path in [page['base'], page['mask'], page['mask_overlay'],
                                        *page['variant_previews'].values()]}
            atlas_page_hashes = {path: hashlib.sha256((root / path).read_bytes()).hexdigest()
                                 for path in sorted(atlas_paths)}
            for action_name, direction, sequence, destination in targets:
                expression = template.replace('PALETTE', json.dumps(palette)).replace(
                    'ACTION', json.dumps(action_name)).replace('VIEW', json.dumps(str(direction)))
                encoded = evaluate(expression, True)
                assert len(encoded) == len(sequence)
                frames = [Image.open(BytesIO(base64.b64decode(item))).convert('RGBA') for item in encoded]
                durations = [round(step['duration_ms']) for step in sequence]
                assert len(sequence) == 1 or all(duration > 0 for duration in durations), (
                    'A timed sequence has a non-positive frame duration')
                visible_frames = []
                visible_durations = []
                for frame_image, duration in zip(frames, durations):
                    if visible_frames and frame_image.tobytes() == visible_frames[-1].tobytes():
                        visible_durations[-1] += duration
                    else:
                        visible_frames.append(frame_image)
                        visible_durations.append(duration)
                destination.parent.mkdir(parents=True, exist_ok=True)
                frames[0].save(destination, format='WEBP', save_all=True, append_images=frames[1:],
                               duration=durations, loop=0, lossless=True, method=4)
                encoded_durations = webp_durations(destination)
                if encoded_durations == durations:
                    expected_frames = frames
                elif encoded_durations == visible_durations:
                    expected_frames = visible_frames
                elif len(visible_frames) == 1 and not encoded_durations:
                    expected_frames = visible_frames
                else:
                    raise AssertionError('Animated WebP did not preserve visible frame timing')
                saved = Image.open(destination)
                assert saved.n_frames == len(expected_frames), 'Animated WebP changed the visible frame count'
                for index, expected_frame in enumerate(expected_frames):
                    saved.seek(index)
                    assert saved.convert('RGBA').tobytes() == expected_frame.tobytes(), (
                        f'Animated WebP changed visible frame {index}')
                evidence = dict(action=action_name, view=direction, palette=palette,
                                frames=[step['frame'] for step in sequence],
                                native_duration_ms=[step['duration_ms'] for step in sequence],
                                exported_duration_ms=visible_durations,
                                encoded_duration_ms=encoded_durations,
                                collapsed_identical_frames=len(frames) - len(visible_frames),
                                manifest_sha256=manifest_hash,
                                viewer_sha256=viewer_hash,
                                animation_sha256=hashlib.sha256(destination.read_bytes()).hexdigest(),
                                method='Browser canvases from native PNGs and final atlas; WebP rounds native timing to integer milliseconds')
                metadata_path = destination.with_suffix('.json')
                metadata_path.write_text(json.dumps(evidence, indent=2) + '\n')
                captured.append(dict(action=action_name, view=direction, palette=palette,
                                     frames=evidence['frames'], native_duration_ms=evidence['native_duration_ms'],
                                     webp=str(destination), webp_sha256=evidence['animation_sha256'],
                                     metadata=str(metadata_path),
                                     metadata_sha256=hashlib.sha256(metadata_path.read_bytes()).hexdigest()))
            if action == 'all':
                capture_for_sequence = {json.dumps(steps, sort_keys=True): i
                                        for i, (_, _, steps, _) in enumerate(targets)}
                bindings = [dict(action=name, view=int(direction), capture_index=capture_for_sequence[
                    json.dumps(steps, sort_keys=True)])
                    for name, animation in actions.items()
                    for direction, steps in animation['views'].items() if steps]
                index = dict(manifest_sha256=manifest_hash, viewer_sha256=viewer_hash,
                             atlas_pages_sha256=atlas_page_hashes,
                             atlas_binding_method='hashed_during_browser_capture',
                             distinct_sequence_count=len(captured), bindings=bindings,
                             captures=captured, visual_acceptance=False,
                             method='Current browser viewer canvas output; WebP rounds durations to integer milliseconds, while sidecars retain exact native timing')
                index_path = Path(output) / 'browser_capture_index.json'
                index_path.write_text(json.dumps(index, indent=2) + '\n')
                print(json.dumps(dict(index=str(index_path), distinct_sequences=len(captured))))
            else:
                print(json.dumps(dict(output=str(captured[0]['webp']), frames=len(captured[0]['frames']),
                                      duration_ms=sum(durations))))
        finally:
            if socket:
                try:
                    socket.send(json.dumps(dict(id=999999, method='Browser.close')))
                except websocket.WebSocketException:
                    pass
                socket.close()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            log.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('project')
    parser.add_argument('action')
    parser.add_argument('view', type=int)
    parser.add_argument('output')
    parser.add_argument('--palette')
    parser.add_argument('--viewer', default='placement_review.html')
    args = parser.parse_args()
    capture(args.project, args.action, args.view, args.output, args.palette, args.viewer)
