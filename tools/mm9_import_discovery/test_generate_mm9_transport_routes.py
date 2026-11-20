#!/usr/bin/env python3
from __future__ import annotations

import unittest
from pathlib import Path

from generate_mm9_transport_routes import generate, load_boat_schedule


ROOT = Path(__file__).resolve().parents[2]


class GenerateMm9TransportRoutesTests(unittest.TestCase):
    def test_source_boat_schedule_is_parsed_by_named_weekday(self) -> None:
        schedule = load_boat_schedule(ROOT / "mm9/extracted/DATA/DATA/BOOK AND SCROLL TEXT.csv")

        self.assertEqual(schedule["Thjorgard"]["Monday"], "Sturmford")
        self.assertEqual(schedule["Guberland"]["Tuesday"], "Isle of Ashes")
        self.assertIsNone(schedule["Lindisfarne"]["Thursday"])

    def test_reviewed_executable_recovery_covers_every_service(self) -> None:
        records, audit = generate(
            ROOT / "mm9/extracted/DATA/DATA/MMIXSHOPS.txt",
            ROOT / "mm9/extracted/RUDE/RUDE",
            ROOT / "mm9/extracted/DATA/DATA/BOOK AND SCROLL TEXT.csv",
            ROOT / "assets_editor_dev/worlds/mm9/maps",
            ROOT / "tools/mm9_import_discovery/mm9_transport_route_recovery.yml",
        )

        self.assertEqual(len(records), 47)
        self.assertEqual(audit["summary"]["dock_count"], 7)
        self.assertEqual(audit["summary"]["rude_service_count"], 8)
        self.assertEqual(audit["summary"]["error_count"], 0)
        routes = {record["CanonicalId"]: record for record in records}
        self.assertEqual(routes["mm9:transport/18/monday"]["TravelDays"], 2)
        self.assertEqual(routes["mm9:transport/18/wednesday"]["RequiredRawKeys"], "73")
        self.assertEqual(routes["mm9:transport/209/monday"]["RequiredRawKeys"], "73")
        self.assertEqual(routes["mm9:transport/138/tuesday"]["ServiceClassification"], "special_passage")
        self.assertEqual(routes["mm9:transport/138/tuesday"]["ForbiddenRawKeys"], "5017")


if __name__ == "__main__":
    unittest.main()
