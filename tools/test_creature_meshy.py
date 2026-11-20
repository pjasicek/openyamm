#!/usr/bin/env python3
"""Offline checks for creature ownership, paid submission recovery and artifact integrity."""

import io
from contextlib import redirect_stdout
import json
import multiprocessing
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

import creature_meshy as meshy
import creature_workspace as workspace


class CreatureJobsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.lock_patch = patch.object(workspace, 'LOCK_ROOT', self.root / 'locks')
        self.lock_patch.start()
        self.addCleanup(self.lock_patch.stop)
        self.project = self.root / 'goblin'
        self.lease = workspace.claim(self.project, 'mm6:gob', 'agent-goblin')
        (self.project / 'reference.png').write_bytes(b'original-reference')
        workspace.write_json(self.project / 'request.json', {'image_url': '@file:reference.png',
                                                            'model_type': 'smart-topology', 'ai_model': 'meshy-t2'})
        self.key_patch = patch.object(meshy, 'account_keys', return_value={'primary': 'fake-key-for-offline-tests'})
        self.key_patch.start()
        self.addCleanup(self.key_patch.stop)

    def submit(self, name='body_v1', credits=15):
        return meshy.submit(self.project, workspace.DEFAULT_STATE, self.lease['token'], name,
                            'image-to-3d', 'request.json', credits)

    def test_two_creatures_can_work_but_aliases_and_foreign_writers_cannot(self):
        other = workspace.claim(self.root / 'demon', 'mm6:dmn', 'agent-demon')
        self.assertNotEqual(other['token'], self.lease['token'])
        with self.assertRaises(RuntimeError):
            workspace.claim(self.root / 'alternate-goblin-branch', 'MM6:GOB', 'another-agent')
        with self.assertRaises(RuntimeError):
            with workspace.project_guard(self.project, other['token']):
                self.fail('Foreign owner acquired project')
        with self.assertRaises(RuntimeError):
            workspace.run(self.project, None, ['true'])
        with self.assertRaises(RuntimeError):
            workspace.release(self.project, other['token'])
        context = multiprocessing.get_context('fork')
        results = context.Queue()

        def competing_writer():
            try:
                with workspace.project_guard(self.project, self.lease['token']):
                    results.put('acquired')
            except RuntimeError:
                results.put('blocked')

        with workspace.project_guard(self.project, self.lease['token']):
            process = context.Process(target=competing_writer)
            process.start()
            process.join(timeout=5)
            self.assertFalse(process.is_alive())
            self.assertEqual(results.get(timeout=1), 'blocked')
        self.assertEqual(workspace.run(self.project, self.lease['token'], ['sh', '-c', 'exit 7']), 7)
        workspace.release(self.project, self.lease['token'])
        resumed = workspace.claim(self.project, 'mm6:gob', 'resumed-agent')
        self.assertNotEqual(resumed['token'], self.lease['token'])
        with self.assertRaises(RuntimeError):
            with workspace.project_guard(self.project, self.lease['token']):
                self.fail('Released owner acquired project')

    def test_submission_reuses_receipt_and_detects_changed_input(self):
        with patch.object(meshy, 'api_request', return_value={'result': 'task-body'}) as api:
            first = self.submit()
            self.assertEqual(self.submit()['task_id'], first['task_id'])
            self.assertEqual(api.call_count, 1)
            self.assertTrue(api.call_args.args[2]['image_url'].startswith('data:image/png;base64,'))
            record = workspace.read_json(self.project / workspace.DEFAULT_STATE)['meshy']['jobs']['body_v1']
            self.assertNotIn('base64,', json.dumps(record))
            (self.project / 'reference.png').write_bytes(b'changed-reference')
            with self.assertRaises(ValueError):
                self.submit()
            self.assertEqual(api.call_count, 1)

    def test_uncertain_submission_survives_resume_without_resubmission(self):
        with patch.object(meshy, 'api_request', side_effect=TimeoutError()) as api:
            with self.assertRaises(RuntimeError):
                self.submit()
            with self.assertRaises(RuntimeError):
                self.submit()
            with self.assertRaises(RuntimeError):
                self.submit('body_v2')
            (self.project / 'reference.png').write_bytes(b'changed-reference')
            with self.assertRaises(RuntimeError):
                self.submit('body_v3')
            self.assertEqual(api.call_count, 1)
        state = workspace.read_json(self.project / workspace.DEFAULT_STATE)
        self.assertEqual(state['meshy']['jobs']['body_v1']['status'], 'UNCERTAIN')
        with patch.object(meshy, 'api_request', return_value={'id': 'recovered-task', 'status': 'PENDING'}):
            meshy.adopt(self.project, workspace.DEFAULT_STATE, self.lease['token'], 'body_v1',
                        'recovered-task', 'Matched service receipt and submission time')
        with patch.object(meshy, 'api_request') as api:
            (self.project / 'reference.png').write_bytes(b'original-reference')
            self.assertEqual(self.submit()['task_id'], 'recovered-task')
            api.assert_not_called()

    def test_credit_reservations_and_rejected_requests(self):
        with patch.object(meshy, 'api_request', return_value={'result': 'task-body'}):
            self.submit(credits=95)
        with patch.object(meshy, 'api_request') as api:
            with self.assertRaises(RuntimeError):
                self.submit('weapon_v1', credits=15)
            api.assert_not_called()
        workspace.release(self.project, self.lease['token'])
        self.lease = workspace.claim(self.project, 'mm6:gob', 'agent-goblin', budget=110)
        rejected = urllib.error.HTTPError('https://api.meshy.ai/test', 422, 'Invalid pose', {}, None)
        with patch.object(meshy, 'api_request', side_effect=rejected):
            with self.assertRaises(RuntimeError):
                self.submit('weapon_v1', credits=15)
        state = workspace.read_json(self.project / workspace.DEFAULT_STATE)
        self.assertEqual(state['meshy']['jobs']['weapon_v1']['status'], 'REJECTED')
        self.assertEqual(meshy.reserved_credits(state['meshy']), 95)

    def test_only_explicit_terminal_costs_release_unused_reservations(self):
        with patch.object(meshy, 'api_request', return_value={'result': 'task-body'}):
            self.submit(credits=95)
        task = {'id': 'task-body', 'status': 'PENDING'}
        with patch.object(meshy, 'api_request', return_value=task):
            job = meshy.poll(self.project, workspace.DEFAULT_STATE, self.lease['token'], 'body_v1')
            self.assertNotIn('consumed_credits', job)
            task.update(status='SUCCEEDED')
            meshy.poll(self.project, workspace.DEFAULT_STATE, self.lease['token'], 'body_v1')
            state = workspace.read_json(self.project / workspace.DEFAULT_STATE)
            self.assertEqual(meshy.reserved_credits(state['meshy']), 95)
            task['consumed_credits'] = 5
            meshy.poll(self.project, workspace.DEFAULT_STATE, self.lease['token'], 'body_v1')
            state = workspace.read_json(self.project / workspace.DEFAULT_STATE)
            self.assertEqual(meshy.reserved_credits(state['meshy']), 5)
        with patch.object(meshy, 'api_request', return_value={'result': 'task-weapon'}):
            self.submit('weapon_v1', credits=15)
        task = {'id': 'task-weapon', 'status': 'FAILED', 'consumed_credits': 0}
        with patch.object(meshy, 'api_request', return_value=task):
            meshy.poll(self.project, workspace.DEFAULT_STATE, self.lease['token'], 'weapon_v1')
        state = workspace.read_json(self.project / workspace.DEFAULT_STATE)
        self.assertEqual(meshy.reserved_credits(state['meshy']), 5)

    def test_download_resume_hash_checks_and_missing_equipment(self):
        with patch.object(meshy, 'api_request', return_value={'result': 'task-body'}):
            self.submit()
        task = {'id': 'task-body', 'status': 'SUCCEEDED', 'consumed_credits': 15,
                'model_urls': {'glb': 'https://assets.meshy.ai/body.glb'}}
        with patch.object(meshy, 'api_request', return_value=task):
            meshy.poll(self.project, workspace.DEFAULT_STATE, self.lease['token'], 'body_v1')
        response = io.BytesIO(b'glTF-test-body')
        response.headers = {'Content-Length': str(len(response.getvalue()))}
        with patch.object(meshy.urllib.request, 'urlopen', return_value=response) as network:
            job = meshy.download(self.project, workspace.DEFAULT_STATE, self.lease['token'], 'body_v1')
            meshy.download(self.project, workspace.DEFAULT_STATE, self.lease['token'], 'body_v1')
            self.assertEqual(network.call_count, 1)
            self.assertEqual(network.call_args.args[0], task['model_urls']['glb'])
        state_path = self.project / workspace.DEFAULT_STATE
        state = workspace.read_json(state_path)
        artifact = dict(job['downloads']['model_urls_glb'], role='body')
        state['selected_artifacts'] = [artifact]
        state['required_components'] = [{'id': 'body', 'artifact_role': 'body'},
                                        {'id': 'scimitar', 'artifact_role': 'weapon'}]
        workspace.write_json(state_path, state)
        self.assertEqual(meshy.inspect(self.project, workspace.DEFAULT_STATE)['missing_component_roles'], ['scimitar'])
        self.assertTrue(meshy.inspect(self.project, workspace.DEFAULT_STATE)['component_inventory_recorded'])
        (self.project / artifact['path']).write_bytes(b'tampered')
        self.assertEqual(meshy.inspect(self.project, workspace.DEFAULT_STATE)['changed_files'], [artifact['path']])
        with patch.object(meshy.urllib.request, 'urlopen') as network:
            with self.assertRaises(ValueError):
                meshy.download(self.project, workspace.DEFAULT_STATE, self.lease['token'], 'body_v1')
            network.assert_not_called()

    def test_api_posts_once_and_local_upload_cannot_escape_project(self):
        with patch.object(meshy.urllib.request, 'build_opener') as opener:
            opener.return_value.open.side_effect = TimeoutError()
            with self.assertRaises(TimeoutError):
                meshy.api_request('POST', '/openapi/v1/rigging', {'model_url': 'example'})
            self.assertEqual(opener.return_value.open.call_count, 1)
        with self.assertRaises(ValueError):
            meshy.expand_files('@file:../secret.png', self.project, [])
        with self.assertRaises(ValueError):
            meshy.expand_files({'api_key': 'secret'}, self.project, [])
        with self.assertRaises(ValueError):
            meshy.expand_files('data:image/png;base64,secrets', self.project, [])

    def test_fixed_wrapper_preserves_arguments_and_balance_creates_no_job(self):
        wrapper = workspace.REPO / 'tools/run_creature_meshy.sh'
        project = self.root / 'creature with spaces'
        workspace.write_json(project / workspace.DEFAULT_STATE,
                             workspace.read_json(self.project / workspace.DEFAULT_STATE))
        result = subprocess.run([str(wrapper), '--project', str(project), 'inspect'], cwd=self.root,
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['identity'], 'mm6:gob')
        marker = self.root / 'unapproved-python.txt'
        result = subprocess.run([str(wrapper), '-c', f"open({str(marker)!r}, 'w').write('unexpected')"],
                                cwd=self.root, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 2)
        self.assertFalse(marker.exists())
        output = io.StringIO()
        with patch.object(sys, 'argv', ['creature_meshy.py', 'balance']), redirect_stdout(output):
            with patch.object(meshy, 'api_request', return_value={'balance': 100}) as api:
                meshy.main()
                api.assert_called_once_with('GET', '/openapi/v1/balance', account='primary')
        self.assertEqual(json.loads(output.getvalue()), {'primary': {'balance': 100}})
        self.assertEqual(workspace.read_json(self.project / workspace.DEFAULT_STATE)['meshy']['jobs'], {})

    def test_backup_account_takes_new_jobs_and_follow_ups_stay_on_their_account(self):
        workspace.write_json(self.project / 'rig.json', {'rig_task_id': 'task-body', 'height_meters': 1.7})
        balances = {'primary': 10, 'backup': 3000}

        def api(method, endpoint, payload=None, account='primary'):
            if endpoint.endswith('/balance'):
                return {'balance': balances[account]}
            if method == 'POST':
                return {'result': 'task-body' if 'image' in endpoint else 'task-rig'}
            return {'id': endpoint.rsplit('/', 1)[1], 'status': 'SUCCEEDED', 'consumed_credits': 5}

        with patch.object(meshy, 'account_keys', return_value={'primary': 'key-1', 'backup': 'key-2'}), \
                patch.object(meshy, 'api_request', side_effect=api) as request:
            self.assertEqual(self.submit()['account'], 'backup')
            self.assertEqual(request.call_args.args[3], 'backup')
            balances['backup'] = 0
            rig = meshy.submit(self.project, workspace.DEFAULT_STATE, self.lease['token'], 'rig_v1', 'rigging',
                               'rig.json', 5)
            self.assertEqual(rig['account'], 'backup')
            meshy.poll(self.project, workspace.DEFAULT_STATE, self.lease['token'], 'rig_v1')
            self.assertEqual(request.call_args.kwargs['account'], 'backup')
            with self.assertRaises(RuntimeError):
                self.submit('body_v2')
        jobs = workspace.read_json(self.project / workspace.DEFAULT_STATE)['meshy']['jobs']
        self.assertNotIn('body_v2', jobs)


if __name__ == '__main__':
    unittest.main()
