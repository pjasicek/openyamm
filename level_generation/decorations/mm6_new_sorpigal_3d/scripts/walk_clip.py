#!/usr/bin/env python3
"""Walk toward one New Sorpigal 6tree01 (9848, 3904; open flat ground to its south) from 6500 to 600 units in a single game run and assemble the
screenshots into an MP4 plus a contact sheet, to judge LOD switches and crossfades in motion. The engine switches
this tree to LOD1 near 1750 units, LOD2 near 3100 and its impostor near 4600 (1600x900).
Usage: walk_clip.py <out_dir> [extra --set args for run_game.sh]"""
import glob, os, subprocess, sys
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
out = os.path.abspath(sys.argv[1]); extra = sys.argv[2:]
os.makedirs(out, exist_ok=True)
for old in glob.glob(os.path.join(out, '*.png')):
    os.remove(old)
tx, ty, z = 9848.0, 3904.0, 170.0
frames = 90
lines = [f'output_dir: {out}', 'settle_seconds: 0.1', 'exit: true', 'shots:']
for i in range(frames):
    d = 6500.0 - (6500.0 - 600.0) * i / (frames - 1)
    lines += [f'  - name: f{i:03d}', f'    position: [{tx:.0f}, {ty - d:.0f}, {z:.0f}]', '    yaw: 1.5708',
              '    pitch: 0.06']
tour = os.path.join(out, 'tour.yml')
open(tour, 'w').write('\n'.join(lines) + '\n')
cmd = [os.path.join(REPO, 'tools/run_game.sh'), '--isolated', 'tree_walk', '--world', 'mm6', '--map', 'oute3.odm',
       '--position', str(tx), str(ty - 6500), str(z), '--yaw-radians', '1.5708', '--pitch-degrees', '3',
       '--warmup', '3', '--seconds', '90', '--set', f'debug.screenshot_tour_path={tour}']
for e in extra:
    cmd += ['--set', e]
subprocess.run(cmd, cwd=REPO, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=400)
shots = sorted(glob.glob(os.path.join(out, '*-f*.png')))
print('frames', len(shots))
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '12', '-pattern_type', 'glob', '-i',
                os.path.join(out, '*-f*.png'), '-vf', 'crop=900:520:350:120,scale=900:-2', '-pix_fmt', 'yuv420p',
                os.path.join(out, 'walk.mp4')], check=True)
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-pattern_type', 'glob', '-i', os.path.join(out, '*-f*.png'),
                '-vf', 'select=not(mod(n\\,6)),crop=900:520:350:120,scale=300:-2,tile=5x3', '-frames:v', '1',
                os.path.join(out, 'sheet.png')], check=True)
