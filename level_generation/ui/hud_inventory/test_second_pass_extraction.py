"""Provisional visual diagnostics must not become verified geometry evidence."""
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
import unittest

from PIL import Image
import second_pass


class ExtractionTests(unittest.TestCase):
    def test_provisional_crop_keeps_coordinates_but_no_sampling_claim(self):
        with TemporaryDirectory(prefix='second-pass-extraction-') as temporary:
            directory = Path(temporary)
            raw = directory / 'raw.png'
            Image.new('RGBA', (48, 48), (30, 60, 90, 255)).save(raw)
            member = dict(target='target', source_rect=[0, 0, 8, 8], export_region=[0, 0, 16, 16],
                          source_sha256='native-test-hash')
            queue = SimpleNamespace(members={'cell': ('job', member)}, targets={'target': {}})
            second_pass.save(directory / 'current.json', {'snapshot': str(directory / 'snapshot')})
            second_pass.save(directory / 'snapshot/masters.json', {'attempt': dict(
                selected_cells=['cell'], raw=str(raw), raw_sha256=second_pass.digest(raw))})
            with patch.object(second_pass, 'OUT', directory), \
                    patch.object(second_pass.registration, 'evidence'), \
                    patch.object(second_pass.registration, 'images', return_value=[]):
                second_pass.extract('cell', 'attempt', [4, 4, 32, 32], queue=queue,
                                    provisional_reason='Canvas origin is unresolved.')
            output = directory / 'evidence/cell/attempt'
            record = second_pass.read(output / 'processing.json')
            self.assertIsNone(record['actual_sampling'])
            self.assertIsNone(record['raw_rect'])
            self.assertEqual(record['provisional_raw_rect'], [4, 4, 32, 32])
            self.assertFalse(record['visual_approval'])
            self.assertEqual(record['extraction_status'], 'Canvas origin is unresolved.')
            with Image.open(output / 'candidate.png') as candidate:
                self.assertEqual(candidate.size, (16, 16))


if __name__ == '__main__':
    unittest.main()
