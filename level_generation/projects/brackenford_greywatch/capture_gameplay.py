"""Capture the ordinary game under an existing X display, loading a faithful scenario save.

Run using xvfb-run for an isolated display. Screenshots include the HUD and normal native rendering.
The menu screenshots are retained so incorrect UI navigation cannot masquerade as a gameplay capture.
"""
import argparse
import configparser
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import statistics
import subprocess
import time

import yaml
from Xlib import X, XK, display
from Xlib.ext import xtest

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
parser = argparse.ArgumentParser()
parser.add_argument('name')
parser.add_argument('--map', default='lg01.odm')
parser.add_argument('--world', default='mm8', help='Mounted world identity; MM8 remains the original default')
parser.add_argument('--control-scheme', choices=['classic', 'modern'], help='Explicit controls for reproducible clicks')
parser.add_argument('--pose', nargs=5, type=float, metavar=('X', 'Y', 'Z', 'YAW', 'PITCH'),
                    help='Native world coordinates; yaw and pitch are radians.')
parser.add_argument('--diagnostic-flying', action='store_true',
                    help='Enable debug flight for review actions; not ordinary movement evidence')
parser.add_argument('--stage', type=Path, default=Path('/tmp/openyamm-brackenford-greywatch'))
parser.add_argument('--review-directory', type=Path, help='Store captures outside the authoring project')
parser.add_argument('--binary', type=Path, help='Use a frozen playtest executable')
parser.add_argument('--seconds', type=float, default=12)
parser.add_argument('--warmup', type=float, default=10)
parser.add_argument('--look-left', type=float, default=0, help='Relative mouse look in radians after loading')
parser.add_argument('--look-down', type=float, default=0, help='Relative mouse pitch in radians after loading')
parser.add_argument('--actions', type=Path, help='Explicit UI review actions: key/text/click/wait/screenshot JSON sequence')
parser.add_argument('--start-save', type=Path, help='Continue a real save for transaction/persistence review')
parser.add_argument('--party-file', type=Path, help='Explicit ordinary-party fixture for a controlled skill comparison')
args = parser.parse_args()
assert re.fullmatch(r'[a-z0-9_]+', args.name)
work = Path('/tmp/openyamm-levelgen-captures') / args.name
work.mkdir(parents=True, exist_ok=True)
review = args.review_directory or PROJECT / 'review/gameplay'
review.mkdir(parents=True, exist_ok=True)
settings = configparser.ConfigParser()
settings.read(args.stage / 'settings.ini')
if args.control_scheme:
    if not settings.has_section('controls'):
        settings.add_section('controls')
    settings['controls']['control_scheme'] = args.control_scheme
settings['startup'] = {'start_in_main_menu': 'true'}
if not settings.has_section('video'):
    settings.add_section('video')
settings['video'].update({'resolution': '1600x1200', 'vsync': 'false', 'fullscreen': 'false'})
settings['logging'] = {'fps_trace': 'true', 'performance_trace': 'true'}
with (work / 'settings.ini').open('w') as stream:
    settings.write(stream, space_around_delimiters=False)
party = json.loads((args.party_file or PROJECT / 'source/baseline_party.json').read_text())
steps = [{'new_game_flow': {'start_map': args.map, 'party': party}}]
if args.start_save:
    steps = [{'load_game': {'path': str(args.start_save.resolve(strict=True))}}]
if args.pose:
    steps.append({'set_pose': dict(map=args.map, **dict(zip(['x', 'y', 'z', 'yaw', 'pitch'], args.pose)))})
steps.append({'save_game': 'view'})
scenario_id = 'levelgen_capture_' + args.name
scenario = dict(id=scenario_id, world=args.world, mode='faithful', steps=steps)
source = work / 'prepare.yml'
source.write_text(yaml.safe_dump(scenario, sort_keys=False))
binary = (args.binary or ROOT / 'build/game/openyamm').resolve()
with (work / 'prepare.log').open('w') as stream:
    subprocess.run([str(binary), '--world', args.world, '--headless-run-scenario', str(source),
                    '--scenario-no-color'], cwd=work, stdout=stream, stderr=subprocess.STDOUT, check=True)
if args.diagnostic_flying:
    # Faithful scenario preparation clears debug overrides. Apply only to this isolated visual review afterwards.
    settings.read(work / 'settings.ini')
    if not settings.has_section('debug'):
        settings.add_section('debug')
    settings['debug']['start_flying'] = 'true'
    with (work / 'settings.ini').open('w') as stream:
        settings.write(stream, space_around_delimiters=False)
saves = work / 'saves'
saves.mkdir(exist_ok=True)
shutil.copy2(Path('/tmp/openyamm_scenario_saves') / scenario_id / 'view.oysav', saves / 'view.oysav')
connection = display.Display()


def screenshot(suffix):
    subprocess.run(['import', '-window', 'root', str(review / (args.name + suffix + '.png'))], check=True)


def capture_burst(options):
    """Sample the authorized 24-bit Xvfb display before spending time encoding PNGs."""
    from PIL import Image

    count = int(options['count'])
    interval = float(options['interval'])
    assert 2 <= count <= 120 and 0.01 <= interval <= 1 and count * interval <= 20
    prefix = options['prefix']
    assert re.fullmatch(r'[a-zA-Z0-9_-]+', prefix)
    screen = connection.screen()
    geometry = screen.root.get_geometry()
    assert screen.root_depth == 24 and connection.display.info.image_byte_order == X.LSBFirst
    frames, times = [], []
    started = time.monotonic()
    for index in range(count):
        time.sleep(max(0, started + index * interval - time.monotonic()))
        frame = screen.root.get_image(0, 0, geometry.width, geometry.height, X.ZPixmap, 0xffffffff)
        assert len(frame.data) == geometry.width * geometry.height * 4
        frames.append(frame.data)
        times.append(time.monotonic() - started)
    paths = []
    for index, data in enumerate(frames):
        name = f'{args.name}_{prefix}_{index:03}.png'
        Image.frombytes('RGB', (geometry.width, geometry.height), data, 'raw', 'BGRX').save(review / name)
        paths.append(name)
    (review / f'{args.name}_{prefix}_frames.json').write_text(json.dumps({
        'screenshots': paths, 'captureElapsedSeconds': times,
        'requestedIntervalSeconds': interval, 'resolution': [geometry.width, geometry.height],
        'method': 'X11 root image reads; PNG encoding happens after the burst',
    }, indent=2) + '\n')


def key(name):
    code = connection.keysym_to_keycode(XK.string_to_keysym(name))
    xtest.fake_input(connection, X.KeyPress, code)
    connection.sync()
    time.sleep(0.12)
    xtest.fake_input(connection, X.KeyRelease, code)
    connection.sync()


def click(x, y):
    xtest.fake_input(connection, X.MotionNotify, x=x, y=y)
    xtest.fake_input(connection, X.ButtonPress, 1)
    connection.sync()
    time.sleep(0.12)
    xtest.fake_input(connection, X.ButtonRelease, 1)
    connection.sync()


def run_actions(actions):
    for action in actions:
        assert len(action) == 1
        if 'key' in action:
            key(action['key'])
        elif 'text' in action:
            # Console input, including shifted ASCII such as the underscore in setting names.
            shift = connection.keysym_to_keycode(XK.string_to_keysym('Shift_L'))
            for character in action['text']:
                assert 32 <= ord(character) < 127, 'Text actions support printable ASCII only'
                symbol = ord(character)
                code = connection.keysym_to_keycode(symbol)
                shifted = connection.keycode_to_keysym(code, 0) != symbol
                assert code and (not shifted or connection.keycode_to_keysym(code, 1) == symbol)
                if shifted:
                    xtest.fake_input(connection, X.KeyPress, shift)
                xtest.fake_input(connection, X.KeyPress, code)
                connection.sync()
                time.sleep(0.06)
                xtest.fake_input(connection, X.KeyRelease, code)
                if shifted:
                    xtest.fake_input(connection, X.KeyRelease, shift)
                connection.sync()
                time.sleep(0.06)
        elif 'hold' in action:
            hold=action['hold']
            duration=float(hold['seconds'])
            assert 0 < duration <= 20
            code=connection.keysym_to_keycode(XK.string_to_keysym(hold['key']))
            assert code
            xtest.fake_input(connection,X.KeyPress,code)
            connection.sync()
            try:
                time.sleep(duration)
            finally:
                xtest.fake_input(connection,X.KeyRelease,code)
                connection.sync()
        elif 'click' in action:
            click(*action['click'])
        elif 'button' in action:
            # Emit a button at the existing pointer. This does not guarantee a
            # world click: UI hit-testing may consume it at the last menu position.
            button = int(action['button'])
            assert 1 <= button <= 3
            xtest.fake_input(connection, X.ButtonPress, button)
            connection.sync()
            time.sleep(0.12)
            xtest.fake_input(connection, X.ButtonRelease, button)
            connection.sync()
        elif 'wait' in action:
            time.sleep(action['wait'])
        elif 'screenshot' in action:
            screenshot('_' + action['screenshot'])
        elif 'burst' in action:
            capture_burst(action['burst'])
        elif 'actions_file' in action:
            path = Path(action['actions_file'])
            deadline = time.monotonic() + 120
            while not path.exists():
                assert time.monotonic() < deadline, 'Review follow-up actions did not arrive'
                time.sleep(0.25)
            run_actions(json.loads(path.read_text()))
        else:
            raise ValueError('Unknown UI review action: ' + str(action))


log_path = review / (args.name + '.log')
with log_path.open('w') as stream:
    process = subprocess.Popen(['stdbuf', '-oL', '-eL', str(binary), '--world', args.world], cwd=work,
                               stdout=stream, stderr=subprocess.STDOUT)
    try:
        time.sleep(8)
        assert process.poll() is None, 'Game exited; inspect capture log'
        windows = [window for window in connection.screen().root.query_tree().children
                   if window.get_wm_name() and 'OpenYAMM' in window.get_wm_name()]
        assert len(windows) == 1, 'Expected one OpenYAMM window on this isolated display'
        windows[0].set_input_focus(X.RevertToParent, X.CurrentTime)
        connection.sync()
        screenshot('_menu')
        click(1415, 443)
        time.sleep(2)
        screenshot('_load')
        click(1000, 1005)
        deadline = time.monotonic() + 45
        while not re.search(r'gameplay_world_frames=[1-9]', log_path.read_text(errors='replace')):
            assert process.poll() is None and time.monotonic() < deadline, 'Game did not finish loading'
            time.sleep(0.25)
        time.sleep(args.warmup)
        if args.look_left or args.look_down:
            xtest.fake_input(connection, X.MotionNotify, detail=1,
                             x=round(-args.look_left / 0.0045), y=round(args.look_down / 0.0045))
            connection.sync()
            time.sleep(0.3)
        if args.actions:
            run_actions(json.loads(args.actions.read_text()))
        screenshot('_warm')
        stream.flush()
        start_offset = log_path.stat().st_size
        time.sleep(args.seconds)
        end_offset = log_path.stat().st_size
        screenshot('')
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
connection.close()
log_text = log_path.read_bytes()[start_offset:end_offset].decode(errors='replace')
if args.seconds > 0:
    assert re.search(r'gameplay_world_frames=[1-9]', log_text), 'No gameplay frames captured; inspect UI screenshots'
samples = [float(value) for value in re.findall(r'Average FPS \(last second\): ([0-9.]+)',
                                                log_text)]
report = dict(name=args.name, world=args.world, map=args.map, pose=args.pose, screenshot=args.name + '.png',
              look_left=args.look_left,
              look_down=args.look_down,
              diagnostic_flying=args.diagnostic_flying,
              warmup_seconds=args.warmup,
              actions=str(args.actions) if args.actions else None,
              party_file=str(args.party_file or PROJECT / 'source/baseline_party.json'),
              performance_sample=args.seconds > 0,
              display=os.environ.get('DISPLAY'), resolution=[1600, 1200], vsync=False,
              measurement_seconds=args.seconds, fps_samples=samples,
              median_fps=statistics.median(samples) if samples else None,
              binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
              settings_sha256=hashlib.sha256((work / 'settings.ini').read_bytes()).hexdigest(),
              native_sha256=hashlib.sha256((Path(settings['assets']['root']) / 'worlds' / args.world / 'maps' / args.map)
                                           .read_bytes()).hexdigest(),
              limitations='Fixed viewpoint, active ordinary party/actors; software display performance is not driver GPU FPS; '
                          'UI and rendered state must be visually checked before accepting samples.')
(review / (args.name + '.json')).write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
