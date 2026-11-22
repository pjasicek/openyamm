#!/usr/bin/env python3
"""Starts a co-op session of several games on this PC, ready to play: see README.md beside this file."""
import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
BINARY = Path(os.environ.get('OPENYAMM_GAME_BINARY') or REPO / 'build/game/openyamm')
PORT = 27950


def load(name):
    data = json.loads((HERE / name).read_text())
    data.pop('_about', None)
    return data


def parse_args():
    profiles = load('profiles.json')
    parser = argparse.ArgumentParser(description='Start a co-op session of several games on this PC.')
    parser.add_argument('profile', nargs='?', choices=sorted(profiles), help='the session to start')
    parser.add_argument('--list', action='store_true', help='list the sessions and the parties')
    parser.add_argument('--check', action='store_true',
                        help='only prepare the saves (shows a party that does not load); no window')
    parser.add_argument('--hidden', action='store_true',
                        help='minimized windows without sound, for an automatic check (with --seconds)')
    parser.add_argument('--seconds', type=float, default=0,
                        help='close the games after this long (default: when the host\'s window is closed)')
    parser.add_argument('--resolution', help='each window\'s size, e.g. 1280x720 (default: by the number of games)')
    parser.add_argument('--map', help='another map file than the profile\'s')
    parser.add_argument('--port', type=int, default=PORT,
                        help='the UDP port the host listens on (another one beside a session that is already up)')
    parser.add_argument('--capture', type=float, metavar='SECONDS',
                        help='each game saves a screenshot (session.png beside its tour) this long after it is up;'
                             ' allow the later games\' start-up, about 20 seconds each')
    parser.add_argument('--then', action='append', default=[], metavar='PLAYER:LINE',
                        help='a console line a game types six seconds before its screenshot (with --capture), e.g.'
                             ' "1:coop propose out02.odm" for the first guest; "1:!key_down: W" is a tour step as'
                             ' it stands; repeatable')
    return parser.parse_args(), profiles


def prepare_save(out, world, map_file, ruleset, party, index):
    """A new game with the party on the map, saved: the game then starts from that save."""
    folder = out / f'p{index}'
    shutil.rmtree(folder, ignore_errors=True)
    (folder / 'prepared').mkdir(parents=True)
    new_game = {'start_map': map_file, 'party': party}
    if ruleset:
        new_game['ruleset'] = ruleset
    scenario = {'id': f'coop_local_p{index}', 'world': world, 'mode': 'faithful',
                'steps': [{'new_game_flow': new_game}, {'save_game': 'coop_local'}]}
    scenario_path = folder / 'prepare.yml'
    # JSON is a YAML subset: the game's scenario loader reads it.
    scenario_path.write_text(json.dumps(scenario, indent=2) + '\n')
    environment = dict(os.environ, SDL_AUDIODRIVER='dummy', OPENYAMM_SCENARIO_SAVE_DIR=str(folder / 'prepared'))
    command = [str(BINARY), '--world', world, '--user-data', str(folder / 'user_data'),
               '--headless-run-scenario', str(scenario_path), '--scenario-no-color']
    with (folder / 'prepare.log').open('w') as log:
        code = subprocess.run(command, cwd=REPO, env=environment, stdout=log, stderr=subprocess.STDOUT,
                              timeout=300, check=False).returncode
    save = folder / 'prepared/coop_local.oysav'
    if code != 0 or not save.exists():
        lines = [line for line in (folder / 'prepare.log').read_text(errors='replace').splitlines()
                 if 'Scenario failure' in line or 'validation' in line or 'Failed to load' in line]
        raise RuntimeError(f'player {index}: the party did not load.\n  ' + '\n  '.join(lines[-4:])
                           + f'\n  (log: {folder / "prepare.log"})')
    return save


def write_tour(path, lines):
    steps = '\n'.join(f'  - {line}' for line in lines)
    path.write_text(f'output_dir: {path.parent}\nexit: false\nsteps:\n{steps}\n')


def start_game(out, profile_name, world, save, index, tour, args, resolution):
    """One game through tools/run_game.sh; returns its process and the folder its log is in."""
    command = [str(REPO / 'tools/run_game.sh'), '--isolated', f'coop_{profile_name}_p{index}', '--world', world,
               '--save', str(save), '--warmup', '1', '--seconds', '0',
               '--set', f'debug.menu_input_tour_path={tour}', '--set', 'coop.test_commands=true',
               '--set', 'video.window_mode=windowed', '--set', f'video.resolution={resolution}']
    if not args.hidden:
        command.append('--visible')
    environment = dict(os.environ)
    # One game's sound is enough: the host's, unless everything is hidden.
    if args.hidden or index > 0:
        environment['SDL_AUDIODRIVER'] = 'dummy'
    log_path = out / f'p{index}/launcher.log'
    log = log_path.open('w')
    process = subprocess.Popen(command, cwd=REPO, env=environment, stdout=log, stderr=subprocess.STDOUT)
    run_folder = None
    started = time.monotonic()
    while time.monotonic() - started < 240:
        text = log_path.read_text(errors='replace')
        found = re.search(r'^Isolated run: (.+)$', text, re.MULTILINE)
        run_folder = Path(found.group(1)) if found else run_folder
        if 'Run active' in text:
            return process, run_folder
        if process.poll() is not None:
            break
        time.sleep(0.3)
    raise RuntimeError(f'player {index}: the game did not start. See {log_path}'
                       + (f' and {run_folder / "game.log"}' if run_folder else ''))


def game_log(run_folder):
    path = run_folder / 'game.log'
    return path.read_text(errors='replace') if path.exists() else ''


def wait_for(run_folder, text, seconds, what):
    started = time.monotonic()
    while time.monotonic() - started < seconds:
        if text in game_log(run_folder):
            return
        time.sleep(0.3)
    raise RuntimeError(f'{what} (waited {seconds:g} s; see {run_folder / "game.log"})')


def main():
    args, profiles = parse_args()
    parties = load('parties.json')
    if args.list or not args.profile:
        print('Sessions:')
        for name, profile in sorted(profiles.items()):
            rules = profile['ruleset'] or 'standard'
            print(f'  {name}: {profile["world"]} {profile["map"]}, {rules}; ' + ', '.join(profile['players']))
        print('Parties:')
        for name, party in sorted(parties.items()):
            print(f'  {name}: ' + ', '.join(f'{m["name"]} ({m["class"]} {m["level"]})' for m in party['members']))
        return 0
    profile = profiles[args.profile]
    world = profile['world']
    map_file = args.map or profile['map']
    players = profile['players']
    resolution = args.resolution or ('1280x720' if len(players) <= 2 else '960x540')
    out = REPO / 'output/coop_local' / args.profile
    out.mkdir(parents=True, exist_ok=True)
    if not BINARY.exists():
        raise RuntimeError(f'no game at {BINARY}: build it first (cmake --build build --target openyamm -j25)')

    print(f'{args.profile}: preparing {len(players)} games ...', flush=True)
    saves = [prepare_save(out, world, map_file, profile['ruleset'], parties[party], index)
             for index, party in enumerate(players)]
    if args.check:
        print('Every party loaded: ' + ', '.join(players))
        return 0

    processes = []
    try:
        host_tour = out / 'p0/tour.yml'
        # The rules the game runs under go into its log (a solo run says so), then it hosts.
        def capture_steps(index, wait):
            if not args.capture:
                return []
            lines = [line.split(':', 1)[1] for line in args.then if line.split(':', 1)[0] == str(index)]
            # A line that begins with "!" is a tour step as it stands (a key held, a wait), not a console line.
            return [f'wait: {max(1.0, wait - 6.0):g}',
                    *[line[1:] if line.startswith('!') else f'console: {line}' for line in lines], 'wait: 6',
                    'capture: session']

        write_tour(host_tour, ['wait: 1', 'console: ruleset', f'console: coop host {args.port}',
                               *capture_steps(0, args.capture or 0)])
        print('Starting the host ...', flush=True)
        host, host_folder = start_game(out, args.profile, world, saves[0], 0, host_tour, args, resolution)
        processes.append(host)
        wait_for(host_folder, 'hosting on UDP port', 60, 'the host did not start hosting')
        folders = [host_folder]
        for index in range(1, len(players)):
            tour = out / f'p{index}/tour.yml'
            # Joined, then beside the host (the host's test commands are on).
            write_tour(tour, ['wait: 1', f'console: coop join 127.0.0.1:{args.port}', 'wait: 8', 'console: coop sync',
                              *capture_steps(index, max(7.0, (args.capture or 0) - 20.0 * index))])
            print(f'Starting player {index + 1} ...', flush=True)
            process, folder = start_game(out, args.profile, world, saves[index], index, tour, args, resolution)
            processes.append(process)
            folders.append(folder)
            wait_for(folder, 'asked the host to bring this player', 90, f'player {index + 1} did not join')
        print(f'All {len(players)} games are in one session on {map_file}.')
        print('  In any console: coop sync brings that player to the host; in the host\'s, coop sync <player>'
              ' brings everyone to that player.')
        print('  Logs: ' + ', '.join(str(folder / 'game.log') for folder in folders))
        print('  ' + ('Closing in %g seconds.' % args.seconds if args.seconds else
                      'Close the host\'s window to end them all (or press Ctrl+C here).'), flush=True)
        started = time.monotonic()
        while host.poll() is None and (not args.seconds or time.monotonic() - started < args.seconds):
            time.sleep(0.5)
        if args.hidden:
            joined = len(re.findall(r'joined the game', game_log(host_folder)))
            print(f'The host\'s log names {joined} join(s).')
    except KeyboardInterrupt:
        pass
    finally:
        # An interrupt, not a termination: the game's launcher closes its game on the first only.
        for process in processes:
            if process.poll() is None:
                process.send_signal(signal.SIGINT)
        for process in processes:
            try:
                process.wait(timeout=20)
            except subprocess.TimeoutExpired:
                process.kill()
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except RuntimeError as error:
        print(f'coop_local: {error}', file=sys.stderr)
        sys.exit(1)
