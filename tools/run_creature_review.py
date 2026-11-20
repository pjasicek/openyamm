#!/usr/bin/env python3
"""Reusable approval entry point for local creature viewer checks and captures.

python3 tools/run_creature_review.py --project level_generation/creatures/mm8_m564_claude check
python3 tools/run_creature_review.py --project <project> --token <lease> playback
python3 tools/run_creature_review.py --project <project> --token <lease> shots standing:Standing:0:quarter:body
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.parse import quote

from creature_workspace import REPO, project_guard

CREATURES = REPO / 'level_generation/creatures'
SHARED = CREATURES / 'claude_shared'


def command(project, mode, port, shots, tier=None):
    project = Path(project).resolve(strict=True)
    if project.parent != CREATURES or not 1024 <= port <= 65535:
        raise ValueError('Choose one creature project and a local server port from 1024 to 65535')
    viewer = project / 'review/viewer'
    if not viewer.resolve().is_relative_to(project):
        raise ValueError('Viewer must remain inside the project')
    manifest = json.loads((viewer / 'manifest.json').read_text())
    url = f'http://127.0.0.1:{port}/{quote(viewer.relative_to(REPO).as_posix())}/'
    clips = {name: clip['duration'] for name, clip in manifest['clips'].items()}
    if tier:
        model = next((model for model in manifest['models'] if model['id'] == tier), None)
        if model is None:
            raise ValueError(f'Unknown model tier: {tier}')
        url += '#' + quote(json.dumps({'clip': manifest['default_clip'], 'model_sha256': model['sha256']}))
        clips = {name: clip['duration'] for name, clip in model.get('clips', manifest['clips']).items()}
    output = (project / 'review' / mode).resolve()
    if not output.is_relative_to(project):
        raise ValueError('Capture output must remain inside the project')
    if mode == 'check':
        return ['node', str(SHARED / 'check_viewer.mjs'), url]
    if mode == 'playback':
        return ['node', str(SHARED / 'capture_playback.mjs'), url, str(output)]
    if mode != 'shots' or not shots:
        raise ValueError('shots requires name:clip:seconds:view:focus entries')
    for shot in shots:
        parts = shot.split(':')
        if len(parts) != 5:
            raise ValueError('Each shot is name:clip:seconds:view:focus')
        name, clip, seconds, view, focus = parts
        if (not re.fullmatch(r'[A-Za-z0-9_-]+', name) or clip not in clips
                or not 0 <= float(seconds) <= clips[clip]
                or view not in ('front', 'right', 'left', 'back', 'quarter', 'rear')
                or focus not in ('body', 'head', 'arms', 'shoulders', 'skirt', 'feet')):
            raise ValueError(f'Invalid shot: {shot}')
    return ['node', str(CREATURES / 'mm8_m424_claude/scripts/viewer_shots.mjs'), url, str(output), *shots]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--project', required=True, type=Path)
    parser.add_argument('--token', default=os.environ.get('CREATURE_3D_TOKEN'))
    parser.add_argument('--port', type=int, default=8912)
    parser.add_argument('--tier', help='Model id from the viewer manifest; default is its selected model')
    parser.add_argument('mode', choices=('check', 'shots', 'playback'))
    parser.add_argument('shots', nargs='*')
    args = parser.parse_args()
    try:
        argv = command(args.project, args.mode, args.port, args.shots, args.tier)
        if args.mode == 'check':
            return subprocess.run(argv, cwd=REPO, check=False).returncode
        with project_guard(args.project, args.token):
            return subprocess.run(argv, cwd=REPO, check=False).returncode
    except (OSError, ValueError, RuntimeError, KeyError) as error:
        parser.exit(1, f'{error}\n')


if __name__ == '__main__':
    raise SystemExit(main())
