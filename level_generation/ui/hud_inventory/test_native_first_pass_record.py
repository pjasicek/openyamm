"""Native first-pass import retains evidence without bypassing acceptance dependencies."""
import json
from pathlib import Path
import tempfile
import unittest
from PIL import Image
from review_dense_sheet import queue_module as module


class NativeFirstPassRecord(unittest.TestCase):
    def test_retained_return_does_not_grant_acceptance(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            q = module.Queue.__new__(module.Queue)
            q.payload_root = root / 'payloads'
            folder = q.payload_root / 'execution'
            folder.mkdir(parents=True)
            q.state_path = root / 'state.json'
            q.state = dict(attempts=[], claims={})
            source = root / 'source.png'
            Image.new('RGBA', (4, 4), 'red').save(source)
            member = dict(id='cell', target='target', source_path=str(source), export_region=[0, 0, 8, 8])
            q.members = {'cell': ('job', member)}
            q.jobs = dict(job=dict(members=[member], dependencies=[dict(job='seed')]),
                          seed=dict(members=[dict(id='seed-cell')]))
            q.accepted = lambda cell: False
            payload = dict(job='job', jobs=['job'], selected_cells=['cell'],
                           dependency_policy='user_authorized_native_first_pass_review_later',
                           external_return=dict(sheet='test'), unresolved_acceptance_dependencies=['seed-cell'],
                           source_hashes={'cell': module.digest(source)},
                           reference_hashes={str(source): module.digest(source)}, prompt='Original submitted prompt')
            (folder / 'payload.json').write_text(json.dumps(payload))
            result = q.record('execution', source)
            self.assertEqual(len(q.state['attempts']), 1)
            self.assertTrue(Path(result['retained_raw']).is_file())
            retained = json.loads(Path(q.state['attempts'][0]['payload']).read_text())
            self.assertEqual(retained['prompt'], payload['prompt'])
            self.assertEqual(retained['unresolved_acceptance_dependencies'], ['seed-cell'])
            with self.assertRaisesRegex(AssertionError, 'Dependencies not accepted'):
                q.accept('cell', source, {}, result['attempt'])
            Image.new('RGBA', (4, 4), 'blue').save(source)
            with self.assertRaisesRegex(AssertionError, 'Submitted source changed'):
                q.record('execution', source)
            self.assertEqual(len(q.state['attempts']), 1)


if __name__ == '__main__':
    unittest.main()
