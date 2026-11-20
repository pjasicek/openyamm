#!/usr/bin/env python3
"""Submit/resume creature and prop Meshy jobs with local uploads and durable receipts."""

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import tempfile
import time
import tomllib
import urllib.error
import urllib.parse
import urllib.request

from creature_workspace import DEFAULT_STATE, project_guard, project_path, read_json, write_json


API_BASE = 'https://api.meshy.ai'
ENDPOINTS = {'image-to-3d': '/openapi/v1/image-to-3d', 'multi-image-to-3d': '/openapi/v1/multi-image-to-3d',
             'text-to-3d': '/openapi/v2/text-to-3d', 'rigging': '/openapi/v1/rigging',
             'retexture': '/openapi/v1/retexture', 'animation': '/openapi/v1/animations',
             'remesh': '/openapi/v1/remesh', 'text-to-motion': '/openapi/v1/text-to-motion'}
# Meshy accounts in order of use: the backup takes new jobs once the primary has too few credits. A task belongs to
# the account that created it, so each job records its account and every later call for it uses that account.
ACCOUNTS = (('primary', 'MESHY_API_KEY'), ('backup', 'MESHY_API_KEY_BACKUP'))
MIME = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
        '.glb': 'application/octet-stream', '.gltf': 'application/octet-stream',
        '.obj': 'application/octet-stream', '.fbx': 'application/octet-stream', '.stl': 'application/octet-stream'}


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def account_keys():
    config = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))) / 'config.toml'
    environment = {}
    if config.exists():
        environment = tomllib.loads(config.read_text()).get('mcp_servers', {}).get('meshy', {}).get('env', {})
    keys = {}
    for account, variable in ACCOUNTS:
        key = os.environ.get(variable) or environment.get(variable)
        if isinstance(key, str) and key.strip():
            keys[account] = key.strip()
    return keys


def api_key(account='primary'):
    key = account_keys().get(account)
    if not key:
        variable = dict(ACCOUNTS)[account]
        raise ValueError(f'Set {variable} or configure it in the global meshy MCP environment')
    return key


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        return None


def api_request(method, endpoint, payload=None, account='primary'):
    key = api_key(account)
    data = json.dumps(payload, allow_nan=False).encode() if payload is not None else None
    request = urllib.request.Request(API_BASE + endpoint, data=data, method=method,
                                     headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
    # POST is deliberately sent once. A lost response does not prove that no job was created.
    with urllib.request.build_opener(NoRedirect).open(request, timeout=60) as response:
        return json.load(response)


def expand_files(value, project, inputs):
    if isinstance(value, dict):
        if any(key.lower() in ('authorization', 'api_key', 'meshy_api_key') for key in value):
            raise ValueError('Credentials belong in the environment, never request JSON')
        return {key: expand_files(item, project, inputs) for key, item in value.items()}
    if isinstance(value, list):
        return [expand_files(item, project, inputs) for item in value]
    if isinstance(value, str) and value.startswith('@file:'):
        path = project_path(project, value[6:])
        if path.suffix.lower() not in MIME or not path.is_file():
            raise ValueError('Upload must be a supported image/model file inside the project')
        if path.stat().st_size > 100 * 1024 * 1024:
            raise ValueError('Upload exceeds the 100 MiB local-file limit')
        content = path.read_bytes()
        inputs.append({'path': str(path.relative_to(project)), 'sha256': hashlib.sha256(content).hexdigest()})
        return 'data:' + MIME[path.suffix.lower()] + ';base64,' + base64.b64encode(content).decode()
    if isinstance(value, str) and value.startswith('data:'):
        raise ValueError('Use @file: paths instead of embedding uploads in request JSON')
    return value


def load_state(project, state):
    path = project_path(project, state)
    progress = read_json(path)
    meshy = progress['meshy']
    if type(meshy['credit_limit']) is not int or meshy['credit_limit'] <= 0 or not isinstance(meshy['jobs'], dict):
        raise ValueError('Malformed Meshy progress or credit limit')
    return path, progress, meshy


def inspect(project, state):
    project = Path(project).resolve()
    path = project_path(project, state)
    progress = read_json(path)
    missing, changed = [], []
    artifacts = progress.get('selected_artifacts', [])
    if not isinstance(artifacts, list):
        raise ValueError('Inspect expects selected_artifacts as a list; inspect other manifest formats directly')
    present_roles = set()
    for artifact in artifacts:
        selected = project_path(project, str((path.parent / artifact['path']).relative_to(project)))
        if not selected.is_file():
            missing.append(artifact['path'])
        elif artifact.get('sha256') and sha(selected) != artifact['sha256']:
            changed.append(artifact['path'])
        elif artifact.get('role'):
            present_roles.add(artifact['role'])
    components = [item['id'] for item in progress.get('required_components', [])
                  if item.get('required', True) and item['artifact_role'] not in present_roles]
    return {'identity': progress.get('creature_3d_identity'), 'stage': progress.get('current_stage'),
            'substep': progress.get('current_substep'), 'next_action': progress.get('next_action'),
            'missing_files': missing, 'changed_files': changed, 'missing_component_roles': components,
            'component_inventory_recorded': 'required_components' in progress,
            'jobs': {name: {key: job[key] for key in ('task_id', 'account', 'status', 'reserved_credits',
                                                      'consumed_credits')
                           if key in job} for name, job in progress.get('meshy', {}).get('jobs', {}).items()}}


def referenced_tasks(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if key.endswith('task_id') and isinstance(item, str):
                yield item
            else:
                yield from referenced_tasks(item)
    elif isinstance(value, list):
        for item in value:
            yield from referenced_tasks(item)


def submission_account(meshy, source, credits):
    # A job built on an earlier task (rig_task_id, input_task_id) must run on that task's account.
    referenced = set(referenced_tasks(source))
    accounts = {job.get('account', 'primary') for job in meshy['jobs'].values() if job.get('task_id') in referenced}
    if len(accounts) > 1:
        raise ValueError('Request references tasks from different Meshy accounts')
    if accounts:
        return accounts.pop()
    keys = account_keys()
    if not keys:
        api_key()
    if len(keys) == 1:
        return next(iter(keys))
    for account in keys:
        if api_request('GET', '/openapi/v1/balance', account=account).get('balance', 0) >= credits:
            return account
    raise RuntimeError('No Meshy account has enough credits for this job; report remaining work')


def reserved_credits(meshy):
    total = 0
    for job in meshy['jobs'].values():
        values = (job['reserved_credits'], job.get('consumed_credits', 0))
        if any(isinstance(value, bool) or not isinstance(value, (int, float))
               or not math.isfinite(value) or value < 0 for value in values):
            raise ValueError('Malformed Meshy credit receipt')
        if job['status'] in ('SUCCEEDED', 'FAILED', 'CANCELED') and 'consumed_credits' in job.get('task', {}):
            total += values[1]
        else:
            total += max(values)
    return total


def submit(project, state, token, job_name, kind, request_path, credits):
    if not re.fullmatch(r'[a-zA-Z0-9_-]+', job_name) or type(credits) is not int or credits <= 0:
        raise ValueError('Use a simple unique job name and a positive conservative credit estimate')
    with project_guard(project, token, state) as project:
        path, progress, meshy = load_state(project, state)
        source = read_json(project_path(project, request_path))
        inputs = []
        payload = expand_files(source, project, inputs)
        fingerprint = hashlib.sha256(json.dumps({'kind': kind, 'request': source, 'inputs': inputs},
                                                sort_keys=True, allow_nan=False).encode()).hexdigest()
        existing = meshy['jobs'].get(job_name)
        if existing:
            if existing['fingerprint'] != fingerprint:
                raise ValueError('Job input changed; inspect dependencies and use a new revision/job name')
            if not existing.get('task_id'):
                raise RuntimeError('Submission has no confirmed task ID; reconcile it before creating another job')
            return existing
        if any(job['status'] in ('SUBMITTING', 'UNCERTAIN') and not job.get('task_id')
               for job in meshy['jobs'].values()):
            raise RuntimeError('An unresolved submission exists; reconcile it before creating any new paid job')
        if reserved_credits(meshy) + credits > meshy['credit_limit']:
            raise RuntimeError('Creature Meshy credit limit reached; retain checkpoints and report remaining work')
        # Detects missing credentials before recording any submission intent.
        account = submission_account(meshy, source, credits)
        job = {'kind': kind, 'request': source, 'inputs': inputs, 'fingerprint': fingerprint, 'account': account,
               'reserved_credits': credits, 'status': 'SUBMITTING',
               'submitted_at': datetime.now(timezone.utc).isoformat()}
        meshy['jobs'][job_name] = job
        write_json(path, progress)
        try:
            response = api_request('POST', ENDPOINTS[kind], payload, account)
            task_id = response.get('result')
            if not isinstance(task_id, str) or not re.fullmatch(r'[a-zA-Z0-9_-]+', task_id):
                raise ValueError('Meshy returned no valid task ID')
            job.update(task_id=task_id, status='PENDING')
        except Exception as error:
            rejected = isinstance(error, urllib.error.HTTPError) and error.code in (
                400, 401, 402, 403, 404, 405, 413, 415, 422, 429)
            job['status'] = 'REJECTED' if rejected else 'UNCERTAIN'
            job['error'] = {'type': type(error).__name__, 'http_status': getattr(error, 'code', None)}
            if isinstance(error, urllib.error.HTTPError):
                try:
                    message = error.read(4096).decode(errors='replace')
                    for key in account_keys().values():
                        message = message.replace(key, '[REDACTED]')
                    message = re.sub(r'data:[^\s"\']+', '[encoded upload omitted]', message)
                    message = re.sub(r'msy_[a-zA-Z0-9]+', '[REDACTED]', message)
                    job['error']['message'] = message[:1024]
                finally:
                    error.close()
            if rejected:
                job['reserved_credits'] = 0
            write_json(path, progress)
            raise RuntimeError(f"Submission {job['status']}; inspect the receipt before another submission") from None
        write_json(path, progress)
        return job


def fetch_job(job):
    task = api_request('GET', ENDPOINTS[job['kind']] + '/' + job['task_id'], account=job.get('account', 'primary'))
    if task.get('id') != job['task_id']:
        raise ValueError('Meshy returned a different task ID')
    if 'consumed_credits' in task:
        consumed = task['consumed_credits']
        if (not isinstance(consumed, (int, float)) or isinstance(consumed, bool)
                or not math.isfinite(consumed) or consumed < 0):
            raise ValueError('Meshy returned an invalid consumed-credit amount')
        job['consumed_credits'] = consumed
    job.update(status=task['status'], task=task)
    return job


def poll(project, state, token, job_name, wait_seconds=0):
    if not 0 <= wait_seconds <= 45:
        raise ValueError('Use a bounded status wait of 0–45 seconds')
    with project_guard(project, token, state) as project:
        path, progress, meshy = load_state(project, state)
        job = meshy['jobs'][job_name]
        if not job.get('task_id'):
            raise RuntimeError('Reconcile the uncertain submission before polling')
        deadline = time.monotonic() + wait_seconds
        while True:
            fetch_job(job)
            write_json(path, progress)
            if job['status'] in ('SUCCEEDED', 'FAILED', 'CANCELED') or time.monotonic() >= deadline:
                return job
            time.sleep(min(5, max(0, deadline - time.monotonic())))


def adopt(project, state, token, job_name, task_id, evidence):
    if not re.fullmatch(r'[a-zA-Z0-9_-]+', task_id) or not evidence.strip():
        raise ValueError('A valid task ID and reconciliation evidence are required')
    with project_guard(project, token, state) as project:
        path, progress, meshy = load_state(project, state)
        job = meshy['jobs'][job_name]
        if job.get('task_id') and job['task_id'] != task_id:
            raise ValueError('Cannot replace an existing task ID')
        candidate = dict(job, task_id=task_id)
        fetch_job(candidate)
        candidate['reconciliation_evidence'] = evidence
        job.update(candidate)
        write_json(path, progress)
        return job


def output_urls(value, prefix=''):
    if isinstance(value, dict):
        for name, item in value.items():
            yield from output_urls(item, prefix + '_' + name)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from output_urls(item, prefix + '_' + str(index))
    elif isinstance(value, str) and value.startswith('https://'):
        yield prefix.strip('_'), value


def download(project, state, token, job_name):
    with project_guard(project, token, state) as project:
        path, progress, meshy = load_state(project, state)
        job = meshy['jobs'][job_name]
        if job['status'] != 'SUCCEEDED':
            raise RuntimeError('Poll until the job has succeeded before downloading')
        outputs = {key: job['task'][key] for key in ('model_urls', 'texture_urls', 'result', 'thumbnail_url',
                                                   'thumbnail_urls', 'alpha_thumbnail_url', 'video_url',
                                                   'multi_view_thumbnails') if key in job['task']}
        urls = list(output_urls(outputs))
        if not urls:
            raise ValueError('Succeeded task has no supported downloadable outputs; inspect its receipt')
        directory = project_path(project, 'meshy/' + job_name)
        directory.mkdir(parents=True, exist_ok=True)
        artifacts = job.setdefault('downloads', {})
        for name, url in urls:
            suffix = Path(urllib.parse.urlsplit(url).path).suffix.lower()
            filename = re.sub(r'[^a-zA-Z0-9_-]', '_', name) + (suffix or '.bin')
            target = project_path(project, str((directory / filename).relative_to(project)))
            previous = artifacts.get(name)
            if previous and target.is_file():
                if sha(target) != previous['sha256']:
                    raise ValueError('Downloaded source was modified; preserve it and diagnose before redownloading')
                continue
            with tempfile.NamedTemporaryFile(dir=directory, delete=False) as stream:
                temporary = Path(stream.name)
                try:
                    # Signed asset URLs receive no API Authorization header.
                    with urllib.request.urlopen(url, timeout=60) as response:
                        while chunk := response.read(1024 * 1024):
                            stream.write(chunk)
                        length = response.headers.get('Content-Length')
                        if length and stream.tell() != int(length):
                            raise ValueError('Incomplete Meshy asset download')
                    stream.flush()
                    os.fsync(stream.fileno())
                    digest = sha(temporary)
                    if target.exists() and sha(target) != digest:
                        raise ValueError('Existing unrecorded download differs; preserve both revisions')
                    os.replace(temporary, target)
                finally:
                    temporary.unlink(missing_ok=True)
            artifacts[name] = {'path': str(target.relative_to(project)), 'sha256': digest}
            write_json(path, progress)
        return job


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project')
    parser.add_argument('--state', default=DEFAULT_STATE)
    parser.add_argument('--token', default=os.environ.get('CREATURE_3D_TOKEN'))
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('balance', help='Read-only authentication/network check of every configured account')
    commands.add_parser('inspect', help='Read-only file/hash/component-role check; visual assembly review is separate')
    for name in ('submit', 'poll', 'download', 'adopt'):
        command = commands.add_parser(name)
        command.add_argument('--job', required=True)
        if name == 'submit':
            command.add_argument('--kind', required=True, choices=ENDPOINTS)
            command.add_argument('--request', required=True,
                                 help='Project-relative JSON; @file: paths upload local files')
            command.add_argument('--credits', type=int, required=True)
        elif name == 'poll':
            command.add_argument('--wait-seconds', type=float, default=0)
        elif name == 'adopt':
            command.add_argument('--task-id', required=True)
            command.add_argument('--evidence', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'balance':
            accounts = account_keys() or {'primary': api_key()}
            print(json.dumps({account: api_request('GET', '/openapi/v1/balance', account=account)
                              for account in accounts}))
            return
        if not args.project:
            parser.error('--project is required for creature operations')
        if args.command == 'inspect':
            print(json.dumps(inspect(args.project, args.state)))
            return
        common = (args.project, args.state, args.token, args.job)
        if args.command == 'submit':
            job = submit(*common, args.kind, args.request, args.credits)
        elif args.command == 'poll':
            job = poll(*common, args.wait_seconds)
        elif args.command == 'adopt':
            job = adopt(*common, args.task_id, args.evidence)
        else:
            job = download(*common)
        print(json.dumps({key: job[key] for key in ('task_id', 'status', 'reserved_credits', 'consumed_credits',
                                                  'downloads', 'error') if key in job}))
    except (OSError, ValueError, RuntimeError, KeyError, urllib.error.URLError) as error:
        # Avoid printing exception request bodies/headers or URL credentials.
        message = str(error) if isinstance(error, (ValueError, RuntimeError, KeyError)) else type(error).__name__
        parser.exit(1, message + '\n')


if __name__ == '__main__':
    main()
