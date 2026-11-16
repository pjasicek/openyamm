// Play here (S5_BROWSER_EDITOR.md 2.10, 3.6; D13): the host builds the project, installs it into its mount of builds,
// makes an outdoor map's terrain material file, and starts the game at the browser's camera through
// tools/run_game.sh --isolated, with two launch directives of the game: debug.startup_console_file (a file of one
// `tp x y z yaw pitch` line, run once the map has loaded) and debug.exit_pose_path (where the party stood when the
// game closed, which the browser's camera then follows: the game_exited notice). The game starts minimised unless
// the person asked to see it (`visible`; tools/RUN_GAME.md).
import { spawn } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';

// The console file's line: the party's feet and facing in the units `loc` prints.
export function startConsoleText(pose, commands = []) {
  const [x, y, z] = pose.position;
  const number = (value, decimals) => Number(value.toFixed(decimals)).toString();
  return '# The Map Studio\'s Play here: the party at the browser\'s camera (tp x y z yaw-radians pitch-degrees).\n'
    + `tp ${number(x, 3)} ${number(y, 3)} ${number(z, 3)} ${number(pose.yaw_radians, 4)} ${number(pose.pitch_degrees, 3)}\n`
    + commands.map((line) => `${line}\n`).join('');
}

// The game's exit pose file (game/debug/ExitPose.cpp, format 1): {world, map, pose} or null.
export function parseExitPose(text) {
  const scalar = (name) => {
    const match = new RegExp(`^${name}: "?([^"\\n]*)"?$`, 'm').exec(text);
    return match ? match[1] : null;
  };
  const nested = (name) => {
    const match = new RegExp(`^  ${name}: (.+)$`, 'm').exec(text);
    return match ? match[1].trim() : null;
  };
  if (scalar('format') !== '1') return null;
  const position = /^ {2}position: \[([^\]]*)\]$/m.exec(text)?.[1].split(',').map((part) => Number(part.trim()));
  const yaw = Number(nested('yaw_radians'));
  const pitch = Number(nested('pitch_degrees'));
  const heading = Number(nested('heading_yaw_units'));
  if (!position || position.length !== 3 || position.some((value) => !Number.isFinite(value))
    || !Number.isFinite(yaw) || !Number.isFinite(pitch)) {
    return null;
  }
  return { world: scalar('world') ?? '', map: scalar('map') ?? '',
    pose: { position, yaw_radians: yaw, pitch_degrees: pitch, heading_yaw_units: Number.isFinite(heading) ? heading : 0 } };
}

const failed = (kind, message, code = -32000) => ({ error: { code, message, data: { kind } } });

// One Play here: answers as soon as the game is started ({result: {run, map, world}}); `onExit(run, exitPose)` is
// called when it closes. context: {core, repo, assets, mount, runs (folder of the runs' files), runGame (the
// launcher, tools/run_game.sh), env, log}.
export async function playHere({ folder, world, pose, visible, commands = [], seconds }, context) {
  const { core, repo, assets, mount, runs, runGame, log = () => undefined } = context;
  if (!Array.isArray(pose?.position) || pose.position.length !== 3 || !pose.position.every(Number.isFinite)
    || !Number.isFinite(pose.yaw_radians) || !Number.isFinite(pose.pitch_degrees)) {
    return failed('invalid_params', 'game.play_here takes a pose: position [x, y, z], yaw_radians, pitch_degrees', -32602);
  }
  if (!Array.isArray(commands) || commands.some((line) => typeof line !== 'string' || /[\n\r;]/.test(line))
    || (seconds !== undefined && !(Number.isFinite(seconds) && seconds >= 1))) {
    return failed('invalid_params', 'game.play_here: commands are single console lines; seconds is 1 or more', -32602);
  }
  if (!existsSync(runGame)) return failed('failed', 'the game launcher is missing', -32603);
  const started = Date.now();
  const built = await core.call('build.run', { project: folder, dry_run: false });
  if (built.error) return built;
  if (built.result.kind === 'overlay') {
    return failed('bad_request', 'an overlay project changes a shipped map: Play here starts new maps only (play the '
      + 'base map with the build installed)');
  }
  const configured = await core.call('session.configure', { asset_root: assets, mount });
  if (configured.error) return configured;
  const installed = await core.call('build.install', { project: folder });
  if (installed.error) return installed;
  // The game draws no ground without an outdoor map's terrain material file.
  if (built.result.kind === 'outdoor') {
    const materials = await new Promise((resolve) => {
      const child = spawn('python3', [path.join(repo, 'openyamm-studio/calibration/outdoor_materials.py'), folder,
        '--mount', mount], { cwd: repo, stdio: ['ignore', 'pipe', 'pipe'] });
      let output = '';
      child.stdout.on('data', (data) => { output += data; });
      child.stderr.on('data', (data) => { output += data; });
      child.on('close', (code) => resolve({ code, output }));
    });
    if (materials.code !== 0) {
      return failed('failed', `the terrain material file was not made: ${materials.output.trim().split('\n').at(-1)}`,
        -32603);
    }
  }
  const run = `studio-play-${new Date().toISOString().replace(/[-:T]/g, '').slice(0, 14)}-${process.pid % 1000}-${
    Math.floor(Math.random() * 1000)}`;
  const runFolder = path.join(runs, run);
  mkdirSync(runFolder, { recursive: true });
  const consoleFile = path.join(runFolder, 'start.console');
  const exitPoseFile = path.join(runFolder, 'exit_pose.yml');
  writeFileSync(consoleFile, startConsoleText(pose, commands));
  const args = ['--isolated', run, '--world', world, '--map', built.result.map, '--assets', assets,
    '--extra-mount', mount, '--set', `debug.startup_console_file=${consoleFile}`,
    '--set', `debug.exit_pose_path=${exitPoseFile}`, '--seconds', String(seconds ?? 0), '--warmup', '0'];
  if (visible) args.push('--visible');
  const child = spawn(runGame, args, { cwd: repo, env: context.env ?? process.env, stdio: ['ignore', 'pipe', 'pipe'] });
  let output = '';
  child.stdout.on('data', (data) => { output += data; });
  child.stderr.on('data', (data) => { output += data; });
  log(`play here ${run}: ${built.result.map} (${world}) at ${pose.position.join(' ')}, built and installed in ${
    Date.now() - started} ms`);
  child.on('close', (code) => {
    writeFileSync(path.join(runFolder, 'launcher.log'), output);
    let exitPose = null;
    try {
      exitPose = parseExitPose(readFileSync(exitPoseFile, 'utf8'));
    } catch {
      exitPose = null;
    }
    context.onExit?.({ run, code, map: built.result.map, world, exitPose });
  });
  return { result: { run, map: built.result.map, world, kind: built.result.kind } };
}
