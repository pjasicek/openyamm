"""Focused packing and raw-return contract checks; fixtures are not generated artwork."""
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from PIL import Image

from dense_bundles import grid_for, save, sha
from catalogue_dense_returns import catalogue


class DenseContracts(unittest.TestCase):
    def test_portrait_budget_and_large_icon_limit(self):
        grid = grid_for(64, 59, 79)
        self.assertEqual(grid['reference_size'], [1008, 1328])
        self.assertGreaterEqual(grid['predicted_sampling'], 2.15)
        self.assertIsNone(grid_for(64, 128, 128))
        skinny = grid_for(1, 1, 256)
        self.assertGreaterEqual(skinny['reference_size'][0]/skinny['reference_size'][1], .5)

    def fixture(self, root, size=(40, 60), extra=None, altered_manifest=False):
        batch = root/'batch'
        folder = batch/'test'
        save(folder/'layout.json', {'cells':[dict(id='cell', source_sha256='original',
            native_size=[20, 30], x2_size=[40, 60], reference_rect=[0, 0, 40, 60])]})
        prompt = b'Test prompt, no actual generation.'
        (folder/'prompt.txt').write_bytes(prompt)
        manifest = dict(bundle_id='test', sheets=[dict(id='S001', cells=['cell'],
            layout='layout.json', layout_sha256=sha(folder/'layout.json'),
            reference_size=[40, 60], prompt_sha256=sha(folder/'prompt.txt')),
            dict(id='S002', cells=['missing'])])
        save(folder/'manifest.json', manifest)
        save(batch/'catalogue.json', {'bundles':[dict(bundle_id='test', manifest='test/manifest.json',
            manifest_sha256=sha(folder/'manifest.json'))]})
        progress = dict(bundle='test', sheets={'S001':dict(raw_path='outputs/raw/S001.png',
            submitted_prompt_path='outputs/prompts/S001.txt', actual_dimensions=list(size))})
        raw = io.BytesIO()
        Image.new('RGB', size, '#555555').save(raw, format='PNG')
        archive = root/'return.zip'
        with zipfile.ZipFile(archive, 'w') as z:
            data = (folder/'manifest.json').read_bytes()
            z.writestr('manifest.json', data+b' ' if altered_manifest else data)
            z.writestr('outputs/progress.json', json.dumps(progress))
            z.writestr('outputs/raw/S001.png', raw.getvalue())
            z.writestr('outputs/prompts/S001.txt', prompt)
            if extra:
                z.writestr(extra, 'bad')
        return batch, archive

    def test_partial_return_is_retained_idempotently_without_acceptance(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            batch, archive = self.fixture(root)
            dest, report = catalogue(batch, archive, root/'out')
            dest2, report2 = catalogue(batch, archive, root/'out')
            self.assertEqual((dest, report), (dest2, report2))
            self.assertEqual(report['accepted'], 0)
            self.assertEqual(report['sheets'][0]['status'], 'needs_cell_sampling_and_visual_review')
            self.assertEqual(report['cells'][1]['status'], 'unreturned')
            self.assertEqual(sha(dest/'return.zip'), sha(archive))
            self.assertTrue((dest/'index.html').exists())

    def test_undersized_return_is_flagged(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            batch, archive = self.fixture(root, size=(20, 30))
            _, report = catalogue(batch, archive, root/'out')
            self.assertEqual(report['sheets'][0]['status'], 'size_or_aspect_warning')
            self.assertEqual(report['sheets'][0]['nominal_sampling_only'], 1)

    def test_changed_manifest_and_path_traversal_are_rejected(self):
        for options in ({'altered_manifest':True}, {'extra':'../escaped.txt'}):
            with self.subTest(options=options), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                batch, archive = self.fixture(root, **options)
                with self.assertRaises((ValueError, AssertionError)):
                    catalogue(batch, archive, root/'out')
                self.assertFalse((root/'escaped.txt').exists())


if __name__ == '__main__':
    unittest.main()
