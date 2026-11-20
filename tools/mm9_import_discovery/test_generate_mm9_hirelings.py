#!/usr/bin/env python3

from __future__ import annotations

import csv
import io
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import generate_mm9_hirelings as hirelings  # noqa: E402


def table_text(rows: list[list[str]]) -> str:
    output = io.StringIO()
    csv.writer(output, delimiter="\t", lineterminator="\n").writerows(rows)
    return output.getvalue()


@unittest.skipUnless(hirelings.MONSTERS_TXT.is_file(), "MM9 MONSTERS.txt is not extracted")
class GenerateMm9HirelingsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = hirelings.generate(hirelings.MONSTERS_TXT)
        cls.header = cls.rows[0]
        cls.by_id = {int(row[0]): dict(zip(cls.header, row)) for row in cls.rows[1:]}

    def test_fifteen_hirelings_thirteen_paid_two_story(self) -> None:
        self.assertEqual(tuple(self.header), hirelings.COLUMNS)
        self.assertEqual(len(self.by_id), 15)
        kinds = [row["kind"] for row in self.by_id.values()]
        self.assertEqual(kinds.count("paid"), 13)
        self.assertEqual(kinds.count("story"), 2)
        self.assertEqual(self.by_id[2]["kind"], "story")
        self.assertEqual(self.by_id[309]["kind"], "story")

    def test_casters_spells(self) -> None:
        arienh = self.by_id[44]
        self.assertEqual(arienh["spell1"], "Fireball,E,6")
        self.assertEqual(arienh["spell2"], "Toxic Cloud,M,7")
        self.assertEqual(arienh["spell1_share_percent"], "60")
        ake = self.by_id[86]
        self.assertEqual(ake["spell1"], "Sparks,E,3")
        self.assertEqual(ake["spell2"], "Lightning Bolt,N,2")
        self.assertEqual(ake["spell1_share_percent"], "60")

    def test_archers_shoot_arrows_as_attack_2(self) -> None:
        archers = sorted(rude for rude, row in self.by_id.items() if row["attack2_missile"] == "Arrow")
        self.assertEqual(archers, [42, 43, 85])
        for rude in archers:
            self.assertNotEqual(self.by_id[rude]["attack2_damage"], "0")

    def test_paid_hire_qbits(self) -> None:
        paid = [row for row in self.by_id.values() if row["kind"] == "paid"]
        self.assertEqual(sorted(int(row["hire_qbit"]) for row in paid), list(range(90450, 90463)))

    def test_checked_in_table_matches_generation(self) -> None:
        self.assertTrue(hirelings.OUTPUT.is_file())
        self.assertEqual(hirelings.OUTPUT.read_text(encoding="utf-8"), table_text(self.rows))


if __name__ == "__main__":
    unittest.main()
