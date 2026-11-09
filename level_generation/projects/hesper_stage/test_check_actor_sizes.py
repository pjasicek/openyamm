"""Fixtures for the actor-size audit; only temporary files are written."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import check_actor_sizes as audit


class ActorSizeChecks(unittest.TestCase):
    def test_indoor_outdoor_sizes_and_descriptor_precedence(self):
        with tempfile.TemporaryDirectory() as folder:
            assets = Path(folder)
            maps = assets / 'worlds/hesper/maps'
            maps.mkdir(parents=True)
            world, engine = assets / 'world.txt', assets / 'engine.txt'
            world.write_text('ID\tName\tHeight\tRadius\n10142\tCell\t300\t110\n')
            engine.write_text('10142\tOld cell\t160\t60\n1\tNative\t100\t40\n')
            actor = dict(actor_index=0, name='Cell', monster_info_id=10142, height=300, radius=110)
            indoor = maps / 'hes_d16.scene.yml'
            outdoor = maps / 'hes_out4.scene.yml'
            (maps / 'hes_d16.blv').touch()
            (maps / 'hes_out4.odm').touch()
            indoor.write_text(json.dumps({'initial_state': {'actors': [actor]}}))
            outdoor.write_text(json.dumps({'initial_state': {'actors': [
                dict(actor_index=0, name='Native', monster_info_id=1, height=100, radius=40)]}}))
            with patch.object(audit, 'ASSETS', assets), patch.object(audit, 'TABLES', [world, engine]):
                output = io.StringIO()
                with redirect_stdout(output):
                    self.assertEqual(audit.audit(), 0)
                self.assertIn('TOTAL: maps=2, actors=2, mismatches=0', output.getvalue())
                for change, expected in [({'height': 160}, 'row Cell height 300 radius 110'),
                                         ({'radius': 60}, 'row Cell height 300 radius 110'),
                                         ({'monster_info_id': 999}, 'no monster row')]:
                    with self.subTest(change=change):
                        indoor.write_text(json.dumps({'initial_state': {'actors': [actor | change]}}))
                        output = io.StringIO()
                        with redirect_stdout(output):
                            self.assertEqual(audit.audit(), 1)
                        self.assertIn('TOTAL: maps=2, actors=2, mismatches=1', output.getvalue())
                        self.assertIn(expected, output.getvalue())
                indoor.unlink()
                output = io.StringIO()
                with redirect_stdout(output):
                    self.assertEqual(audit.audit(), 1)
                self.assertIn('hes_d16: ERROR:', output.getvalue())


if __name__ == '__main__':
    unittest.main()
