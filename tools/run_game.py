"""Prepare and supervise isolated desktop runs of an OpenYAMM development executable."""
import argparse
import configparser
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import statistics
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]


def finite_number(value):
    number = float(value)
    if not math.isfinite(number):
        raise argparse.ArgumentTypeError('must be finite')
    return number


def print_fps_lines(log_path, offset):
    """Print FPS samples from complete log lines after offset; returns the offset after the last complete line."""
    with log_path.open('rb') as reader:
        reader.seek(offset)
        chunk = reader.read()
    end = chunk.rfind(b'\n') + 1
    for value in re.findall(r'Average FPS \(last second\): ([0-9.]+)', chunk[:end].decode(errors='replace')):
        print(f'FPS {value}', flush=True)
    return offset + end


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('name', help='Short label; every invocation creates a fresh temporary directory')
    parser.add_argument('--world', required=True, help='World id, e.g. mm6')
    parser.add_argument('--map', help='Map filename, e.g. oute3.odm; optional when retaining a save\'s map')
    parser.add_argument('--save', type=Path, help='Read an existing save through a private copy')
    parser.add_argument('--menu', action='store_true', help='Start at the main menu with isolated settings and saves')
    parser.add_argument('--ruleset', metavar='ID[:OPTION...]',
                        help='Rules of the new game, e.g. maw or maw:hell:horizontal (not with --save or --menu)')
    parser.add_argument('--position', nargs=3, type=finite_number, metavar=('X', 'Y', 'Z'))
    parser.add_argument('--yaw-radians', type=finite_number)
    parser.add_argument('--pitch-degrees', type=finite_number)
    parser.add_argument('--settings', type=Path, default=ROOT / 'settings.ini', help='Settings to copy')
    parser.add_argument('--binary', type=Path,
                        default=Path(os.environ.get('OPENYAMM_GAME_BINARY') or ROOT / 'build/game/openyamm'),
                        help='Executable to test (default $OPENYAMM_GAME_BINARY, else build/game/openyamm)')
    parser.add_argument('--assets', type=Path, help='Asset root override (otherwise resolved from copied settings)')
    parser.add_argument('--extra-mount', type=Path,
                        help='A development folder read in front of the asset root (the game\'s --extra-mount), such as '
                             'the Map Studio\'s mount of builds')
    parser.add_argument('--set', action='append', default=[], metavar='SECTION.KEY=VALUE', help='Repeatable override')
    parser.add_argument('--seconds', type=finite_number, default=15, help='Run after warmup; 0 waits until closed')
    parser.add_argument('--warmup', type=finite_number, default=3, help='Seconds after startup save is loaded')
    parser.add_argument('--prepare-only', action='store_true', help='Prepare private settings/save without a GUI launch')
    parser.add_argument('--visible', action='store_true',
                        help='Show the window; runs start minimized otherwise, which does not give representative FPS')
    parser.add_argument('--show-fps', action='store_true', help='Print the per-second FPS to the terminal during the run')
    args = parser.parse_args()
    if not re.fullmatch(r'[a-zA-Z0-9_-]{1,60}', args.name):
        parser.error('name must contain 1-60 letters, digits, underscores or hyphens')
    if not args.map and not args.save and not args.menu:
        parser.error('provide --map, --save or --menu')
    camera = [args.position is not None, args.yaw_radians is not None, args.pitch_degrees is not None]
    if any(camera) and not all(camera):
        parser.error('provide --position, --yaw-radians and --pitch-degrees together')
    if args.pitch_degrees is not None and not -89 <= args.pitch_degrees <= 89:
        parser.error('pitch must be between -89 and 89 degrees')
    if args.ruleset and (args.save or args.menu):
        parser.error('--ruleset starts a new game; it cannot be combined with --save or --menu')
    if args.seconds < 0 or args.warmup < 0:
        parser.error('seconds and warmup must be nonnegative')
    return args


def extra_mount_arguments(args):
    return ['--extra-mount', str(args.extra_mount.resolve(strict=True))] if args.extra_mount else []


def write_settings(path, settings):
    with path.open('w') as stream:
        settings.write(stream, space_around_delimiters=False)


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def stop_game(process):
    if process.poll() is None:
        process.terminate()  # SDL handles SIGTERM as a quit request, permitting normal shutdown.
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def prepare(args, run, binary, metadata):
    source = args.settings.resolve(strict=True)
    settings = configparser.ConfigParser(interpolation=None)
    with source.open() as stream:
        settings.read_file(stream)
    for section in ('assets', 'startup', 'debug', 'video', 'logging'):
        if not settings.has_section(section):
            settings.add_section(section)
    for override in args.set:
        key, separator, value = override.partition('=')
        section, dot, option = key.partition('.')
        if not separator or not dot or not section or not option or '\n' in override or '\r' in override:
            raise ValueError('expected SECTION.KEY=VALUE: ' + override)
        if not settings.has_section(section):
            settings.add_section(section)
        settings[section][option] = value
    asset_path = args.assets or Path(settings['assets'].get('root') or 'assets_dev')
    if not asset_path.is_absolute():
        asset_path = (Path.cwd() if args.assets else source.parent) / asset_path
    settings['assets']['root'] = str(asset_path.resolve(strict=True))
    # Pins typed in an isolated run (`pin <text>`) go to the inbox of the settings they came from, not the run folder.
    pin_inbox = Path(settings['debug'].get('pin_inbox_path') or 'pins_inbox')
    if not pin_inbox.is_absolute():
        pin_inbox = source.parent / pin_inbox
    settings['debug']['pin_inbox_path'] = str(pin_inbox)
    # Owned paths/startup controls cannot be redirected by inherited settings or --set.
    settings['startup'].update(start_in_main_menu='true' if args.menu else 'false', save_file='')
    settings['debug'].update(start_world=args.world, start_map_file=args.map or '', override_start_position='false')
    settings['logging'].update(fps_trace='true', performance_trace='true',
                               gameplay_trace_file='logs/gameplay_trace.log', combat_trace_file='logs/combat_trace.log')
    write_settings(run / 'settings.ini', settings)
    if args.menu and not args.map and not args.save:
        shutil.copy2(run / 'settings.ini', run / 'launch-settings.ini')
        metadata.update(settings_sha256=digest(run / 'launch-settings.ini'),
                        assets=settings['assets']['root'], display=os.environ.get('DISPLAY'),
                        command=[str(binary), '--world', args.world, *extra_mount_arguments(args)])
        return dict(os.environ, TMPDIR=str(run / 'tmp'))
    steps = []
    if args.save:
        source_save = args.save.resolve(strict=True)
        private_save = run / 'saves/source.oysav'
        shutil.copy2(source_save, private_save)
        metadata['source_save_sha256'] = digest(private_save)
        steps.append({'load_game': {'path': str(private_save)}})
        if args.map and not args.position:
            steps.append({'load_map': {'map': args.map}})
    else:
        new_game = {'start_map': args.map}
        if args.ruleset:
            new_game['ruleset'] = args.ruleset
        steps.append({'new_game_flow': new_game})
    if args.position:
        pose = dict(zip(('x', 'y', 'z'), args.position))
        pose.update(yaw=args.yaw_radians, pitch=math.radians(args.pitch_degrees))
        if args.map:
            pose['map'] = args.map
        steps.append({'set_pose': pose})
    # An autosave name: maps that forbid saving (an arena's allow_save_game: false) still accept the game's autosave.
    steps.append({'save_game': 'autosave'})
    scenario = {'id': 'desktop_launch', 'world': args.world, 'mode': 'faithful', 'steps': steps}
    # JSON is a YAML subset; use the existing scenario loader without a Python YAML dependency.
    scenario_path = run / 'prepare.yml'
    scenario_path.write_text(json.dumps(scenario, indent=2) + '\n')
    environment = dict(os.environ, TMPDIR=str(run / 'tmp'), OPENYAMM_SCENARIO_SAVE_DIR=str(run / 'prepared'))
    for trace in ('GAMEPLAY', 'PROJECTILE'):
        variable = f'OPENYAMM_{trace}_TRACE_FILE'
        if environment.get(variable):
            environment[variable] = str(run / 'logs' / f'{trace.lower()}_environment_trace.log')
    command = [str(binary), '--world', args.world, *extra_mount_arguments(args), '--headless-run-scenario',
               str(scenario_path), '--scenario-no-color']
    if args.save and not args.map and not args.position:
        # A plain save replay needs the exact saved state, without a scenario round trip.
        prepared = private_save
        (run / 'prepare.log').write_text('Using an unchanged private copy of the source save.\n')
    else:
        with (run / 'prepare.log').open('w') as log:
            process = subprocess.Popen(command, cwd=run, env=environment, stdout=log, stderr=subprocess.STDOUT)
            try:
                if process.wait(timeout=180) != 0:
                    raise RuntimeError('Scenario preparation failed; inspect prepare.log')
            finally:
                stop_game(process)
        prepared = run / 'prepared/autosave.oysav'
    startup_save = run / 'saves/startup.oysav'
    shutil.copy2(prepared, startup_save)
    # Faithful scenarios can rewrite debug settings: restore the requested rendering/settings snapshot afterwards.
    settings['startup']['save_file'] = '' if args.menu else str(startup_save)
    write_settings(run / 'settings.ini', settings)
    shutil.copy2(run / 'settings.ini', run / 'launch-settings.ini')
    metadata.update(settings_sha256=digest(run / 'launch-settings.ini'), save_sha256=digest(startup_save),
                    assets=settings['assets']['root'], display=os.environ.get('DISPLAY'),
                    command=[str(binary), '--world', args.world, *extra_mount_arguments(args)])
    return environment


def run_game(args, run, binary, environment, metadata):
    if shutil.which('glxinfo'):
        with (run / 'renderer-info.txt').open('w') as renderer_log:
            subprocess.run(['glxinfo', '-B'], env=environment, stdout=renderer_log,
                           stderr=subprocess.STDOUT, timeout=15, check=False)
    # Line buffering makes the startup marker and per-second FPS available while the game runs.
    command = ['stdbuf', '-oL', '-eL', str(binary), '--world', args.world, *extra_mount_arguments(args)]
    # A minimized window keeps rendering (screenshots, logs, timed exit) without covering the desktop.
    environment = dict(environment, OPENYAMM_START_MINIMIZED='0' if args.visible else '1')
    metadata['window'] = 'visible' if args.visible else 'minimized'
    log_path = run / 'game.log'
    with log_path.open('w') as log:
        process = subprocess.Popen(command, cwd=run, env=environment, stdout=log, stderr=subprocess.STDOUT)
        metadata['pid'] = process.pid
        metadata['status'] = 'running'
        (run / 'run.json').write_text(json.dumps(metadata, indent=2) + '\n')
        started = time.monotonic()
        try:
            with log_path.open() as reader:
                while True:
                    line = reader.readline()
                    if line.startswith('Startup camera: '):
                        metadata['loaded_camera'] = {
                            key: float(value) for key, value in (field.split('=') for field in line.split()[2:])}
                    if args.menu and line.startswith('Development assets: '):
                        break
                    if line.startswith('Startup save ready: map='):
                        metadata['loaded_map'] = line.strip().split('map=', 1)[1]
                        if args.map and metadata['loaded_map'].lower() != args.map.lower():
                            raise RuntimeError('Loaded map does not match the requested map')
                        break
                    if process.poll() is not None:
                        raise RuntimeError('Game exited before loading the startup save; inspect game.log')
                    if time.monotonic() - started > 180:
                        raise RuntimeError('Startup timed out; inspect game.log')
                    if not line:
                        time.sleep(0.1)
            metadata['startup_seconds'] = time.monotonic() - started
            print('Scene loaded; warming up.', flush=True)
            warmup_end = time.monotonic() + args.warmup
            while time.monotonic() < warmup_end:
                if process.poll() is not None:
                    raise RuntimeError('Game closed during warmup')
                time.sleep(0.1)
            offset = log_path.stat().st_size
            measured = time.monotonic()
            print('Run active; ' + ('close the window to finish.' if args.seconds == 0
                                   else f'automatic exit in {args.seconds:g} seconds.'), flush=True)
            fps_offset = offset
            while process.poll() is None and (args.seconds == 0 or time.monotonic() - measured < args.seconds):
                time.sleep(0.1)
                if args.show_fps:
                    fps_offset = print_fps_lines(log_path, fps_offset)
            metadata['measurement_seconds'] = time.monotonic() - measured
            with log_path.open('rb') as reader:
                reader.seek(offset)
                sample = reader.read().decode(errors='replace')
            (run / 'measurement.log').write_text(sample)
            fps = [float(value) for value in re.findall(r'Average FPS \(last second\): ([0-9.]+)', sample)]
            metadata.update(fps_samples=fps, median_fps=statistics.median(fps) if fps else None)
        finally:
            stop_game(process)
            metadata['exit_code'] = process.returncode
        if process.returncode != 0:
            raise RuntimeError(f'Game exited with code {process.returncode}; inspect game.log')


def main():
    args = parse_args()
    binary = args.binary.resolve(strict=True)
    run = Path(tempfile.mkdtemp(prefix=f'openyamm-desktop-{args.name}-'))
    for name in ('saves', 'logs', 'tmp'):
        (run / name).mkdir()
    metadata = {'request': {key: str(value) if isinstance(value, Path) else value for key, value in vars(args).items()},
                'run_directory': str(run), 'status': 'preparing',
                'timing_note': 'FPS log samples include ordinary simulation/rendering; these are not GPU timer results. '
                               'Only visible-window runs give representative FPS.'}
    print(f'Isolated run: {run}', flush=True)
    try:
        metadata['binary_sha256'] = digest(binary)
        environment = prepare(args, run, binary, metadata)
        metadata['status'] = 'prepared'
        if not args.prepare_only:
            run_game(args, run, binary, environment, metadata)
            metadata['status'] = 'completed'
    except (Exception, KeyboardInterrupt) as error:
        metadata.update(status='failed', error=str(error) or 'Interrupted')
        print(f'Run failed: {metadata["error"]}', flush=True)
        return 1
    finally:
        (run / 'run.json').write_text(json.dumps(metadata, indent=2) + '\n')
        print(f'Run record: {run / "run.json"}', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
