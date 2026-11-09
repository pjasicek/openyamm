"""Fixtures for the kit's shapes (blv_kit.py), run in Blender's Python (the kit needs bpy):
    blender --background --factory-startup --python-exit-code 1 --python test_blv_kit.py
Each new flight, ramp, tier and polygon room is also handed to the walkability audit (check_walkability.py), so the
kit's shapes are ones monsters walk."""
import math
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import blv_kit as kit
import check_walkability as audit


def faces(panels):
    """Kit panels as the audit's faces (the kit's `inward` is the face's normal side)."""
    return [audit.Face([tuple(p) for p in panel[0]], tuple(panel[2])) for panel in panels]


def walk(panels, start, ceiling=1024):
    """The audit's findings over panels inside an open box with a ceiling over everything."""
    xs = [p[0] for panel in panels for p in panel[0]]
    ys = [p[1] for panel in panels for p in panel[0]]
    lid = kit.ceiling(min(xs) - 64, min(ys) - 64, max(xs) + 64, max(ys) + 64, ceiling, 'trim')
    findings, _ = audit.analyse(audit.Level('kit', faces(panels + lid), start))
    return findings


class Shapes(unittest.TestCase):
    def test_footprints(self):
        self.assertEqual(kit.chamfer_rect(0, 0, 100, 50, 10),
                         [(0, 10), (10, 0), (90, 0), (100, 10), (100, 40), (90, 50), (10, 50), (0, 40)])
        self.assertEqual(len(kit.chamfer_rect(0, 0, 100, 50, {'ne': 20})), 5)
        octagon = kit.ngon(0, 0, 100, 8)
        self.assertTrue(kit._ccw(octagon))
        # The default phase puts a flat side on each axis.
        self.assertAlmostEqual(max(x for x, _ in octagon), 100 * math.cos(math.pi / 8))
        # An L footprint splits into convex pieces that cover it.
        ell = [(0, 0), (300, 0), (300, 100), (100, 100), (100, 300), (0, 300)]
        pieces = kit.convex_pieces(ell)
        self.assertEqual(len(pieces), 2)
        area = sum(abs(sum(ax * by - bx * ay for (ax, ay), (bx, by) in zip(p, p[1:] + p[:1]))) / 2 for p in pieces)
        self.assertAlmostEqual(area, 300 * 100 + 100 * 200)

    def test_wall_line(self):
        wall = kit.Wall.line((0, 0), (300, 300))
        self.assertAlmostEqual(wall.length, 300 * math.sqrt(2))
        p = wall.point(wall.length / 2, 10, out=math.sqrt(2))
        self.assertAlmostEqual((p.x, p.y, p.z), (149, 151, 10), places=4)
        back = wall.offset(64)
        self.assertAlmostEqual((back.point(0, 0) - wall.point(0, 0)).length, 64, places=4)
        # An axis wall's offset is the one recessed_door always made.
        axis = kit.Wall('y', 100, (0, 1, 0)).offset(16)
        self.assertEqual((axis.axis, axis.plane), ('y', 84))
        quads = kit.banded(wall, 0, wall.length, [(0, 64, 'trim'), (64, 256, 'floor')], [(100, 200, 0, 128)])
        self.assertEqual(len(quads), 5)

    def test_monster_safe_shapes(self):
        self.assertTrue(kit.monster_safe(24, 48))
        self.assertTrue(kit.monster_safe(16, 20))
        self.assertFalse(kit.monster_safe(32, 24))
        self.assertFalse(kit.monster_safe(24, 32))
        with self.assertRaises(ValueError):
            kit.flight_along((0, 0), (96, 0), 200, 0, 4, rise=32)
        with self.assertRaises(ValueError):
            kit.ramp_along((0, 0), (100, 0), 200, 0, 120)

    def test_kit_shapes_walk(self):
        room = kit.polygon_floor(kit.chamfer_rect(0, 0, 2400, 1600, 300), 0, 'floor')
        # A diagonal flight onto a chamfered dais, with balustrades: no findings.
        dais = kit.box((1500, 900, 0), (2000, 1400, 96), 'trim', top='floor')
        rail = [kit.box((1500, 900, 96), (2000, 916, 160), 'trim')[0]]
        stairs = kit.flight_along((1250, 1150), (1500, 1150), 300, 0, 4, rise=24)
        findings = walk(room + dais + stairs, (300, 300, 0))
        self.assertEqual({f['kind'] for f in findings} - {'step'}, set())
        # A ramp up to a 128 platform reaches it; without the ramp the platform's 128 edge is a wall.
        platform = kit.box((1600, 400, 0), (2200, 1000, 128), 'trim', top='floor')
        up = kit.ramp(1300, 500, 1600, 900, 0, 128, 'east', skirt='trim')
        self.assertEqual(walk(room + platform + up, (300, 300, 0)), [])
        self.assertEqual(walk(room + platform, (300, 300, 0)), [])
        # Concentric tiers: a dais of 24 risers on 48 treads, and a pit of the same, both walk.
        floor = kit.polygon_floor(kit.ngon(0, 0, 1600, 16), 0, 'floor')
        tiers = kit.ring_flight(0, 0, [800, 750, 700, 650], 0, 24, sides=16, cap='floor')
        self.assertEqual(walk(floor + tiers, (-1200, 0, 0)), [])
        ring = [p for p in floor]
        pit = kit.ring_flight(0, 0, [800, 750, 700, 650], 0, -24, sides=16, cap='floor')
        hole = kit.convex_pieces(kit.ngon(0, 0, 800, 16))
        outer = [panel for panel in kit.polygon_floor(kit.ngon(0, 0, 1600, 16), 0, 'floor')]
        self.assertTrue(hole and outer and ring)
        # A sunken centre without tiers (a 96 drop) is a pit.
        sunk = kit.ring_flight(0, 0, [800], 0, -96, sides=16, cap='floor')
        annulus = []
        big, small = kit.ngon(0, 0, 1600, 16), kit.ngon(0, 0, 800, 16)
        for j in range(16):
            annulus += kit.polygon_floor([big[j], big[(j + 1) % 16], small[(j + 1) % 16], small[j]], 0, 'floor')
        self.assertIn('pit', {f['kind'] for f in walk(annulus + sunk, (-1200, 0, 0))})
        self.assertEqual(walk(annulus + pit, (-1200, 0, 0)), [])

    def test_clipping_and_chamfered_walls(self):
        footprint = kit.chamfer_rect(0, 0, 1000, 800, 200)
        # A floor laid across the whole rectangle loses its corners.
        cut = kit.clip_to(kit.floor(0, 0, 1000, 800, 0, 'floor'), footprint)
        self.assertEqual(len(cut[0][0]), 8)
        # A wall under a ceiling sloping from 600 at x 0 to 300 at x 1000 keeps only what lies below it.
        slope = ((0, 0, 600), (300, 0, 1000))
        wall = kit.Wall('y', 0, (0, 1, 0)).quad(0, 1000, 0, 800, 'trim')
        kept = kit.clip_to(wall, None, below=slope)[0][0]
        self.assertAlmostEqual(max(p.z for p in kept if p.x < 1), 600)
        self.assertAlmostEqual(max(p.z for p in kept if p.x > 999), 300)
        walls = kit.rect_walls(0, 0, 1000, 800, [(0, 512, 'trim')], {'south': [(400, 600, 0, 384)]},
                               chamfer={'ne': 200, 'sw': 150})
        diagonals = [w for w in walls if abs(w[2][0]) > 0.1 and abs(w[2][1]) > 0.1]
        self.assertEqual(len(diagonals), 2)
        # The south side runs from the south-west cut and keeps its hole.
        south = [w for w in walls if w[2] == (0, 1, 0)]
        self.assertEqual(sorted(round(min(p.x for p in w[0])) for w in south), [150, 400, 600])
        ramp = kit.ramp(0, 0, 256, 300, 0, 128, 'east', rail=48)
        self.assertEqual(len(ramp), 3)

    def test_ceilings(self):
        hip = kit.hip_ceiling(kit.ngon(0, 0, 500, 8), 512, 768, 'trim', top=0.4)
        self.assertEqual(len(hip), 9)
        self.assertTrue(all(kit._down(p[0])[2] < 0 for p in hip))
        pyramid = kit.hip_ceiling(kit.chamfer_rect(0, 0, 400, 400, 50), 300, 500, 'trim', top=0)
        self.assertEqual(len(pyramid), 8)
        barrel = kit.vault(0, 0, 1000, 400, 512, 200, 'x', 'trim', segments=6, ends='trim')
        self.assertEqual(len(barrel), 8)
        crown = max(p[2] for panel in barrel for p in panel[0])
        self.assertAlmostEqual(crown, 712)

    def test_poly_room_and_room_at(self):
        with tempfile.TemporaryDirectory() as folder:
            b = kit.Builder('hes_test.blv', {'floor': 'hcfloor', 'trim': 'hcfloor', 'ceiling': 'hcceiling', 'marker': 'hcfloor'},
                            folder, decoration_ids={})
            octagon = kit.ngon(0, 0, 1000, 8)
            panels = b.poly_room('round', octagon, 0, 512, [(0, 64, 'trim'), (64, 512, 'floor')],
                                 holes={0: [(200, 500, 0, 384)]}, ceiling_role=None)
            b.rooms['round'] += kit.hip_ceiling(octagon, 512, 768, 'trim')
            b.box_room('box', 1200, -200, 2000, 200, 0, 512, [(0, 512, 'floor')])
            far = b.opening_line('round', 'box', b.edge_wall('round', 0), 200, 500, 0, 384)
            self.assertEqual(len(b.portals), 1)
            self.assertTrue(far.point(0, 0).x > b.edge_wall('round', 0).point(0, 0).x)
            # The octagon's bounds reach (900, 900); its footprint does not.
            self.assertEqual(b.room_at(0, 0, 10), 'round')
            with self.assertRaises(ValueError):
                b.room_at(900, 900, 10)
            self.assertGreater(len(panels), 8)
            with self.assertRaises(ValueError):
                b.poly_room('cw', list(reversed(octagon)), 0, 512, [(0, 512, 'floor')])
            panels = b.box_room('cut', 3000, 0, 4000, 800, 0, 512, [(0, 512, 'floor')], chamfer=200)
            self.assertEqual(b.room_at(3500, 400, 10), 'cut')
            self.assertEqual(len(panels[0][0]), 8)


if __name__ == '__main__':
    result = unittest.main(argv=['test_blv_kit'], exit=False).result
    sys.exit(0 if result.wasSuccessful() else 1)
