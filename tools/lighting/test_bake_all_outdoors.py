import contextlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import bake_all_outdoors as batch


class BatchBakeTests(unittest.TestCase):
    def test_scope_failure_isolation_and_installation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profiles = root / 'profiles'
            profiles.mkdir()
            (profiles / 'mm6_oute3.yml').write_text(json.dumps(dict(samples=64, sky_energy=0.35)))
            (profiles / 'mm7_c.yml').write_text(json.dumps(dict(samples=64, sky_energy=0.35, azimuth=315)))
            for world, name in [('mm6', 'a.odm'), ('mm6', 'b.odm'), ('mm7', 'c.odm'), ('mm8', 'd.odm'),
                                ('mm9', 'e.odm'), ('mm6', 'indoor.blv')]:
                source = root / 'assets_dev/worlds' / world / 'maps' / name
                source.parent.mkdir(parents=True, exist_ok=True)
                source.touch()
                if name == 'a.odm':
                    source.with_suffix('.lighting').write_text('original lighting')
                    source.with_suffix('.bake.json').write_text('original recipe')
            baked = []

            def producer(command, **kwargs):
                profile = json.loads(Path(command[command.index('--profile') + 1]).read_text())
                baked.append((profile['world'], profile['map']))
                output = Path(command[command.index('--output') + 1])
                stem = Path(profile['map']).stem
                (output / f'{stem}.bake.json').write_text('new recipe')
                if profile['map'] == 'a.odm':
                    # Producer failure after emitting a recipe must not corrupt the installed pair.
                    return subprocess.CompletedProcess(command, 1)
                (output / f'{stem}.lighting').write_text('new lighting')
                self.assertEqual(profile['samples'], 16)
                self.assertEqual(profile['sky_energy'], 0.35)
                self.assertEqual(profile['azimuth'], 225)
                return subprocess.CompletedProcess(command, 0)

            output = root / 'output'
            with patch.object(batch, 'ROOT', root), patch.object(batch, 'PROFILES', profiles), \
                    patch.object(batch.shutil, 'which', return_value='/fake/blender'), \
                    patch.object(batch.subprocess, 'run', side_effect=producer), \
                    patch('sys.argv', ['batch', '--output', str(output), '--samples', '16',
                                       '--azimuth', '225', '--install']), \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(batch.main(), 1)
            self.assertEqual(baked, [('mm6', 'a.odm'), ('mm6', 'b.odm'), ('mm7', 'c.odm'), ('mm8', 'd.odm')])
            failed = root / 'assets_dev/worlds/mm6/maps/a'
            self.assertEqual(failed.with_suffix('.lighting').read_text(), 'original lighting')
            self.assertEqual(failed.with_suffix('.bake.json').read_text(), 'original recipe')
            for world, name in baked[1:]:
                installed = root / 'assets_dev/worlds' / world / 'maps' / name
                self.assertEqual(installed.with_suffix('.lighting').read_text(), 'new lighting')
                self.assertEqual(installed.with_suffix('.bake.json').read_text(), 'new recipe')
            report = json.loads((output / 'batch-report.json').read_text())
            self.assertEqual([r['status'] for r in report['results']], ['failed', 'installed', 'installed', 'installed'])

            original_report = (output / 'batch-report.json').read_bytes()
            baked.clear()
            retry_output = root / 'retry'
            with patch.object(batch, 'ROOT', root), patch.object(batch, 'PROFILES', profiles), \
                    patch.object(batch.shutil, 'which', return_value='/fake/blender'), \
                    patch.object(batch.subprocess, 'run', side_effect=producer), \
                    patch('sys.argv', ['batch', '--output', str(retry_output), '--retry-failed',
                                       str(output / 'batch-report.json'), '--install']), \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(batch.main(), 1)
            self.assertEqual(baked, [('mm6', 'a.odm')])
            self.assertEqual((output / 'batch-report.json').read_bytes(), original_report)
            retry = json.loads((retry_output / 'retry-report.json').read_text())
            self.assertEqual(len(retry['results']), 1)
            self.assertEqual(retry['results'][0]['map'], 'mm6/a.odm')

    def test_dry_run_does_not_launch_blender_or_create_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'unused'
            with patch('sys.argv', ['batch', '--output', str(output), '--world', 'mm7', '--dry-run']), \
                    patch.object(batch.subprocess, 'run') as run, contextlib.redirect_stdout(io.StringIO()) as log:
                self.assertEqual(batch.main(), 0)
            run.assert_not_called()
            self.assertFalse(output.exists())
            self.assertIn('worlds/mm7/maps/', log.getvalue())
            self.assertNotIn('worlds/mm6/maps/', log.getvalue())
            self.assertNotIn('worlds/mm8/maps/', log.getvalue())


if __name__ == '__main__':
    unittest.main()
