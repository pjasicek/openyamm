#!/usr/bin/env python3
"""Own one creature across agent turns; serialize its writes without sharing Blender scenes.

Use tools/run_creature_workspace.sh with the same arguments as a stable entry point.
Keep ordinary workspace writes sandboxed; invoke the Blender and Meshy wrappers separately.
"""

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import uuid


REPO = Path(__file__).resolve().parents[1]
LOCK_ROOT = REPO / 'output/creature_3d_locks'
DEFAULT_STATE = 'creature_3d_progress.json'


def read_json(path):
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f'Expected a JSON object: {path}')
    return value


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        try:
            json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)


def project_path(project, relative):
    path = (project / relative).resolve()
    if not path.is_relative_to(project) or path == project:
        raise ValueError('File must remain inside the creature project')
    return path


@contextmanager
def file_lock(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a') as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError(f'Another creature operation is running: {path}') from None
        yield


def active_lease(project):
    if not LOCK_ROOT.exists():
        return None
    for path in LOCK_ROOT.glob('*.json'):
        lease = read_json(path)
        other = Path(lease['project'])
        if project.is_relative_to(other) or other.is_relative_to(project):
            return path, lease
    return None


@contextmanager
def project_guard(project, token=None, state=None):
    project = Path(project).resolve()
    if not project.is_dir():
        raise ValueError(f'Creature project does not exist: {project}')
    with file_lock(project / '.creature_3d_write.lock'):
        active = active_lease(project)
        if active:
            _, lease = active
            if not token or token != lease['token'] or str(project) != lease['project']:
                raise RuntimeError(f"Creature is owned by {lease['owner']}; use its recorded lease or another creature")
            if state and str(project_path(project, state)) != lease['state']:
                raise ValueError('This lease owns a different progress record')
        elif token:
            raise RuntimeError('Creature lease is no longer active')
        elif state:
            raise RuntimeError('Claim the creature before changing Meshy state')
        yield project


def claim(project, identity, owner, state=DEFAULT_STATE, budget=None):
    project = Path(project).resolve()
    creatures = REPO / 'level_generation/creatures'
    if project == REPO or project == creatures:
        raise ValueError('Choose one creature project, not a shared root')
    if project.is_relative_to(creatures) and project.parent != creatures:
        raise ValueError('Claim the top-level creature project; select its branch through --state')
    identity = identity.lower()
    if not re.fullmatch(r'[a-z0-9_-]+:[a-z0-9_-]+', identity):
        raise ValueError('Identity must be world:native-family, for example mm6:gob')
    if not owner.strip():
        raise ValueError('A nonempty agent/session owner is required')
    if budget is not None and (type(budget) is not int or budget <= 0):
        raise ValueError('Credit budget must be a positive integer')
    project.mkdir(parents=True, exist_ok=True)
    lease_path = LOCK_ROOT / (identity.replace(':', '_') + '.json')
    with project_guard(project), file_lock(lease_path.with_suffix('.lock')):
        if lease_path.exists():
            current = read_json(lease_path)
            raise RuntimeError(f"{identity} is owned by {current['owner']} in {current['project']}")
        state_path = project_path(project, state)
        progress = read_json(state_path) if state_path.exists() else {}
        previous_identity = progress.get('creature_3d_identity')
        if previous_identity and previous_identity != identity:
            raise ValueError('Existing progress belongs to another creature identity')
        progress['creature_3d_identity'] = identity
        meshy = progress.setdefault('meshy', {'jobs': {}})
        if not isinstance(meshy, dict) or not isinstance(meshy.get('jobs'), dict):
            raise ValueError('Existing meshy record must contain a jobs object')
        if budget is not None:
            meshy['credit_limit'] = budget
        else:
            meshy.setdefault('credit_limit', 100)
        lease = {'identity': identity, 'owner': owner, 'project': str(project), 'state': str(state_path),
                 'token': uuid.uuid4().hex, 'claimed_at': datetime.now(timezone.utc).isoformat()}
        write_json(state_path, progress)
        write_json(lease_path, lease)
        return lease


def release(project, token):
    with project_guard(project, token) as project:
        active = active_lease(project)
        if not active:
            raise RuntimeError('No active creature lease')
        path, _ = active
        path.unlink()


def run(project, token, command):
    if not command:
        raise ValueError('A command after -- is required')
    with project_guard(project, token):
        return subprocess.run(command, cwd=REPO, check=False).returncode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('claim', 'release', 'run'):
        command = commands.add_parser(name)
        command.add_argument('--project', required=True)
        if name == 'claim':
            command.add_argument('--identity', required=True)
            command.add_argument('--owner', required=True)
            command.add_argument('--state', default=DEFAULT_STATE)
            command.add_argument('--budget', type=int)
        else:
            command.add_argument('--token', default=os.environ.get('CREATURE_3D_TOKEN'))
        if name == 'run':
            command.add_argument('argv', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    try:
        if args.command == 'claim':
            print(json.dumps(claim(args.project, args.identity, args.owner, args.state, args.budget)))
        elif args.command == 'release':
            if not args.token:
                raise ValueError('The owning token is required')
            release(args.project, args.token)
        else:
            argv = args.argv[1:] if args.argv and args.argv[0] == '--' else args.argv
            raise SystemExit(run(args.project, args.token, argv))
    except (OSError, ValueError, RuntimeError) as error:
        parser.exit(1, f'{error}\n')


if __name__ == '__main__':
    main()
