#!/usr/bin/env python3
"""Collect retained capture evidence and verify the final pilot export/provenance."""
import configparser
import hashlib
import json
import re
from pathlib import Path

from PIL import Image

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[3]
REVIEW = PROJECT / 'review'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if json.loads((PROJECT / 'manifest.json').read_text())['selected_version'] != 'v2':
        raise SystemExit('This collector describes historical v2 captures. Current seam-review evidence is in review/v3/.')
    stage = json.loads((REVIEW / 'stage.json').read_text())
    captures = {}
    for tier in ('native', 'restored'):
        for view in ('overhead', 'horizon', 'loadcheck'):
            name = 'mm6sky_' + tier + '_' + view
            capture = json.loads((REVIEW / (name + '.json')).read_text())
            assert capture['binary_sha256'] == stage['binary_sha256']
            log = (REVIEW / (name + '.log')).read_text()
            timings = re.findall(r'stage="initial sky resource preloaded" delta_ms=([\d.]+)', log)
            capture['initial_sky_preload_ms'] = [float(v) for v in timings]
            capture['file_tracing_enabled'] = view == 'horizon'
            capture['render_time_sky_load_warnings'] = log.count('kind=sky phase=render')
            capture['screenshot_sha256'] = sha(REVIEW / capture['screenshot'])
            captures[name] = capture
    a, b = configparser.ConfigParser(), configparser.ConfigParser()
    a.read(REVIEW / 'settings_x1.ini')
    b.read(REVIEW / 'settings_x2.ini')
    assert a['video_quality']['sky'] == 'x1' and b['video_quality']['sky'] == 'x2'
    a['video_quality']['sky'] = 'x2'
    assert {s: dict(a[s]) for s in a.sections()} == {s: dict(b[s]) for s in b.sections()}
    evidence = {}
    for tier, directory, suffix in [('native', 'textures', 'bmp'), ('restored', 'textures_x2', 'png')]:
        output = REVIEW / (tier + '_sky_file_access.txt')
        trace = Path('/tmp/openyamm-mm6sky-' + tier + '-file-access.log')
        if trace.exists():
            lines = [line for line in trace.read_text().splitlines()
                     if f'/worlds/mm6/{directory}/6plansky1.{suffix}"' in line
                     and '= -1' not in line]
            assert lines, 'Expected sky file was not opened'
            output.write_text('\n'.join(lines) + '\n')
        assert output.exists()
        evidence[tier] = output.name
    runtime = {'captures': captures, 'successful_sky_file_opens': evidence,
               'same_binary': True, 'same_settings_except_sky_tier': True,
               'initial_sky_preloaded_during_map_load': True,
               'poses': {'overhead': [-9954.209, -9427.790, 161.0, 83.552, 25.955],
                         'horizon': [-9954.209, -9427.790, 161.0, 173.552, 5.0]},
               'pose_units': 'x,y,z in world units; yaw,pitch in degrees',
               'time_weather': 'Same retained save within each pair; successful asset open confirms 6plansky1',
               'limits': ['Single initial-load sample per tier; OS file cache not flushed.',
                          'Use untraced loadcheck timings only; horizon tracing substantially adds overhead.',
                          'Xvfb steady runs approximately 60fps; not a target-GPU performance benchmark.',
                          'No frame-level p95/p99 or long weather-transition/cache-lifecycle measurement.',
                          'Wall-clock cloud scroll and ordinary actors may differ between runs.',
                          'Only New Sorpigal fair-weather pilot, not all-map/night/weather acceptance.']}
    (REVIEW / 'runtime_checks.json').write_text(json.dumps(runtime, indent=2) + '\n')
    export = PROJECT / 'runtime_x2/6plansky1.png'
    assert export.read_bytes() == (PROJECT / 'runtime_x2/6sky01.png').read_bytes()
    assert export.read_bytes() == (Path(stage['stage']) / 'assets_dev/worlds/mm6/textures_x2/6plansky1.png').read_bytes()
    with Image.open(export) as image:
        assert image.size == (1024, 1024) and image.mode == 'RGB'
    assert sha(ROOT / 'settings.ini') == stage['main_settings_sha256']
    assert sha(ROOT / 'assets_dev/engine/data_tables/continent_settings.txt') == stage['continent_table_sha256']
    files = ['source/6plansky1.bmp', 'source/6plansky1.png', 'source/overhead.oysav', 'source/horizon.oysav',
             'prompts/v1.txt', 'prompts/v2.txt', 'generated/v1.png', 'generated/v2.png',
             'runtime_x2/6plansky1.png', 'runtime_x2/6sky01.png']
    manifest = {'world': 'mm6', 'texture_key': '6plansky1', 'identical_aliases': ['6sky01'],
                'status': 'visual review', 'selected_version': 'v2', 'user_art_acceptance': None,
                'agent_assessment': 'Tile and x1/x2 consistency reviewed; original-game sky/fog presentation unresolved after screenshot 1290',
                'generation_mode': 'built-in imagegen edit; v1 native restoration, v2 targeted palette correction',
                'native_source': 'assets_dev/worlds/mm6/textures/6plansky1.bmp',
                'native_size': [512, 512], 'generated_size': [1254, 1254], 'runtime_size': [1024, 1024],
                'selected_export': 'runtime_x2/6plansky1.png', 'runtime_sha256': sha(export),
                'export_method': 'ImageMagick Lanczos resize, opaque PNG24; no post-export palette or seam editing',
                'imagemagick_version': 'See export_tool_version.txt',
                'project_review': 'review/index.html', 'feedback': 'review/feedback.md',
                'production_installed': False, 'isolated_stage': stage['stage'],
                'planned_production_targets': ['assets_dev/worlds/mm6/textures_x2/6plansky1.png',
                                               'assets_dev/worlds/mm6/textures_x2/6sky01.png'],
                'files': {name: sha(PROJECT / name) for name in files}}
    (PROJECT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({tier: captures['mm6sky_' + tier + '_loadcheck']['initial_sky_preload_ms']
                      for tier in ('native', 'restored')}, indent=2))
    print('Capture, tier, staged-export, duplicate and unchanged-main-settings checks passed.')


if __name__ == '__main__':
    main()
