"""An explicit review collection must never pick up another generation or changed pixels."""

import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import serve


class CollectionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        package = self.root / 'selected'
        package.mkdir()
        self.manifest = {'creature': 'mm6:test', 'pixels_per_logical_pixel': 2, 'frames': {'a': {}}}
        raw = json.dumps(self.manifest).encode()
        (package / 'manifest.json').write_bytes(raw)
        self.record = dict(creature='mm6:test', label='Selected', manifest='selected/manifest.json',
                           manifest_sha256=hashlib.sha256(raw).hexdigest(), artifact_sha256='selected-pixels',
                           frame_count=1, source='Packed outline', pipeline_status='manual_review_pending')
        self.collection = dict(schema_version=1, collection_id='test', title='Selected collection',
                               family_count=1, frame_count=1, pixels_per_logical_pixel=2, families=[self.record])
        self.path = self.root / 'collection.json'
        self.family = SimpleNamespace(manifest=self.manifest, artifact_sha256='selected-pixels')

    def write(self):
        self.path.write_text(json.dumps(self.collection))

    def test_explicit_selection_resolves_relative_to_collection_and_ignores_discovery(self):
        self.write()
        with patch.object(serve, 'load_family', return_value=self.family) as loader, \
                patch.object(serve, 'build_queue', side_effect=AssertionError('Historical queue consulted')):
            families, metadata = serve.load_collection(self.path)
        self.assertEqual(families, [self.family])
        self.assertEqual(metadata['collection_id'], 'test')
        self.assertEqual(loader.call_args.args[1], self.root / 'selected/manifest.json')

    def test_changed_manifest_is_rejected_before_loading_pixels(self):
        self.write()
        (self.root / self.record['manifest']).write_text('{}')
        with patch.object(serve, 'load_family') as loader, self.assertRaisesRegex(ValueError, 'manifest changed'):
            serve.load_collection(self.path)
        loader.assert_not_called()

    def test_changed_atlas_pixels_are_rejected(self):
        self.write()
        self.family.artifact_sha256 = 'different-generation'
        with patch.object(serve, 'load_family', return_value=self.family), \
                self.assertRaisesRegex(ValueError, 'pixels changed'):
            serve.load_collection(self.path)

    def test_duplicate_family_and_partial_coverage_are_rejected(self):
        self.collection['families'].append(dict(self.record))
        self.write()
        with self.assertRaisesRegex(ValueError, 'Duplicate creature'):
            serve.load_collection(self.path)
        self.collection['families'].pop()
        self.record['frame_count'] = 2
        self.write()
        with self.assertRaisesRegex(ValueError, 'coverage'):
            serve.load_collection(self.path)


if __name__ == '__main__':
    unittest.main()
