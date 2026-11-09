"""Regressions of detached_parts_audit.py: synthetic parts for each root rule, and the Sea Monster's r3 export, whose
seven dorsal tail fins floated 6-23 cm above the tail while the old chain rule passed them all.

    python3 level_generation/creatures/claude_shared/test_detached_parts_audit.py [-v]

The Sea Monster case needs ../mm9_seamon_claude/work/before_eyesfins_r3.glb (skipped when it is gone).
"""
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np  # noqa: E402
from scipy.spatial import cKDTree  # noqa: E402
import detached_parts_audit as audit  # noqa: E402

THRESHOLD = 0.004
SEAMON_R3 = Path(__file__).resolve().parent.parent / 'mm9_seamon_claude' / 'work' / 'before_eyesfins_r3.glb'
SEAMON_FIXED = Path(__file__).resolve().parents[3] / 'assets_source' / 'worlds' / 'mm9' / 'models' / 'mm9_seamon.glb'
# fin centres (glTF) from mm9_seamon_claude/review/mouth_20261030/fin_gates_before.json, with fin_gates.py's base gap
# at bind: the front fin touched, the other six floated
SEAMON_FINS = [((0.034, 0.638, -0.284), 0.0), ((0.032, 0.607, -0.494), 0.0588), ((0.033, 0.498, -0.855), 0.0988),
               ((0.030, 0.472, -1.084), 0.1680), ((0.019, 0.424, -1.333), 0.0926), ((0.027, 0.406, -1.570), 0.1912),
               ((0.026, 0.408, -1.795), 0.2163)]


def box(lo, hi, rotate=None, pivot=None):
    """Closed box (8 corners, 12 outward triangles), optionally rotated about the x axis by `rotate` radians."""
    lo, hi = np.asarray(lo, float), np.asarray(hi, float)
    v = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
    f = np.array([[0, 1, 3], [0, 3, 2], [4, 6, 7], [4, 7, 5], [0, 4, 5], [0, 5, 1],
                  [2, 3, 7], [2, 7, 6], [0, 2, 6], [0, 6, 4], [1, 5, 7], [1, 7, 3]])
    if rotate is not None:
        c, s = np.cos(rotate), np.sin(rotate)
        rot = np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
        piv = np.asarray(pivot, float)
        v = (v - piv) @ rot.T + piv
    return v, f


def sphere(centre, radius, rings=8, segments=12):
    v = [[0.0, radius, 0.0]]
    for r in range(1, rings):
        phi = np.pi * r / rings
        for s in range(segments):
            th = 2 * np.pi * s / segments
            v.append([radius * np.sin(phi) * np.cos(th), radius * np.cos(phi), radius * np.sin(phi) * np.sin(th)])
    v.append([0.0, -radius, 0.0])
    f = []
    for s in range(segments):
        f.append([0, 1 + (s + 1) % segments, 1 + s])
    for r in range(rings - 2):
        a, b = 1 + r * segments, 1 + (r + 1) * segments
        for s in range(segments):
            s1 = (s + 1) % segments
            f += [[a + s, a + s1, b + s], [a + s1, b + s1, b + s]]
    last, base = len(v) - 1, 1 + (rings - 2) * segments
    for s in range(segments):
        f.append([last, base + s, base + (s + 1) % segments])
    return np.array(v) + np.asarray(centre, float), np.array(f)


def write_glb(path, parts):
    """One unskinned mesh, one primitive per part."""
    data, accessors, views, prims = b'', [], [], []
    for v, f in parts:
        for arr, kind, comp, target in ((v.astype(np.float32), 'VEC3', 5126, 34962),
                                         (f.astype(np.uint32).reshape(-1), 'SCALAR', 5125, 34963)):
            data += b'\0' * (-len(data) % 4)
            views.append({'buffer': 0, 'byteOffset': len(data), 'byteLength': arr.nbytes, 'target': target})
            acc = {'bufferView': len(views) - 1, 'componentType': comp, 'count': len(arr), 'type': kind}
            if kind == 'VEC3':
                acc.update(min=arr.min(0).tolist(), max=arr.max(0).tolist())
            accessors.append(acc)
            data += arr.tobytes()
        prims.append({'attributes': {'POSITION': len(accessors) - 2}, 'indices': len(accessors) - 1})
    data += b'\0' * (-len(data) % 4)
    doc = {'asset': {'version': '2.0'}, 'scene': 0, 'scenes': [{'nodes': [0]}],
           'nodes': [{'name': 'Model', 'mesh': 0}], 'meshes': [{'name': 'Model', 'primitives': prims}],
           'accessors': accessors, 'bufferViews': views, 'buffers': [{'byteLength': len(data)}]}
    head = json.dumps(doc).encode()
    head += b' ' * (-len(head) % 4)
    path.write_bytes(struct.pack('<III', 0x46546C67, 2, 28 + len(head) + len(data))
                     + struct.pack('<II', len(head), 0x4E4F534A) + head + struct.pack('<II', len(data), 0x004E4942)
                     + data)


BODY = box((-0.5, 0.0, -1.0), (0.5, 0.5, 1.0))  # top at y = 0.5


def fin(z0, bottom, tilt=None):
    """A 2 cm thick, 30 cm tall and 30 cm long plate standing on the body's top from z0 to z0 + 0.3."""
    lo, hi = (-0.01, bottom, z0), (0.01, bottom + 0.3, z0 + 0.3)
    if tilt is None:
        return box(lo, hi)
    return box(lo, hi, rotate=tilt, pivot=(0.0, bottom, z0 + 0.3))


class Synthetic(unittest.TestCase):
    def measure(self, parts, **kw):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'model.glb'
            write_glb(path, parts)
            cr = audit.Creature(path)
            return cr, audit.measure_pose_root(cr, cr.rest, THRESHOLD, **kw)

    def part_near(self, cr, centre):
        cen = np.array([cr.rest[v].mean(0) for v in cr.comp_verts])
        return int(np.argmin(np.linalg.norm(cen - np.asarray(centre), axis=1)))

    def test_plate_rooted_along_its_base_is_attached(self):
        cr, (gaps, attached, rooted, visible, kinds) = self.measure([BODY, fin(-0.15, 0.48)])
        self.assertTrue(attached.all())

    def test_plate_touching_at_one_corner_is_lifted(self):
        # the front of the base 1 cm in the body, the back 5 cm above it (about 11 degrees)
        tilted = fin(-0.15, 0.49, tilt=np.arctan2(0.06, 0.3))
        cr, (gaps, attached, rooted, visible, kinds) = self.measure([BODY, tilted])
        k = self.part_near(cr, (0.0, 0.66, 0.0))
        self.assertFalse(attached[k])
        self.assertEqual(kinds[k], 'lifted')
        self.assertGreater(gaps[k][0], 0.03)
        # the old chain rule took the touching corner for a root
        self.assertTrue(audit.measure_pose(cr, cr.rest, THRESHOLD)[1][k])

    def test_row_of_fins_resting_on_each_other_must_reach_the_body(self):
        # the front fin rooted; two equal fins behind it overlap its back end but float 5 cm above the body
        front = fin(-0.6, 0.48)
        mid = box((0.012, 0.55, -0.35), (0.032, 0.85, -0.05))
        back = box((-0.01, 0.55, -0.1), (0.01, 0.85, 0.2))
        cr, (gaps, attached, rooted, visible, kinds) = self.measure([BODY, front, mid, back])
        k_front, k_mid, k_back = (self.part_near(cr, c) for c in ((0, 0.63, -0.45), (0.022, 0.7, -0.2), (0, 0.7, 0.05)))
        self.assertTrue(attached[k_front])
        self.assertFalse(attached[k_mid])
        self.assertFalse(attached[k_back])
        self.assertAlmostEqual(gaps[k_mid][0], 0.05, delta=0.005)
        old = audit.measure_pose(cr, cr.rest, THRESHOLD)[1]
        self.assertTrue(old[k_mid] and old[k_back])

    def test_eyeball_in_a_socket_and_a_tooth_pass(self):
        eye = sphere((0.2, 0.5, 0.5), 0.05)  # half in the body
        tooth = box((-0.2, 0.45, 0.6), (-0.18, 0.6, 0.62))  # root 5 cm deep
        cr, (gaps, attached, rooted, visible, kinds) = self.measure([BODY, eye, tooth])
        self.assertTrue(attached.all())

    def test_loose_eyeball_and_a_floating_cluster(self):
        eye = sphere((0.2, 0.56, 0.5), 0.05)  # 1 cm above the body
        a = sphere((-0.2, 0.7, 0.0), 0.05)
        b = sphere((-0.2, 0.79, 0.0), 0.05)  # overlaps a; both 15 cm above the body
        cr, (gaps, attached, rooted, visible, kinds) = self.measure([BODY, eye, a, b])
        k_eye = self.part_near(cr, (0.2, 0.56, 0.5))
        self.assertAlmostEqual(gaps[k_eye][0], 0.01, delta=0.002)
        k_a, k_b = self.part_near(cr, (-0.2, 0.7, 0.0)), self.part_near(cr, (-0.2, 0.79, 0.0))
        breaks = [k for k in (k_a, k_b) if gaps[k][5] is not None]
        self.assertEqual(len(breaks), 1)  # one break, the other carried
        self.assertAlmostEqual(gaps[breaks[0]][0], 0.15, delta=0.005)

    def test_chunky_part_whose_root_parts_in_a_clip(self):
        # not a plate: a 20 cm block 1 cm in the body at bind; in the pose one edge stays in and the far side lifts 8 cm
        block = box((-0.1, 0.49, -0.1), (0.1, 0.69, 0.1))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'model.glb'
            write_glb(path, [BODY, block])
            cr = audit.Creature(path)
        k = 1 - cr.body
        self.assertTrue(audit.measure_pose_root(cr, cr.rest, THRESHOLD)[1][k])
        roots = cr.last_roots
        self.assertIn(k, roots)
        P = cr.rest.copy()
        verts = cr.comp_verts[k]
        tilted = box((-0.1, 0.49, -0.1), (0.1, 0.69, 0.1), rotate=np.arctan2(0.09, 0.2), pivot=(0.0, 0.49, 0.1))[0]
        order = cKDTree(box((-0.1, 0.49, -0.1), (0.1, 0.69, 0.1))[0]).query(P[verts])[1]
        P[verts] = tilted[order]
        self.assertTrue(audit.measure_pose_root(cr, P, THRESHOLD)[1][k])  # one touching edge passes without a bind root
        gaps, attached, rooted, visible, kinds = audit.measure_pose_root(cr, P, THRESHOLD, roots=roots)
        self.assertFalse(attached[k])
        self.assertEqual(kinds[k], 'parted')
        self.assertGreater(gaps[k][0], 2 * THRESHOLD)
        self.assertGreater(cr.last_lifts[k][0], gaps[k][0] * 0.5)

    def test_pivoting_part_keeps_its_root(self):
        # a block pivoting about the middle of its root: one side sinks as the other lifts, so it stays seated
        block = box((-0.1, 0.46, -0.1), (0.1, 0.69, 0.1))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'model.glb'
            write_glb(path, [BODY, block])
            cr = audit.Creature(path)
        k = 1 - cr.body
        audit.measure_pose_root(cr, cr.rest, THRESHOLD)
        roots = cr.last_roots
        P = cr.rest.copy()
        verts = cr.comp_verts[k]
        pivoted = box((-0.1, 0.46, -0.1), (0.1, 0.69, 0.1), rotate=0.3, pivot=(0.0, 0.5, 0.0))[0]
        order = cKDTree(box((-0.1, 0.46, -0.1), (0.1, 0.69, 0.1))[0]).query(P[verts])[1]
        P[verts] = pivoted[order]
        self.assertTrue(audit.measure_pose_root(cr, P, THRESHOLD, roots=roots)[1][k])

    def test_part_wholly_inside_has_no_root_to_part(self):
        cr, _ = self.measure([BODY, sphere((0.0, 0.25, 0.0), 0.05)])
        self.assertEqual(cr.last_roots, {})

    def test_point_behind_a_thin_plate_corner_is_outside(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'model.glb'
            write_glb(path, [BODY, fin(-0.15, 0.6)])
            cr = audit.Creature(path)
            geo = audit.PoseGeometry(cr, cr.rest)
            k = self.part_near(cr, (0, 0.75, 0.0))
            # far below and behind the plate's lower back corner
            sd = geo.signed(np.array([[0.0, 0.4, 0.3], [0.05, 0.45, -0.3]]), k)[0]
            self.assertTrue((sd > 0).all())


@unittest.skipUnless(SEAMON_R3.exists(), f'{SEAMON_R3} is not kept')
class SeaMonsterR3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cr = audit.Creature(SEAMON_R3)
        cen = np.array([cls.cr.rest[v].mean(0) for v in cls.cr.comp_verts])
        cls.fins = []
        for c, gap in SEAMON_FINS:
            d = np.linalg.norm(cen - np.array(c), axis=1)
            k = int(np.argmin(d))
            assert d[k] < 0.02, f'no component at fin {c}'
            cls.fins.append((k, gap))

    def check_pose(self, P):
        gaps, attached, rooted, visible, kinds = audit.measure_pose_root(self.cr, P, THRESHOLD)
        reported = 0
        for k, gap in self.fins:
            if gap == 0.0:
                self.assertTrue(attached[k], f'front fin {k} should stay rooted')
                continue
            self.assertFalse(attached[k], f'fin {k} ({gap * 100:.0f} cm above the tail) passed')
            if gaps[k][5] is not None:
                reported += 1
                self.assertGreater(gaps[k][0], 0.02)
        self.assertGreaterEqual(reported, 5)
        return gaps, kinds

    def test_bind_flags_every_floating_fin(self):
        gaps, kinds = self.check_pose(self.cr.rest)
        k_front2 = self.fins[1][0]  # touches the back at one corner; its base lifts to about 5 cm
        self.assertEqual(kinds[k_front2], 'lifted')

    def test_hit_flags_every_floating_fin(self):
        self.check_pose(self.cr.pose('Hit', 0.3))

    def test_old_chain_rule_passed_them(self):
        attached = audit.measure_pose(self.cr, self.cr.rest, THRESHOLD)[1]
        self.assertTrue(all(attached[k] for k, _ in self.fins))


@unittest.skipUnless(SEAMON_FIXED.exists(), f'{SEAMON_FIXED} is not installed')
class SeaMonsterFixed(unittest.TestCase):
    def test_rooted_fins_pass(self):
        cr = audit.Creature(SEAMON_FIXED)
        gaps, attached, rooted, visible, kinds = audit.measure_pose_root(cr, cr.rest, THRESHOLD)
        self.assertEqual(gaps, {})


if __name__ == '__main__':
    unittest.main()
