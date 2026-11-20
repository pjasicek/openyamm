import ast
import copy
from pathlib import Path
import re
import unittest

from export_indoor_scene_yml import parse_indoor_blv, repair_snake_temple_lift


class SnakeTempleLiftTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[1]
        map_path = root / "assets_dev/worlds/mm6/maps/6t8.blv"
        self.map = parse_indoor_blv(map_path)
        scene = map_path.with_suffix(".scene.yml").read_text(encoding="utf-8")
        block = scene.split("    - door_index: 0\n", 1)[1].split("    - door_index: 1\n", 1)[0]
        self.door = {"door_id": 3}
        for key in ("vertex_ids", "x_offsets", "y_offsets", "z_offsets"):
            self.door[key] = ast.literal_eval(re.search(rf"      {key}: (\[.*\])", block).group(1))
        self.door["num_vertices"] = len(self.door["vertex_ids"])
        self.door["num_offsets"] = len(self.door["x_offsets"])

    def assert_wall_closed(self, door):
        # Both rear wall panels must reach the platform along their whole lower edge, throughout the 696-unit stroke.
        for distance in (0, 174, 348, 522, 696):
            vertices = copy.deepcopy(self.map["vertices"])
            for index, vertex_id in enumerate(door["vertex_ids"]):
                vertices[vertex_id]["z"] = door["z_offsets"][index] - distance
            for face_id in (490, 779):
                bottom_ids = [vertex_id for vertex_id in self.map["face_vertex_ids"][face_id]
                              if self.map["vertices"][vertex_id]["z"] == 700]
                self.assertEqual(len(bottom_ids), 2)
                self.assertEqual([vertices[vertex_id]["z"] for vertex_id in bottom_ids],
                                 [700 - distance, 700 - distance])

    def test_mounted_lift_wall_covers_full_shaft(self):
        self.assert_wall_closed(self.door)

    def test_export_repairs_legacy_gap_and_is_idempotent(self):
        legacy = copy.deepcopy(self.door)
        index = legacy["vertex_ids"].index(821)
        for key in ("vertex_ids", "x_offsets", "y_offsets", "z_offsets"):
            legacy[key].pop(index)
        legacy["num_vertices"] -= 1
        legacy["num_offsets"] -= 1
        with self.assertRaises(AssertionError):
            self.assert_wall_closed(legacy)
        other_door = copy.deepcopy(legacy)
        other_door["door_id"] = 4
        original_other = copy.deepcopy(other_door)
        repair_snake_temple_lift([legacy, other_door], self.map["vertices"])
        self.assert_wall_closed(legacy)
        self.assertEqual(legacy, self.door)
        self.assertEqual(other_door, original_other)
        repair_snake_temple_lift([legacy], self.map["vertices"])
        self.assertEqual(legacy, self.door)


if __name__ == "__main__":
    unittest.main()
