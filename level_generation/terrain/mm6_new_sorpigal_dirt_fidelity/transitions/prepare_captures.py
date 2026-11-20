"""Prepare isolated flat fixtures and sustained-flight camera saves for the new dirt pack."""
import configparser
import json
import math
from pathlib import Path
import shutil
import subprocess

P = Path(__file__).resolve().parent
OLD = P.parents[1] / 'mm6_new_sorpigal_transitions'
stage = Path('/tmp/openyamm-sorpigal-dirt-fidelity')
playtest = json.loads((P / 'reports/playtest.json').read_text())
tile_names = [*playtest['files'], *playtest['water']['files']]
runtime = stage / 'transitions/assets_dev/worlds/mm6/terrain_x2'
flat = stage / 'transitions_flat'
if not flat.exists():
    shutil.copytree(stage / 'transitions', flat, symlinks=True)
maps = flat / 'assets_dev/worlds/mm6/maps'
assert not maps.is_symlink()
for overlay in maps.glob('oute3.scene.*.yml'):
    overlay.rename(overlay.with_suffix('.yml.disabled'))
for name in ['oute3.odm', 'oute3.scene.yml']:
    assert not (maps / name).is_symlink()
    shutil.copy2(OLD / 'fixture' / name, maps / name)
for source in (runtime / name for name in tile_names):
    shutil.copy2(source, flat / 'assets_dev/worlds/mm6/terrain_x2' / source.name)
settings = configparser.ConfigParser(interpolation=None)
settings.read(flat / 'settings.ini')
settings['assets']['root'] = str(flat / 'assets_dev')
with (flat / 'settings.ini').open('w') as stream:
    settings.write(stream, space_around_delimiters=False)
linear = stage / 'transitions_flat_linear'
if not linear.exists():
    shutil.copytree(flat, linear, symlinks=True)
settings['assets']['root'] = str(linear / 'assets_dev')
settings['video']['terrain_filtering'] = 'linear'
with (linear / 'settings.ini').open('w') as stream:
    settings.write(stream, space_around_delimiters=False)
for source in (runtime / name for name in tile_names):
    shutil.copy2(source, linear / 'assets_dev/worlds/mm6/terrain_x2' / source.name)
subprocess.run(['python3', str(OLD / 'build_pose_helper.py')], check=True)
poses = json.loads((P / 'captures/poses.json').read_text())
for pose in poses:
    if pose['name'] == 'user_dirt':
        continue
    output = P / 'captures/poses' / (pose['stage'] + '_' + pose['name'] + '.oysav')
    output.parent.mkdir(exist_ok=True)
    command = ['/tmp/sorpigal-transition-capture-save', str(P.parent / 'references/Dirt_View.oysav'),
               str(output), str(pose['x']), str(pose['y']), str(pose['z']),
               str(math.radians(pose['yaw'])), str(math.radians(pose['pitch']))]
    if pose['stage'] == 'flat':
        command.append('empty-world')
    command.append('--fly-buff')
    subprocess.run(command, check=True)
