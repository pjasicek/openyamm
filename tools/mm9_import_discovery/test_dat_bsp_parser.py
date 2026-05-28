#!/usr/bin/env python3
from __future__ import annotations

import struct
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from convert_abc_model import (
    AbcModel,
    AnimBinding,
    Lod,
    ModelAnimation,
    NodeInfo,
    Piece,
    SocketInfo,
    Transform,
    Vertex,
    scale_abc_model,
)
from transcode_mm9_dat_to_blv import build_leaf_grid_layout, build_spatial_grid_layout
from transcode_mm9_dat_to_odm import (
    BinaryReader,
    DatWorld,
    ObjectProperty,
    OdmBModel,
    OdmFace,
    OdmVertex,
    PBlockTableSummary,
    Poly,
    UserPortal,
    WorldBsp,
    WorldInfo,
    WorldLeaf,
    read_world_objects,
    read_leaf,
    read_node,
    read_user_portal,
)


def dummy_poly() -> Poly:
    return Poly(
        center=(0.0, 0.0, 0.0),
        lightmap_width=0,
        lightmap_height=0,
        unknown_flag=0,
        unknown_list=[],
        surface_index=0,
        plane_index=0,
        disk_verts=[],
    )


def dummy_world_bsp(name: str, polies: list[Poly] | None = None, leaves: list[WorldLeaf] | None = None) -> WorldBsp:
    return WorldBsp(
        name=name,
        textures=[],
        points=[],
        point_normals=[],
        planes=[],
        surfaces=[],
        polies=polies or [],
        leaves=leaves or [],
        nodes=[],
        user_portals=[],
        min_box=(0.0, 0.0, 0.0),
        max_box=(0.0, 0.0, 0.0),
        world_translation=(0.0, 0.0, 0.0),
        root_node_index=0,
        section_count=0,
        counts={},
        pblock_table=PBlockTableSummary(
            dim_a=0,
            dim_b=0,
            dim_c=0,
            min_box=(0.0, 0.0, 0.0),
            max_box=(0.0, 0.0, 0.0),
            record_count=0,
        ),
    )


class DatBspParserTests(unittest.TestCase):
    def test_scale_abc_model_scales_only_world_distance_values(self) -> None:
        model = AbcModel(
            name="test",
            version=13,
            command_string="",
            internal_radius=5.0,
            lod_distances=[10.0],
            pieces=[
                Piece(
                    name="piece",
                    material_index=0,
                    specular_power=0.0,
                    specular_scale=0.0,
                    lod_weight=1.0,
                    lods=[
                        Lod(
                            faces=[],
                            vertices=[
                                Vertex(
                                    position=(1.0, 2.0, 3.0),
                                    normal=(0.0, 1.0, 0.0),
                                    weights=[],
                                )
                            ],
                        )
                    ],
                )
            ],
            nodes=[
                NodeInfo(
                    name="root",
                    index=0,
                    flags=0,
                    child_count=0,
                    bind_matrix=np.identity(4, dtype=np.float32),
                )
            ],
            animations=[
                ModelAnimation(
                    name="idle",
                    interpolation_time_ms=0,
                    keyframes=[],
                    node_transforms=[
                        [
                            Transform(
                                translation=(4.0, 5.0, 6.0),
                                rotation=(0.0, 0.0, 0.0, 1.0),
                            )
                        ]
                    ],
                )
            ],
            sockets=[
                SocketInfo(
                    name="socket",
                    node_index=0,
                    rotation=(0.0, 0.0, 0.0, 1.0),
                    translation=(7.0, 8.0, 9.0),
                )
            ],
            anim_bindings=[AnimBinding(name="binding", extents=(10.0, 11.0, 12.0), origin=(13.0, 14.0, 15.0))],
        )
        model.nodes[0].bind_matrix[:3, 3] = np.array([16.0, 17.0, 18.0], dtype=np.float32)

        scale_abc_model(model, 2.0)

        self.assertEqual(model.internal_radius, 10.0)
        self.assertEqual(model.lod_distances, [20.0])
        self.assertEqual(model.pieces[0].lods[0].vertices[0].position, (2.0, 4.0, 6.0))
        self.assertEqual(model.pieces[0].lods[0].vertices[0].normal, (0.0, 1.0, 0.0))
        self.assertEqual(model.animations[0].node_transforms[0][0].translation, (8.0, 10.0, 12.0))
        self.assertEqual(model.animations[0].node_transforms[0][0].rotation, (0.0, 0.0, 0.0, 1.0))
        self.assertEqual(model.sockets[0].translation, (14.0, 16.0, 18.0))
        self.assertEqual(model.sockets[0].rotation, (0.0, 0.0, 0.0, 1.0))
        self.assertEqual(model.anim_bindings[0].extents, (20.0, 22.0, 24.0))
        self.assertEqual(model.anim_bindings[0].origin, (26.0, 28.0, 30.0))
        np.testing.assert_array_equal(model.nodes[0].bind_matrix[:3, 3], np.array([32.0, 34.0, 36.0]))

    def test_read_leaf_preserves_portal_payload_and_packed_polygon_entries(self) -> None:
        data = bytearray()
        data += struct.pack("<H", 1)
        data += struct.pack("<HH", 0xFFFF, 3)
        data += b"abc"
        data += struct.pack("<I", 2)
        data += struct.pack("<II", 0x00060032, 0x00FF0031)
        data += struct.pack("<I", 0x12345678)

        leaf = read_leaf(BinaryReader(bytes(data)))

        self.assertEqual(leaf.count, 1)
        self.assertIsNone(leaf.index)
        self.assertEqual(len(leaf.portal_data), 1)
        self.assertEqual(leaf.portal_data[0].portal_id, 0xFFFF)
        self.assertEqual(leaf.portal_data[0].contents, b"abc")
        self.assertEqual(leaf.polygon_entries, [0x00060032, 0x00FF0031])
        self.assertEqual(leaf.polygon_ref_indices(), [6, 255])
        self.assertEqual(
            [(polygon_ref.world_model_index, polygon_ref.poly_index) for polygon_ref in leaf.polygon_refs()],
            [(0x32, 6), (0x31, 255)],
        )
        self.assertEqual(leaf.unknown, 0x12345678)

    def test_read_leaf_index_reference_variant(self) -> None:
        data = struct.pack("<HHII", 0xFFFF, 42, 0, 0x90ABCDEF)

        leaf = read_leaf(BinaryReader(data))

        self.assertEqual(leaf.count, 0xFFFF)
        self.assertEqual(leaf.index, 42)
        self.assertEqual(leaf.portal_data, [])
        self.assertEqual(leaf.polygon_entries, [])
        self.assertEqual(leaf.unknown, 0x90ABCDEF)

    def test_read_node_preserves_child_indices(self) -> None:
        data = struct.pack("<IHII", 436, 0xFFFF, 1, 0xFFFFFFFE)

        node = read_node(BinaryReader(data))

        self.assertEqual(node.poly_index, 436)
        self.assertEqual(node.leaf_index, 0xFFFF)
        self.assertEqual(node.front_index, 1)
        self.assertEqual(node.back_index, 0xFFFFFFFE)

    def test_read_user_portal_uses_mm9_v66_layout(self) -> None:
        data = bytearray()
        data += struct.pack("<H", 17)
        data += b"MiddleDoorPortal5"
        data += struct.pack("<IHffffff", 0, 0x20E0, 10.0, -4962.0, 36.0, 60.0, 0.0, 128.0)

        portal = read_user_portal(BinaryReader(bytes(data)))

        self.assertEqual(portal.name, "MiddleDoorPortal5")
        self.assertEqual(portal.unknown_int_1, 0)
        self.assertEqual(portal.unknown_int_2, 0)
        self.assertEqual(portal.unknown_short, 0x20E0)
        self.assertEqual(portal.center, (10.0, -4962.0, 36.0))
        self.assertEqual(portal.dims, (60.0, 0.0, 128.0))

    def test_read_world_objects_preserves_unknown_property_raw_bytes(self) -> None:
        object_payload = bytearray()
        object_payload += struct.pack("<H", 6)
        object_payload += b"Object"
        object_payload += struct.pack("<I", 1)
        object_payload += struct.pack("<H", 7)
        object_payload += b"Mystery"
        object_payload += struct.pack("<BIH", 128, 0x1234, 3)
        object_payload += b"xyz"
        data = bytearray()
        data += struct.pack("<I", 1)
        data += struct.pack("<H", len(object_payload))
        data += object_payload

        objects = read_world_objects(BinaryReader(bytes(data)))

        self.assertEqual(len(objects), 1)
        self.assertEqual(len(objects[0].properties), 1)
        prop = objects[0].properties[0]
        self.assertEqual(prop.name, "Mystery")
        self.assertEqual(prop.code, 128)
        self.assertEqual(prop.flags, 0x1234)
        self.assertEqual(prop.declared_data_length, 3)
        self.assertEqual(prop.raw_data, b"xyz")
        self.assertFalse(prop.decoded)
        self.assertIsNone(prop.value)

    def test_spatial_grid_layout_emits_native_rooms_and_portal_link(self) -> None:
        bmodel = OdmBModel(name="test")
        bmodel.vertices = [
            OdmVertex(0, 0, 0),
            OdmVertex(100, 0, 0),
            OdmVertex(0, 100, 0),
            OdmVertex(1000, 0, 0),
            OdmVertex(1100, 0, 0),
            OdmVertex(1000, 100, 0),
        ]
        bmodel.faces = [
            OdmFace(
                vertex_indices=[0, 1, 2],
                texture_us=[0, 0, 0],
                texture_vs=[0, 0, 0],
                texture_alias="STONE",
                bitmap_index=0,
                polygon_type=0,
                attributes=0,
                plane_normal=(0, 0, 0),
                plane_distance=0,
            ),
            OdmFace(
                vertex_indices=[3, 4, 5],
                texture_us=[0, 0, 0],
                texture_vs=[0, 0, 0],
                texture_alias="STONE",
                bitmap_index=0,
                polygon_type=0,
                attributes=0,
                plane_normal=(0, 0, 0),
                plane_distance=0,
            ),
        ]

        layout = build_spatial_grid_layout([bmodel], 2, "STONE")

        self.assertEqual(len(layout.rooms), 2)
        self.assertEqual(sum(len(room.triangles) for room in layout.rooms), 2)
        self.assertEqual(len(layout.portals), 1)
        self.assertEqual(layout.portals[0].front_room_id, 0)
        self.assertEqual(layout.portals[0].back_room_id, 1)

    def test_leaf_grid_layout_uses_decoded_leaf_polygon_refs(self) -> None:
        bmodel = OdmBModel(name="test", source_model_index=1)
        bmodel.vertices = [
            OdmVertex(0, 0, 0),
            OdmVertex(100, 0, 0),
            OdmVertex(0, 100, 0),
            OdmVertex(1000, 0, 0),
            OdmVertex(1100, 0, 0),
            OdmVertex(1000, 100, 0),
        ]
        bmodel.faces = [
            OdmFace(
                vertex_indices=[0, 1, 2],
                texture_us=[0, 0, 0],
                texture_vs=[0, 0, 0],
                texture_alias="STONE",
                bitmap_index=0,
                polygon_type=0,
                attributes=0,
                plane_normal=(0, 0, 0),
                plane_distance=0,
            ),
            OdmFace(
                vertex_indices=[3, 4, 5],
                texture_us=[0, 0, 0],
                texture_vs=[0, 0, 0],
                texture_alias="STONE",
                bitmap_index=0,
                polygon_type=0,
                attributes=0,
                plane_normal=(0, 0, 0),
                plane_distance=0,
            ),
        ]
        bmodel.source_poly_for_face = [0, 1]
        dat_world = DatWorld(
            path=Path("test.dat"),
            version=66,
            object_data_pos=0,
            render_data_pos=0,
            world_model_pos=0,
            world_info=WorldInfo("", 0.0, (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
            world_models=[
                dummy_world_bsp(
                    "VisBSP",
                    leaves=[
                        WorldLeaf(0, None, [], [(0 << 16) | 1], 0),
                        WorldLeaf(0, None, [], [(1 << 16) | 1], 0),
                    ],
                ),
                dummy_world_bsp("Geometry", polies=[dummy_poly(), dummy_poly()]),
            ],
            objects=[],
        )

        layout = build_leaf_grid_layout(dat_world, [bmodel], 2, "STONE")

        self.assertEqual(layout.diagnostics["sector_mode"], "leaf_grid")
        self.assertEqual(layout.diagnostics["valid_leaf_polygon_refs"], 2)
        self.assertEqual(layout.diagnostics["matched_leaf_polygon_refs"], 2)
        self.assertEqual(layout.diagnostics["unassigned_source_triangles"], 0)
        self.assertEqual(len(layout.rooms), 2)
        self.assertEqual(len(layout.portals), 1)

    def test_leaf_grid_layout_adds_mm9_user_portal_hints(self) -> None:
        left = OdmBModel(name="left", source_model_index=1)
        left.vertices = [
            OdmVertex(-1000, 0, 0),
            OdmVertex(-900, 0, 0),
            OdmVertex(-1000, 100, 0),
        ]
        left.faces = [
            OdmFace(
                vertex_indices=[0, 1, 2],
                texture_us=[0, 0, 0],
                texture_vs=[0, 0, 0],
                texture_alias="STONE",
                bitmap_index=0,
                polygon_type=0,
                attributes=0,
                plane_normal=(0, 0, 0),
                plane_distance=0,
            )
        ]
        left.source_poly_for_face = [0]
        right = OdmBModel(name="right", source_model_index=2)
        right.vertices = [
            OdmVertex(900, 0, 0),
            OdmVertex(1000, 0, 0),
            OdmVertex(900, 100, 0),
        ]
        right.faces = [
            OdmFace(
                vertex_indices=[0, 1, 2],
                texture_us=[0, 0, 0],
                texture_vs=[0, 0, 0],
                texture_alias="STONE",
                bitmap_index=0,
                polygon_type=0,
                attributes=0,
                plane_normal=(0, 0, 0),
                plane_distance=0,
            )
        ]
        right.source_poly_for_face = [0]
        dat_world = DatWorld(
            path=Path("test.dat"),
            version=66,
            object_data_pos=0,
            render_data_pos=0,
            world_model_pos=0,
            world_info=WorldInfo("", 0.0, (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
            world_models=[
                dummy_world_bsp(
                    "VisBSP",
                    leaves=[
                        WorldLeaf(0, None, [], [(0 << 16) | 1], 0),
                        WorldLeaf(0, None, [], [(0 << 16) | 2], 0),
                    ],
                ),
                dummy_world_bsp("Left", polies=[dummy_poly()]),
                dummy_world_bsp("Right", polies=[dummy_poly()]),
            ],
            objects=[],
        )
        dat_world.world_models[0].user_portals = [
            UserPortal(
                name="DoorPortal",
                center=(0.0, 0.0, 0.0),
                dims=(0.0, 64.0, 64.0),
                unknown_int_1=0,
                unknown_int_2=0,
                unknown_short=0,
            )
        ]

        layout = build_leaf_grid_layout(dat_world, [left, right], 2, "STONE", 1.0)

        self.assertEqual(layout.diagnostics["dat_user_portals"], 1)
        self.assertEqual(layout.diagnostics["dat_user_portals_emitted"], 1)
        self.assertTrue(any(portal.source_kind == "mm9_user_portal" for portal in layout.portals))


if __name__ == "__main__":
    unittest.main()
