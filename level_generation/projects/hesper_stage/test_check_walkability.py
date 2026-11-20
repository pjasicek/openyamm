"""Fixtures for the walkability audit: small levels built from faces; nothing is read from the stage."""
import unittest

import check_walkability as audit
from check_walkability import Face, Level


def floor(x0, y0, x1, y1, z):
    return Face([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], (0, 0, 1))


def ceiling(x0, y0, x1, y1, z):
    return Face([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], (0, 0, -1))


def wall(x0, y0, x1, y1, z0, z1):
    return Face([(x0, y0, z0), (x1, y1, z0), (x1, y1, z1), (x0, y0, z1)], (y1 - y0, x0 - x1, 0))


def box(x0, y0, x1, y1, z0, z1, top=True):
    faces = [wall(x0, y0, x1, y0, z0, z1), wall(x1, y0, x1, y1, z0, z1), wall(x1, y1, x0, y1, z0, z1),
             wall(x0, y1, x0, y0, z0, z1)]
    return faces + ([floor(x0, y0, x1, y1, z1)] if top else [])


def room(x0, y0, x1, y1, z=0, height=512):
    """A closed room: floor, ceiling and four walls."""
    return [floor(x0, y0, x1, y1, z), ceiling(x0, y0, x1, y1, z + height)] + box(x0, y0, x1, y1, z, z + height,
                                                                                  top=False)


def flight(x0, y0, x1, y1, z0, steps, rise, west=False):
    """Treads climbing east (or west), with their risers."""
    faces, run = [], (x1 - x0) / steps
    for k in range(steps):
        a = x1 - run * (k + 1) if west else x0 + run * k
        riser = a + run if west else a
        faces += [floor(a, y0, a + run, y1, z0 + rise * (k + 1)),
                  wall(riser, y0, riser, y1, z0 + rise * k, z0 + rise * (k + 1))]
    return faces


def level(faces, actors=(), movers=None, start=(200, 200, 0)):
    return Level('fixture', faces, start, actors, movers)


def kinds(findings, allowed=False):
    return sorted(f['kind'] for f in findings if ('allowed' in f) == allowed)


class Walkability(unittest.TestCase):
    def test_flat_room_and_low_step(self):
        findings, _ = audit.analyse(level(room(0, 0, 2000, 1000)))
        self.assertEqual(findings, [])
        # A 32 dais is fine everywhere.
        findings, _ = audit.analyse(level(room(0, 0, 2000, 1000) + box(800, 300, 1400, 700, 0, 32)))
        self.assertEqual(findings, [])

    def test_platform_reached_by_stairs_or_not(self):
        base = room(0, 0, 2000, 1000) + box(1000, 200, 1600, 800, 0, 96)
        findings, _ = audit.analyse(level(base))
        self.assertEqual(kinds(findings), ['unreachable'])
        self.assertEqual(findings[0]['rise'], 96)
        # A flight of 24 risers with 48 treads up its west side: the dais is reached, its sheer sides are steps.
        findings, _ = audit.analyse(level(base + flight(808, 200, 1000, 800, 0, 4, 24)))
        self.assertEqual(set(kinds(findings)), {'step'})
        self.assertIn(96, [f['rise'] for f in findings])
        # A ledge the party climbs (48) is a step even with no way up for monsters.
        findings, _ = audit.analyse(level(room(0, 0, 2000, 1000) + box(1000, 200, 1600, 800, 0, 48)))
        self.assertIn('step', kinds(findings))
        self.assertIn('unreachable', kinds(findings))

    def test_short_treads_and_allowed_platform(self):
        # 32 risers on 24 treads: one 40-unit path step climbs two risers.
        faces = room(0, 0, 2000, 1000) + flight(800, 200, 896, 800, 0, 4, 32) + box(896, 200, 1600, 800, 0, 128)
        findings, _ = audit.analyse(level(faces))
        self.assertIn('flight', kinds(findings))
        allow = [dict(kind='unreachable', at=[1200, 500, 96], reason='a table')]
        findings, _ = audit.analyse(level(room(0, 0, 2000, 1000) + box(1000, 200, 1600, 800, 0, 96)), allow)
        self.assertEqual(kinds(findings, allowed=True), ['unreachable'])
        self.assertEqual(kinds(findings), [])
        self.assertTrue(allow[0].get('used'))

    def test_trench_pit_and_its_way_out(self):
        # A 64-deep trench across the room's middle: a pit.
        faces = [f for f in room(0, 0, 3000, 1000) if f.kind != 'floor']
        faces += [floor(0, 0, 1200, 1000, 0), floor(1800, 0, 3000, 1000, 0), floor(1200, 0, 1800, 1000, -64),
                  wall(1200, 0, 1200, 1000, -64, 0), wall(1800, 1000, 1800, 0, -64, 0)]
        findings, _ = audit.analyse(level(faces))
        self.assertIn('pit', kinds(findings))
        pit = next(f for f in findings if f['kind'] == 'pit')
        self.assertEqual(pit['exit_rise'], 64)
        # Two 32 risers on 48 treads up each side are the way out.
        stairs = flight(1704, 0, 1800, 1000, -64, 2, 32) + flight(1200, 0, 1296, 1000, -64, 2, 32, west=True)
        findings, _ = audit.analyse(level(faces + stairs))
        self.assertEqual(kinds(findings), [])
        # A 32-deep trench is no finding.
        shallow = [Face(f.points + (0, 0, 32) * (f.points[:, 2:] < 0), f.normal) for f in faces]
        findings, _ = audit.analyse(level(shallow))
        self.assertEqual(kinds(findings), [])

    def test_cut_off_room(self):
        # Two rooms joined by an opening whose floor drops 128 below both: the far room is cut off.
        faces = room(0, 0, 1000, 1000) + room(1064, 0, 2064, 1000)
        faces = [f for f in faces if not (f.kind == 'wall' and f.lo[0] in (1000, 1064) and f.hi[0] in (1000, 1064))]
        faces += [wall(1000, 0, 1000, 400, 0, 512), wall(1000, 600, 1000, 1000, 0, 512),
                  wall(1064, 0, 1064, 400, 0, 512), wall(1064, 600, 1064, 1000, 0, 512),
                  floor(1000, 400, 1064, 600, -128), wall(1000, 400, 1064, 400, -128, 512),
                  wall(1000, 600, 1064, 600, -128, 512)]
        findings, _ = audit.analyse(level(faces))
        self.assertEqual(kinds(findings), [])          # nothing lives there
        monster = dict(index=0, name='Drudge', x=1600, y=500, z=0, radius=60, height=180)
        findings, _ = audit.analyse(level(faces, [monster]))
        self.assertEqual(kinds(findings), ['unreachable'])
        self.assertEqual(findings[0]['actors'], [0])
        # A posted (immobile) monster need not walk anywhere.
        findings, _ = audit.analyse(level(faces, [dict(monster, immobile=True)]))
        self.assertEqual(kinds(findings), [])

    def test_mover_recess_and_flush(self):
        faces = room(0, 0, 2000, 1000)
        faces = [f for f in faces if f.kind != 'floor']
        faces += [floor(0, 0, 900, 1000, 0), floor(1100, 0, 2000, 1000, 0), floor(900, 0, 1100, 1000, -256)]

        def block(top):
            # A lowering block: its top at 384 closed, `top` when lowered.
            return {7: [[Face(f.points, f.normal, door=7, pose=p) for f in box(900, 0, 1100, 1000, z - 256, z)]
                        for p, z in enumerate((top, 384))]}
        findings, _ = audit.analyse(level(faces, movers=block(-16)))
        self.assertEqual(kinds(findings), ['mover'])
        self.assertEqual((findings[0]['pose'], findings[0]['rise']), ('open', 16))
        findings, _ = audit.analyse(level(faces, movers=block(0)))
        self.assertEqual(kinds(findings), [])

    def test_triangulated_hatch_over_stairs(self):
        # A closed hatch covers lower treads: its internal triangle edge is not a drop off the hatch.
        faces = [floor(0, 0, 400, 1000, 128), floor(800, 0, 1200, 1000, 128),
                 floor(400, 0, 800, 200, 128), floor(400, 800, 800, 1000, 128), floor(400, 200, 800, 800, 64)]

        def hatch(z):
            return {9: [[Face([(400, 200, z), (800, 200, z), (800, 800, z)], door=9),
                         Face([(400, 200, z), (800, 800, z), (400, 800, z)], door=9)]]}

        self.assertEqual(audit.mover_findings(level(faces, movers=hatch(128))), [])
        for z, kind, rise in ((112, 'recess', 16), (224, 'lip', 96)):
            findings = audit.mover_findings(level(faces, movers=hatch(z)))
            self.assertEqual(len(findings), 1)
            self.assertIn(kind, findings[0]['text'])
            self.assertEqual(findings[0]['rise'], rise)

    def test_actors(self):
        faces = room(0, 0, 2000, 1000) + box(1000, 300, 1400, 700, 0, 128) + [ceiling(1600, 300, 1800, 700, 170)]
        actor = dict(index=0, name='Drudge', radius=60, height=180)
        good = dict(actor, x=500, y=500, z=0)
        findings, _ = audit.analyse(level(faces, [good]))
        self.assertEqual(findings, [])
        for place, text in (((1700, 500, 0), 'ceiling'), ((1200, 500, 300), 'no floor'),
                            ((1030, 260, 0), 'wall'), ((1010, 500, 128), 'overhangs')):
            with self.subTest(place=place):
                x, y, z = place
                findings, _ = audit.analyse(level(faces, [dict(actor, x=x, y=y, z=z)]))
                found = [f for f in findings if f['kind'] == 'actor']
                self.assertEqual(len(found), 1)
                self.assertIn(text, found[0]['text'])


if __name__ == '__main__':
    unittest.main()
