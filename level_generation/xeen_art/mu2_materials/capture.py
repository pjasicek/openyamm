#!/usr/bin/env python3
"""In-game reference captures of the shipped maps whose ground and dressing MU-2 proposes for each Xeen surface map.
One isolated, minimised game run per shipped map (build-xeen binary), a noon tour of six views: four from above the
map's centre and two from quadrant points. Output: views/<world>_<map>/NN-<name>.png. Two runs at a time."""
import subprocess, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
REFS = [('mm7', '7out02.odm'), ('mm7', '7out03.odm'), ('mm7', '7out13.odm'), ('mm8', 'out03.odm'),
        ('mm6', 'outc1.odm'), ('mm7', '7out06.odm'), ('mm7', 'out10.odm'), ('mm7', 'out11.odm'),
        ('mm8', 'out07.odm'), ('mm6', 'outb3.odm'), ('mm7', 'out09.odm'), ('mm8', 'out08.odm'),
        ('mm6', 'outb1.odm'), ('mm8', 'out06.odm'), ('mm8', 'out04.odm'), ('mm7', '7out04.odm')]
import os
Z = int(os.environ.get('MU2_Z', '5200'))
SHOTS = [('centre-n', 0, 0, Z, 1.5708, -0.5), ('centre-s', 0, 0, Z, -1.5708, -0.5),
         ('sw-high', -14000, -14000, Z, 0.785, -0.42), ('ne-high', 14000, 14000, Z, -2.356, -0.42),
         ('nw-high', -14000, 14000, Z, -0.785, -0.42), ('se-high', 14000, -14000, Z, 2.356, -0.42)]


def launch(world, stem):
    out = HERE / 'views' / f'{world}_{stem[:-4]}'
    out.mkdir(parents=True, exist_ok=True)
    tour = out / 'tour.yml'
    lines = [f'output_dir: {out}', 'exit: true', 'settle_seconds: 2.5', 'shots:']
    for name, x, y, z, yaw, pitch in SHOTS:
        lines += [f'  - name: {name}', f'    position: [{x}, {y}, {z}]', f'    yaw: {yaw}', f'    pitch: {pitch}',
                  '    time: "12:00"', '    commands: ["sky weather 0", "weather clear"]']
    tour.write_text('\n'.join(lines) + '\n')
    cmd = [str(ROOT / 'tools/run_game.sh'), '--isolated', f'xeen_a6_mu2_{world}_{stem[:-4]}', '--world', world,
           '--map', stem, '--binary', str(ROOT / 'build-xeen/game/openyamm'), '--warmup', '5', '--seconds', '60',
           '--set', f'debug.screenshot_tour_path={tour}']
    log = open(out / 'run.log', 'w')
    return subprocess.Popen(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)


def main():
  todo = [r for r in REFS if not list((HERE / 'views' / f'{r[0]}_{r[1][:-4]}').glob('06-*.png'))]
  running = []
  while todo or running:
      while todo and len(running) < 2:
          r = todo.pop(0)
          running.append((r, launch(*r)))
      for item in list(running):
          if item[1].poll() is not None:
              running.remove(item)
              shots = list((HERE / 'views' / f'{item[0][0]}_{item[0][1][:-4]}').glob('*.png'))
              print(item[0], 'exit', item[1].returncode, 'shots', len(shots), flush=True)
      time.sleep(2)


if __name__ == '__main__':
    main()
