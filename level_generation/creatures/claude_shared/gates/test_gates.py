"""Focused numeric regressions and independent Blender importer/skinning parity.

blender -b --threads 4 --python-exit-code 2 --python test_gates.py -- --out <scratch> [--glb <file> ...]
"""
import argparse
import json
import math
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import run_gates as g


def write_glb(path, doc, data):
    data += b'\0'*(-len(data) % 4)
    doc['asset'] = {'version': '2.0'}
    doc['buffers'] = [{'byteLength': len(data)}]
    header = json.dumps(doc).encode(); header += b' '*(-len(header) % 4)
    path.write_bytes(struct.pack('<III', 0x46546c67, 2, 28+len(header)+len(data))+
                     struct.pack('<II', len(header), 0x4e4f534a)+header+
                     struct.pack('<II', len(data), 0x004e4942)+data)


class GatesTests(unittest.TestCase):
    def test_axial_thrust_keeps_signed_lead_without_a_flat_axis(self):
        glb = SimpleNamespace(names={'Spear': 0})
        mesh = SimpleNamespace(rest=np.array([[0., 0., 0.], [0., 0., 1.]]))
        prop = {'name': 'spear', 'node': 'Spear', 'kind': 'melee', 'meshes': [mesh],
                'tip': [0., 1., 0.], 'edge_axis': [0., 1., 0.], 'impacts': {'Attack': .01}}
        times = np.array([0., .02, .04])
        for speed, expected in [(1., 'PASS'), (-1., 'FAIL')]:
            pose = np.tile(np.eye(4), (3, 1, 1, 1))
            pose[:, 0, 1, 3] = times * speed
            config = {'forward': [0., 1., 0.]}
            report = g.Report(config)
            g.prop_timing(prop, pose, times, glb, 'Attack', config, report)
            rows = {r['gate']: r for r in report.rows.values()}
            self.assertEqual(rows['blade_edge_share']['status'], 'N/A')
            self.assertEqual(rows['blade_signed_lead']['status'], expected)

    def test_finger_curl_follows_folded_knuckle(self):
        for knuckle in (0, 80, 120):
            a = math.radians(knuckle)/2
            root = g.rotation(np.array([math.sin(a), 0., 0., math.cos(a)]))
            for middle in (-40, 40):
                b = math.radians(middle)/2
                bend = g.rotation(np.array([math.sin(b), 0., 0., math.cos(b)]))
                curl = g.finger_curl(root @ [0, 1, 0], root @ bend @ [0, 1, 0],
                                     root, [0, 1, 0], [0, 0, 1])
                self.assertAlmostEqual(curl, middle, places=5)

    def test_four_digit_hand_config(self):
        hand = {'fingers': ['thumb', 'index', 'middle', 'pinky'], 'palm_axis': [0, 0, 1]}
        g.validate_config({'hands': {'R': hand}})
        for roots in (['thumb'], ['thumb', 'index', 'index']):
            with self.assertRaises(ValueError):
                g.validate_config({'hands': {'R': dict(hand, fingers=roots)}})

    def test_wrist_roll_after_forearm_twist(self):
        positions = {}
        config = {'hands': {}}
        for side, x in [('L', 1.), ('R', -1.)]:
            for name, y, z in [('UpperArm', 0, 1), ('Forearm', -1, 1), ('Hand', -2, 1),
                               ('Thigh', 0, .8), ('Calf', 0, .4), ('Foot', -.1, 0)]:
                positions[f'B_{side}_{name}'] = [x, y, z]
            fingers = [f'B_{side}_Finger{i}' for i in [0, 1, 2, 4]]
            for name in fingers:
                positions[name] = [x, -2.1, 1]
            config['hands'][side] = {'fingers': fingers, 'palm_axis': [1, 0, 0]}
        positions['B_R_ForearmTwist'] = [-1, -1.6, 1]
        names = {name: i for i, name in enumerate(positions)}
        rest = np.tile(np.eye(4), (len(names), 1, 1))
        rest[:, :3, 3] = list(positions.values())
        pose = np.tile(rest, (3, 1, 1, 1))
        for name, degrees in [('B_R_ForearmTwist', 60), ('B_R_Hand', 90)]:
            a = math.radians(degrees)/2
            pose[:, names[name], :3, :3] = g.rotation(np.array([0., math.sin(a), 0., math.cos(a)]))
        glb = SimpleNamespace(names=names, rest=rest, parents={}, nodes=[{} for _ in names])
        report = g.Report(config)
        g.bone_gates(glb, pose, np.array([0., 1/48, 2/48]), 'Probe', config, report, [])
        wrist = next(r for r in report.rows.values() if r['gate'] == 'wrist_roll_deg' and r['region'] == 'R')
        self.assertAlmostEqual(wrist['worst'], 30., places=5)

    def test_runtime_nlerp_short_path(self):
        q = np.array([[0, 0, 0, 1.], [0, 0, -math.sin(math.pi/4), -math.cos(math.pi/4)]])
        result = g.interpolate(np.array([2., 3]), q, np.array([1., 2.5, 4]), 'LINEAR', True)
        np.testing.assert_allclose(g.rotation(result[1]) @ [1, 0, 0], [2**-.5, 2**-.5, 0], atol=1e-7)
        np.testing.assert_allclose(g.rotation(result[0]), np.eye(3), atol=1e-7)
        self.assertAlmostEqual(g.angle(g.rotation(result[2]) @ [1, 0, 0], [0, 1, 0]), 0)

    def test_step_and_rejected_cubic(self):
        times = np.array([1., 2, 3])
        result = g.interpolate(np.array([1., 3]), np.array([[2.], [8.]]), times, 'STEP')
        np.testing.assert_equal(result.ravel(), [2, 2, 8])
        values = np.array([[0.], [2.], [3.], [3.], [8.], [0.]])
        with self.assertRaises(ValueError):
            g.interpolate(np.array([1., 3]), values, np.array([0., 2, 4]), 'CUBICSPLINE')

    def test_quaternion_roll_and_jitter(self):
        angles = np.radians(np.array([179., -179.]))
        q = np.array([[0, math.sin(a/2), 0, math.cos(a/2)] for a in angles])
        swing, roll = g.swing_twist(g.rotation(q), np.array([0, 1., 0]))
        np.testing.assert_allclose(swing, 0, atol=1e-5)
        self.assertAlmostEqual(abs(np.diff(np.unwrap(np.radians(roll))))[0]*180/np.pi, 2., places=4)
        for angles, expected in [(np.arange(10)*2., False), ((-1.)**np.arange(10)*10., True)]:
            q = np.array([[math.sin(math.radians(a)/2), 0, 0, math.cos(math.radians(a)/2)] for a in angles])
            r = g.rotation(q)
            vel = g.rotation_vector(r[1:] @ r[:-1].transpose(0, 2, 1))*48
            accel = np.linalg.norm(np.diff(vel, axis=0), axis=1)*48*180/np.pi
            self.assertEqual(bool(accel.max() > 20000), expected)

    def test_accessor_stride_sparse_and_normalized(self):
        with tempfile.TemporaryDirectory(dir=SCRATCH) as tmp:
            p = Path(tmp)/'a.glb'
            data = bytes([255, 0, 0, 0, 99, 99, 99, 99, 0, 128, 127, 0, 99, 99, 99, 99,
                          1, 0, 0, 0, 0, 0, 255, 0])
            doc = {'bufferViews': [{'buffer': 0, 'byteLength': 16, 'byteStride': 8},
                                   {'buffer': 0, 'byteOffset': 16, 'byteLength': 1},
                                   {'buffer': 0, 'byteOffset': 20, 'byteLength': 4}],
                   'accessors': [{'bufferView': 0, 'componentType': 5121, 'normalized': True,
                                  'count': 2, 'type': 'VEC4', 'sparse': {'count': 1,
                                  'indices': {'bufferView': 1, 'componentType': 5121},
                                  'values': {'bufferView': 2}}}]}
            write_glb(p, doc, data)
            np.testing.assert_equal(g.Glb(p).accessor(0), [[1, 0, 0, 0], [0, 0, 1, 0]])
            doc['bufferViews'][0]['byteLength'] = 2
            write_glb(p, doc, data)
            with self.assertRaises(ValueError):
                g.Glb(p).accessor(0)

    def test_hierarchy_and_nonzero_clip_start(self):
        with tempfile.TemporaryDirectory(dir=SCRATCH) as tmp:
            p = Path(tmp)/'nodes.glb'
            data = np.array([2., 3., 0, 0, 0, 2, 0, 0], '<f4').tobytes()
            doc = {'nodes': [{'name': 'parent', 'translation': [1, 0, 0], 'children': [1]},
                             {'name': 'child', 'translation': [0, 1, 0]}],
                   'bufferViews': [{'buffer': 0, 'byteOffset': 0, 'byteLength': 8},
                                   {'buffer': 0, 'byteOffset': 8, 'byteLength': 24}],
                   'accessors': [{'bufferView': 0, 'componentType': 5126, 'type': 'SCALAR', 'count': 2},
                                 {'bufferView': 1, 'componentType': 5126, 'type': 'VEC3', 'count': 2}],
                   'animations': [{'name': 'move', 'samplers': [{'input': 0, 'output': 1}],
                                   'channels': [{'sampler': 0, 'target': {'node': 0, 'path': 'translation'}}]}]}
            write_glb(p, doc, data); glb = g.Glb(p)
            pose = glb.pose(glb.clips()[0][1], np.array([2.5]))
            np.testing.assert_allclose(pose[0, 1, :3, 3], [1, 0, 1])
            grid = g.sample_grid(2, 2.11, 48)
            self.assertEqual(grid[0], 2); self.assertEqual(grid[-1], 2.11)
            self.assertLessEqual(np.diff(grid).max(), 1/48+1e-10)

    def test_surface_signed_depth_and_opening(self):
        vertices = np.array([[-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
                             [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]], float)
        faces = np.array([[0, 2, 1], [0, 3, 2], [4, 5, 6], [4, 6, 7], [0, 1, 5], [0, 5, 4],
                          [1, 2, 6], [1, 6, 5], [2, 3, 7], [2, 7, 6], [3, 0, 4], [3, 4, 7]])
        mesh = SimpleNamespace(rest=vertices, faces=faces, weld=np.arange(8), weld_first=np.arange(8), label='cube',
                               find_components=lambda: None, components=np.zeros(8, int))
        surface = g.Surface(mesh, np.ones(8, bool)).build(vertices)
        d, _ = surface.signed(np.array([[0, 0, 0], [2, 0, 0]]), True)
        np.testing.assert_allclose(d, [-1, 1])
        self.assertAlmostEqual(surface.gap(np.array([[1., 0, 0], [2., 0, 0]])), 0)
        self.assertAlmostEqual(surface.gap(np.array([[2., 0, 0], [3., 0, 0]])), 1)
        self.assertAlmostEqual(g.penetration(surface, np.array([[0, 0, 0]]))[0], 1000)
        class GrazingTree:
            def find_nearest(self, point):
                from mathutils import Vector
                return Vector((0, 0, 1)), Vector((0, 0, 1)), 0, 1.

            def ray_cast(self, origin, direction):
                if origin.length < .5e-6:
                    return origin-direction*1e-6, direction, 0, 0.
                return None, None, None, None

        surface.tree = GrazingTree()
        distances, _ = surface.signed(np.array([[0., 0, 0]]), containment=True)
        np.testing.assert_allclose(distances, [-1.])
        class RepeatedFaceTree(GrazingTree):
            def ray_cast(self, origin, direction):
                return origin-direction*1e-6, direction, 0, 0.

        surface.tree = RepeatedFaceTree()
        distances, _ = surface.signed(np.array([[0., 0, 0], [2., 0, 0]]), containment=True)
        np.testing.assert_allclose(distances, [-1., 1.])
        class MissedExitTree(GrazingTree):
            def ray_cast(self, origin, direction):
                if origin.x < -1.5:
                    return origin+direction, direction, 0, 1.
                return None, None, None, None

        surface.tree = MissedExitTree()
        distances, _ = surface.signed(np.array([[-2., 0, 0]]), containment=True)
        np.testing.assert_allclose(distances, [1.])
        self.assertTrue(g.exact_ray_parity(vertices[faces], [0, 0, 0], [1, 0, 0]))
        self.assertFalse(g.exact_ray_parity(vertices[faces], [-2, 0, 0], [1, 0, 0]))
        np.testing.assert_equal(g.exact_ray_parity(vertices[faces], [[0, 0, 0], [-2, 0, 0]], [1, 0, 0]),
                                [True, False])
        first = vertices.copy(); first[:, 0] *= .25
        second = first+np.array([.50000005, 0, 0])
        near_parts = np.concatenate([first[faces], second[faces]])
        np.testing.assert_equal(g.exact_ray_parity(near_parts, [[-2., 0, 0], [0, 0, 0]], [1, 0, 0]),
                                [False, True])
        mesh.faces = faces[[i for i in range(12) if i not in [2, 3]]]
        cloth = g.Surface(mesh, np.ones(8, bool), cap=True, opening={'axis': [0, 0, 1]}).build(vertices)
        self.assertAlmostEqual(g.penetration(cloth, np.array([[0, 0, 2.]]), True)[0], 0)
        self.assertAlmostEqual(g.penetration(cloth, np.array([[1.01, 0, 0.]]), True)[0], 10, places=3)
        self.assertAlmostEqual(g.penetration(cloth, np.array([[1.01, 0, 0.]]), False)[0], 0)
        self.assertAlmostEqual(g.penetration(cloth, np.array([[.99, 0, 0.]]), False)[0], 10, places=3)
        mesh.glb = SimpleNamespace(names={'cuff': 0})
        cloth = g.Surface(mesh, np.ones(8, bool), cap=True,
                          opening={'node': 'cuff', 'point': [0, 0, 1], 'axis': [0, 0, 1]})
        pose = np.eye(4)[None]; pose[0, 2, 3] = 3
        cloth.build(vertices+np.array([0, 0, 3]), pose)
        np.testing.assert_allclose(cloth.plane[0], [0, 0, 4])
        self.assertAlmostEqual(g.penetration(cloth, np.array([[0, 0, 5.]]), True)[0], 0)

    def test_open_sheet_does_not_enclose_empty_space(self):
        vertices = np.array([[-10., -10, 0], [10, -10, 0], [0, 10, 0]])
        mesh = SimpleNamespace(rest=vertices, faces=np.array([[0, 1, 2]]), weld=np.arange(3),
                               weld_first=np.arange(3), label='sheet', find_components=lambda: None,
                               components=np.zeros(3, int))
        surface = g.Surface(mesh, np.ones(3, bool)).build(vertices)
        distances, _ = surface.signed(np.array([[0, 0, -.1], [0, 0, .1]]), containment=True)
        np.testing.assert_allclose(distances, [.1, .1], atol=1e-7)

    def test_two_handed_surface_contact_checks_off_hand(self):
        vertices = np.array([[-1., -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
                             [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]])
        faces = np.array([[0, 2, 1], [0, 3, 2], [4, 5, 6], [4, 6, 7], [0, 1, 5], [0, 5, 4],
                          [1, 2, 6], [1, 6, 5], [2, 3, 7], [2, 7, 6], [3, 0, 4], [3, 4, 7]])
        cube = SimpleNamespace(rest=vertices, faces=faces, weld=np.arange(8), weld_first=np.arange(8),
                               label='grip', find_components=lambda: None, components=np.zeros(8, int))
        surface = g.Surface(cube, np.ones(8, bool)).build(vertices)
        points = np.array([[1., .2, .2], [1, .3, .2], [1, .2, .3],
                           [1.004, .2, .2], [1.004, .3, .2], [1.004, .2, .3]])
        mesh = SimpleNamespace(label='body/colour0', rest=points, edges=np.empty((0, 2), int),
                               lengths=np.empty(0), edge_regions={}, feet={}, surfaces={}, head_surface=None,
                               cloth=[], glb=SimpleNamespace(names={'Staff': 0}),
                               prop_surfaces={('staff', ('L', 'R')): None, ('staff', ('R',)): None},
                               grip_samples={})
        for side, ids in [('R', [0, 1, 2]), ('L', [3, 4, 5])]:
            mesh.grip_samples[('staff', 0, side)] = (np.array([ids]), np.eye(3),
                                                    [np.ones(3, bool) for _ in range(6)], side)
        prop = {'name': 'staff', 'node': 'Staff', 'meshes': [cube], 'hands': [
                {'side': 'R'}, {'side': 'L', 'clips': ['Attack'], 'intervals': {'Attack': [[0, .5]]}}],
                'grip_surfaces': {s: [surface] for s in 'LR'},
                'grip_signatures': {s: ['cube'] for s in 'LR'}, 'solid_surfaces': [surface]}
        report = g.Report({})
        for clip in ('Attack', 'Walking'):
            g.mesh_sample(mesh, points, g.C[None], 0., clip, {}, report, [prop], [], {})
        g.mesh_sample(mesh, points, g.C[None], .6, 'Attack', {}, report, [prop], [], {})
        right = report.rows[('body', 'Attack', mesh.label, 'grip_gap_mm', 'staff R palm')]
        left = report.rows[('body', 'Attack', mesh.label, 'grip_gap_mm', 'staff L palm')]
        self.assertEqual(right['status'], 'PASS')
        self.assertEqual(left['status'], 'FAIL')
        self.assertAlmostEqual(left['worst'], 4., places=3)
        self.assertEqual(left['samples'], 1)
        self.assertNotIn(('body', 'Walking', mesh.label, 'grip_gap_mm', 'staff L palm'), report.rows)

    def test_static_rejections_and_strict_lod(self):
        doc = {'textures': [{}]}
        ramp = {'openyamm_region_mask': {'index': 0},
                'openyamm_region_ramps': [{'range': [0, 1], 'colors': [[0, .5, 1]]*16}]}
        self.assertTrue(g.valid_ramps(doc, ramp))
        ramp['openyamm_region_ramps'][0]['colors'] = [[0, 0, 0]]*15
        self.assertFalse(g.valid_ramps(doc, ramp))
        self.assertFalse(g.valid_ramps(doc, {'openyamm_region_mask': {'index': -1}}))
        report = g.Report({})
        self.assertTrue(report.add('near', 8.5, 10))
        self.assertFalse(report.add('far', 5, 10))
        report.add('weights', .0002, .0001)
        report.add('strict_lod', 0, -1)
        self.assertEqual(report.rows[('body', 'static', 'all', 'weights', '')]['status'], 'FAIL')
        self.assertEqual(report.rows[('body', 'static', 'all', 'strict_lod', '')]['status'], 'FAIL')
        with self.assertRaises(ValueError):
            g.validate_config({'thresholds': {'typo': 1}})

    def test_skinning_all_lods_and_raw_weight_gate(self):
        with tempfile.TemporaryDirectory(dir=SCRATCH) as tmp:
            path = Path(tmp)/'skin.glb'; data = bytearray()
            doc = {'bufferViews': [], 'accessors': []}

            def accessor(values, kind, dtype='<f4', component=5126):
                array = np.array(values, dtype=dtype)
                doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(data), 'byteLength': array.nbytes})
                data.extend(array.tobytes()); data.extend(b'\0'*(-len(data) % 4))
                doc['accessors'].append({'bufferView': len(doc['bufferViews'])-1, 'componentType': component,
                                         'type': kind, 'count': len(array)})
                return len(doc['accessors'])-1

            co = accessor([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]], 'VEC3')
            joints = accessor([[0, 0, 0, 0], [1, 0, 0, 0], [1, 0, 0, 0], [0, 0, 0, 0]], 'VEC4', '<u2', 5123)
            weights = accessor([[1.0002, 0, 0, 0], [1, 0, 0, 0], [1, 0, 0, 0], [1, 0, 0, 0]], 'VEC4')
            indices = accessor([[0], [1], [2], [0], [2], [3]], 'SCALAR', '<u2', 5123)
            bind = accessor([np.eye(4).ravel(), np.eye(4).ravel()], 'MAT4')
            primitive = {'attributes': {'POSITION': co, 'JOINTS_0': joints, 'WEIGHTS_0': weights}, 'indices': indices}
            doc['meshes'] = [{'name': 'base', 'primitives': [primitive],
                              'extras': {'openyamm_lods': [1], 'openyamm_shadow_lods': [2]}},
                             {'name': 'lod1', 'primitives': [primitive]}, {'name': 'shadow', 'primitives': [primitive]}]
            doc['nodes'] = [{'name': 'a'}, {'name': 'b'}, {'name': 'body', 'mesh': 0, 'skin': 0}]
            doc['skins'] = [{'joints': [0, 1], 'inverseBindMatrices': bind}]
            doc['materials'] = [{'extensions': {'KHR_materials_specular': {}}}]
            write_glb(path, doc, bytes(data)); glb = g.Glb(path); meshes = g.load_meshes(glb)
            self.assertEqual(len(meshes), 3)
            mesh = meshes[0]; pose = glb.rest.copy(); pose[1, 0, 3] += 1
            g.configure_mesh(mesh, {'regions': {'head': 'exposed', 'exposed': {'vertices': [0]}}}, g.Report({}))
            np.testing.assert_equal(mesh.regions['head'], [True, False, False, False])
            empty_report = g.Report({})
            g.configure_mesh(mesh, {'regions': {'head': {'vertices': []}}}, empty_report)
            self.assertEqual(empty_report.rows[('body', 'static', mesh.label, 'head_setup', '')]['status'],
                             'UNVERIFIED')
            p = mesh.posed(pose)
            np.testing.assert_allclose(p[:, 0], [0, 2, 2, 0])
            duplicate_doc = json.loads(json.dumps(doc))
            duplicate_doc['meshes'][0]['primitives'] = [primitive, primitive]
            duplicate_path = Path(tmp)/'seams.glb'
            write_glb(duplicate_path, duplicate_doc, bytes(data))
            duplicate_mesh = g.load_meshes(g.Glb(duplicate_path))[0]
            foot_config = {'regions': {'foot_L': {'vertices': list(range(8))}}}
            g.configure_mesh(duplicate_mesh, foot_config, g.Report(foot_config))
            self.assertEqual(len(duplicate_mesh.feet['L'][0]), 2)
            ratios = np.linalg.norm(p[mesh.edges[:, 0]]-p[mesh.edges[:, 1]], axis=1)/mesh.lengths
            self.assertAlmostEqual(ratios.max(), 2.)
            mesh.regions['hand_R'] = np.ones(len(mesh.vertices), bool)
            before = g.grip_points(mesh, 'R', {})[-1]
            self.assertEqual(before, g.grip_points(mesh, 'R', {})[-1])
            mesh.vertices[0, 0] += .001
            self.assertNotEqual(before, g.grip_points(mesh, 'R', {})[-1])
            report = g.Report({'previous_counts': {'body': {'colour': [1, 1]}}})
            g.static_gates(glb, report, 'body')
            failed = {r['gate'] for r in report.rows.values() if r['status'] == 'FAIL'}
            self.assertTrue({'weight_sum_error', 'lod_strict_decrease', 'material_extensions', 'triangles'} <= failed)
            struct.pack_into('<3f', data, 3*3*4, 0, 0, 0)
            write_glb(path, doc, bytes(data)); welded = g.load_meshes(g.Glb(path))[0]
            self.assertEqual(welded.weld[0], welded.weld[3])
            offset = doc['bufferViews'][doc['accessors'][joints]['bufferView']]['byteOffset']
            struct.pack_into('<H', data, offset+3*4*2, 1)
            write_glb(path, doc, bytes(data)); separate = g.load_meshes(g.Glb(path))[0]
            self.assertNotEqual(separate.weld[0], separate.weld[3])

    def test_adaptive_grid_and_time_weighted_contact(self):
        # Float32 GLB endpoints must not create accidental near-duplicate samples during refinement.
        coarse = g.sample_grid(np.float32(0), np.float32(3), 24)
        samples = set()
        for a, b in zip(coarse, coarse[1:]):
            samples.update(round(float(t), 12) for t in g.sample_grid(a, b, 48))
        self.assertEqual(len(samples), 145)
        mesh = SimpleNamespace(label='feet')
        trace = [{'time': t, 'L': {'low': low}, 'R': {'low': low}} for t, low in
                 [(0, 0), (.1, 0), (.2, 0), (1., .1)]]
        report = g.Report({}); g.finish_feet(trace, mesh, 'Running', {}, report)
        result = next(r for r in report.rows.values() if r['gate'] == 'running_contact_pct')
        self.assertAlmostEqual(result['worst'], 60)
        self.assertEqual(result['status'], 'FAIL')

    def test_report_missing_and_threshold_override(self):
        report = g.Report({'thresholds': {'wrist_roll_deg': 40}, 'clip_thresholds': {'Attack': {'wrist_roll_deg': 50}}})
        self.assertEqual(report.limit('wrist_roll_deg', 'Attack'), 50)
        self.assertEqual(report.limit('wrist_roll_deg', 'Standing'), 40)
        report.missing('grip', 'No grip region', clip='Attack', lod='colour3')
        with tempfile.TemporaryDirectory(dir=SCRATCH) as tmp:
            self.assertEqual(report.write(Path(tmp), 1), 'UNVERIFIED')
            result = json.loads((Path(tmp)/'gates.json').read_text())
            self.assertEqual(result['counts']['UNVERIFIED'], 1)
        with self.assertRaises(ValueError):
            g.validate_config({'props': [{'name': 'axe', 'file': 'a.glb', 'node': 'Axe', 'kind': 'melee', 'typo': 1}]})
        report.series('single_key_clip', np.array([]), np.array([]), 10., detail='No time interval')
        self.assertEqual(report.rows[('body', 'static', 'all', 'single_key_clip', '')]['status'], 'UNVERIFIED')



def blender_parity(path):
    import bpy
    from mathutils.kdtree import KDTree
    glb = g.Glb(path)
    mesh = max(g.load_meshes(glb), key=lambda candidate: len(candidate.rest))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.fps = 48
    bpy.ops.import_scene.gltf(filepath=str(Path(path).resolve()), bone_heuristic='BLENDER', merge_vertices=False)
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    objects = [o for o in bpy.data.objects if o.type == 'MESH']
    obj = max(objects, key=lambda o: len(o.data.vertices))
    fps = bpy.context.scene.render.fps/bpy.context.scene.render.fps_base
    # Establish index correspondence once in bind pose; exporter UV splits may be reordered by the importer.
    rig.animation_data.action = None
    for track in rig.animation_data.nla_tracks:
        track.mute = True
    for pb in rig.pose.bones:
        pb.matrix_basis.identity()
    bpy.context.view_layer.update()
    tree = KDTree(len(mesh.rest))
    for i, co in enumerate(mesh.rest):
        tree.insert(co, i)
    tree.balance()
    ids = []; rest_error = 0.
    raw_weights = np.zeros((len(mesh.rest), len(mesh.bone_names)))
    for k in range(mesh.weights.shape[1]):
        np.add.at(raw_weights, (np.arange(len(mesh.rest)), mesh.joints[:, k]), mesh.weights[:, k])
    groups = {vg.index: mesh.bone_names.index(vg.name) for vg in obj.vertex_groups if vg.name in mesh.bone_names}
    for vertex in obj.data.vertices:
        point = obj.matrix_world @ vertex.co
        _, index, distance = tree.find(point)
        weights = np.zeros(len(mesh.bone_names))
        for entry in vertex.groups:
            if entry.group in groups:
                weights[groups[entry.group]] = entry.weight
        candidates = [i for _, i, _ in tree.find_range(point, 1e-5)]
        if candidates:
            index = candidates[int(np.argmin(np.linalg.norm(raw_weights[candidates]-weights, axis=1)))]
        ids.append(index); rest_error = max(rest_error, distance)
    if rest_error > 1e-5:
        raise AssertionError(f'Bind correspondence error {rest_error} on {path}')
    rows = []
    for name, animation, start, end in glb.clips():
        action = bpy.data.actions.get(name)
        if action is None:
            action = next(a for a in bpy.data.actions if a.name.split('|')[-1] == name)
        rig.animation_data.action = action
        if action.slots:
            rig.animation_data.action_slot = action.slots[0]
        for t in [start, start+(end-start)*.371, end]:
            frame = t*fps
            bpy.context.scene.frame_set(math.floor(frame), subframe=frame-math.floor(frame))
            evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = evaluated.to_mesh()
            co = np.empty(len(m.vertices)*3); m.vertices.foreach_get('co', co)
            co = g.transform(np.array(evaluated.matrix_world), co.reshape(-1, 3)); evaluated.to_mesh_clear()
            expected = mesh.posed(glb.pose(animation, np.array([t]))[0])[ids]
            error = float(np.linalg.norm(co-expected, axis=1).max())
            rows.append({'clip': name, 'time_s': float(t), 'max_error_m': error})
            if error > 1e-4:
                raise AssertionError(f'Blender parity {path} {name} {t}: {error} m')
    result = {'file': str(path), 'sha256': glb.sha256,
              'max_error_m': max(r['max_error_m'] for r in rows), 'samples': rows}
    print('PARITY', path, result['max_error_m'], flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--glb', type=Path, action='append', default=[])
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    SCRATCH = args.out.resolve(); SCRATCH.mkdir(parents=True, exist_ok=True)
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(GatesTests))
    if not result.wasSuccessful():
        raise AssertionError('Numeric regression failed')
    results = [blender_parity(path) for path in args.glb]
    payload = {'unit_tests': result.testsRun, 'blender_parity': results}
    (SCRATCH/'tests.json').write_text(json.dumps(payload, indent=2)+'\n')
