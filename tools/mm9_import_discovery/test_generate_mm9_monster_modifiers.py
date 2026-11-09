#!/usr/bin/env python3
from __future__ import annotations

import unittest

from generate_mm9_monster_modifiers import REPOSITORY, duration_minutes, projectile_blasts

PROJECTILE_TABLE = REPOSITORY / 'mm9' / 'extracted' / 'DATA' / 'DATA' / 'PROJECTILE.txt'


class DurationMinutesTest(unittest.TestCase):
    """SPELL.txt's duration cells (game minutes) for a cast's skills e1 and e2."""

    def test_per_point_cells(self):
        self.assertEqual(duration_minutes('1 minute per point in e1', 10, 1), 10.0)
        self.assertEqual(duration_minutes('1 per point in e2', 12, 3), 3.0)
        self.assertEqual(duration_minutes('5 minutes per point of e1', 4, 1), 20.0)
        self.assertEqual(duration_minutes('10 minutes per point in e1 ', 10, 4), 100.0)

    def test_plain_and_empty_cells(self):
        self.assertEqual(duration_minutes('30', 5, 1), 30.0)
        self.assertEqual(duration_minutes('0', 5, 1), 0.0)
        self.assertEqual(duration_minutes('', 5, 1), 0.0)
        self.assertEqual(duration_minutes('n/a', 5, 1), 0.0)


@unittest.skipUnless(PROJECTILE_TABLE.is_file(), 'needs mm9/extracted')
class ProjectileBlastsTest(unittest.TestCase):
    """PROJECTILE.txt's damageRadius in our units: feet x 12 LT x 2.56; projectiles without one are left out."""

    def test_blasts(self):
        blasts = projectile_blasts(PROJECTILE_TABLE)
        self.assertEqual(blasts['dragonfirebolt'], 768.0)
        self.assertEqual(blasts['dragonbreath2'], 921.6)
        self.assertEqual(blasts['redyellowthingy'], 307.2)
        self.assertNotIn('arrow', blasts)


if __name__ == '__main__':
    unittest.main()
