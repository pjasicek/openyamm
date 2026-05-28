#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from pygltflib import ARRAY_BUFFER, ELEMENT_ARRAY_BUFFER, FLOAT, UNSIGNED_INT, Material, Mesh, Node, Primitive

from convert_abc_model import GL_TRIANGLES, Buffer, GltfBuilder, align_blob
from mm9_units import MM9_TO_OPENYAMM_COORDINATE_SCALE
from transcode_mm9_dat_to_odm import (
    DatWorld,
    OdmBModel,
    OdmFace,
    OdmVertex,
    UserPortal,
    WorldLeaf,
    build_texture_size_index,
    read_dat_world,
    transcode_geometry,
    write_alias_bitmaps,
    write_material_aliases,
    write_raw_objects,
    yaml_scalar,
)


@dataclass
class SourceTriangle:
    material_name: str
    vertices: list[OdmVertex]
    uvs: list[tuple[int, int]]


@dataclass
class SourceRoom:
    room_id: int
    triangles: list[SourceTriangle] = field(default_factory=list)


@dataclass
class SourcePortal:
    front_room_id: int
    back_room_id: int
    material_name: str
    vertices: list[OdmVertex]
    source_kind: str = "synthetic"
    source_name: str = ""
    source_model_index: int = -1
    source_portal_index: int = -1


@dataclass
class SourceLayout:
    rooms: list[SourceRoom]
    portals: list[SourcePortal]
    diagnostics: dict[str, Any]


@dataclass(frozen=True)
class FaceRecordKey:
    model_index: int
    face_index: int


@dataclass
class FaceRecord:
    key: FaceRecordKey
    poly_key: tuple[int, int]
    bmodel: OdmBModel
    face: OdmFace
    centroid: tuple[float, float, float]


def face_centroid(vertices: list[OdmVertex], face: OdmFace) -> tuple[float, float, float]:
    count = max(1, len(face.vertex_indices))
    return (
        sum(vertices[index].x for index in face.vertex_indices) / count,
        sum(vertices[index].y for index in face.vertex_indices) / count,
        sum(vertices[index].z for index in face.vertex_indices) / count,
    )


def append_face_triangle(room: SourceRoom, bmodel: OdmBModel, face: OdmFace) -> None:
    room.triangles.append(SourceTriangle(
        material_name=face.texture_alias,
        vertices=[bmodel.vertices[index] for index in face.vertex_indices],
        uvs=list(zip(face.texture_us, face.texture_vs)),
    ))


def build_face_records(bmodels: list[OdmBModel]) -> list[FaceRecord]:
    records = []
    for bmodel in bmodels:
        for face_index, face in enumerate(bmodel.faces):
            source_poly_index = -1
            if face_index < len(bmodel.source_poly_for_face):
                source_poly_index = bmodel.source_poly_for_face[face_index]
            records.append(FaceRecord(
                key=FaceRecordKey(bmodel.source_model_index, face_index),
                poly_key=(bmodel.source_model_index, source_poly_index),
                bmodel=bmodel,
                face=face,
                centroid=face_centroid(bmodel.vertices, face),
            ))
    return records


def build_one_room_layout(bmodels: list[OdmBModel]) -> SourceLayout:
    room = SourceRoom(room_id=0)
    for bmodel in bmodels:
        for face in bmodel.faces:
            append_face_triangle(room, bmodel, face)
    return SourceLayout(rooms=[room], portals=[], diagnostics={"sector_mode": "one_room", "rooms": 1, "portals": 0})


def build_layout_from_cell_triangles(
    cell_triangles: dict[tuple[int, int], list[SourceTriangle]],
    portal_material_name: str,
    diagnostics: dict[str, Any],
) -> SourceLayout:
    occupied_cells = sorted(cell for cell, triangles in cell_triangles.items() if triangles)
    if not occupied_cells:
        return SourceLayout(rooms=[], portals=[], diagnostics={**diagnostics, "rooms": 0, "portals": 0})

    cell_to_room_id = {cell: room_id for room_id, cell in enumerate(occupied_cells)}
    rooms = [
        SourceRoom(room_id=cell_to_room_id[cell], triangles=list(cell_triangles[cell]))
        for cell in occupied_cells
    ]
    bounds_by_room_id = {room.room_id: room_bounds(room) for room in rooms}
    portal_pairs: set[tuple[int, int]] = set()

    for cell, room_id in cell_to_room_id.items():
        for neighbor in ((cell[0] + 1, cell[1]), (cell[0], cell[1] + 1)):
            neighbor_room_id = cell_to_room_id.get(neighbor)
            if neighbor_room_id is not None:
                portal_pairs.add(tuple(sorted((room_id, neighbor_room_id))))

    bridged_pairs: set[tuple[int, int]] = set()
    connected = {0}
    remaining = {room.room_id for room in rooms if room.room_id != 0}
    while remaining:
        best_pair: tuple[int, int] | None = None
        best_distance = float("inf")
        for left_id in connected:
            left_bounds = bounds_by_room_id[left_id]
            left_center = ((left_bounds[0] + left_bounds[1]) * 0.5, (left_bounds[2] + left_bounds[3]) * 0.5)
            for right_id in remaining:
                right_bounds = bounds_by_room_id[right_id]
                right_center = ((right_bounds[0] + right_bounds[1]) * 0.5, (right_bounds[2] + right_bounds[3]) * 0.5)
                distance = (left_center[0] - right_center[0]) ** 2 + (left_center[1] - right_center[1]) ** 2
                if distance < best_distance:
                    best_distance = distance
                    best_pair = (left_id, right_id)
        if best_pair is None:
            break
        pair = tuple(sorted(best_pair))
        portal_pairs.add(pair)
        bridged_pairs.add(pair)
        connected.add(best_pair[1])
        remaining.remove(best_pair[1])

    portals = [
        build_portal_quad(
            left_id,
            right_id,
            bounds_by_room_id[left_id],
            bounds_by_room_id[right_id],
            portal_material_name,
        )
        for left_id, right_id in sorted(portal_pairs)
    ]
    return SourceLayout(
        rooms=rooms,
        portals=portals,
        diagnostics={
            **diagnostics,
            "rooms": len(rooms),
            "portals": len(portals),
            "synthetic_bridge_portals": len(bridged_pairs),
        },
    )


def portal_node_name(portal_index: int, portal: SourcePortal) -> str:
    return f"PORTAL_{portal_index}_{portal.front_room_id}_{portal.back_room_id}"


def room_bounds(room: SourceRoom) -> tuple[int, int, int, int, int, int]:
    vertices = [vertex for triangle in room.triangles for vertex in triangle.vertices]
    return (
        min(vertex.x for vertex in vertices),
        max(vertex.x for vertex in vertices),
        min(vertex.y for vertex in vertices),
        max(vertex.y for vertex in vertices),
        min(vertex.z for vertex in vertices),
        max(vertex.z for vertex in vertices),
    )


def build_portal_quad(
    front_room_id: int,
    back_room_id: int,
    front_bounds: tuple[int, int, int, int, int, int],
    back_bounds: tuple[int, int, int, int, int, int],
    material_name: str,
) -> SourcePortal:
    min_x = max(front_bounds[0], back_bounds[0])
    max_x = min(front_bounds[1], back_bounds[1])
    min_y = max(front_bounds[2], back_bounds[2])
    max_y = min(front_bounds[3], back_bounds[3])
    min_z = max(front_bounds[4], back_bounds[4])
    max_z = min(front_bounds[5], back_bounds[5])

    front_center_x = (front_bounds[0] + front_bounds[1]) // 2
    front_center_y = (front_bounds[2] + front_bounds[3]) // 2
    back_center_x = (back_bounds[0] + back_bounds[1]) // 2
    back_center_y = (back_bounds[2] + back_bounds[3]) // 2

    if min_z >= max_z:
        min_z = min(front_bounds[4], back_bounds[4])
        max_z = max(front_bounds[5], back_bounds[5])
    if max_z - min_z < 256:
        center_z = (min_z + max_z) // 2
        min_z = center_z - 128
        max_z = center_z + 128

    if abs(front_center_x - back_center_x) >= abs(front_center_y - back_center_y):
        x = (front_center_x + back_center_x) // 2
        if min_y >= max_y:
            center_y = (front_center_y + back_center_y) // 2
            min_y = center_y - 512
            max_y = center_y + 512
        vertices = [
            OdmVertex(x, min_y, min_z),
            OdmVertex(x, max_y, min_z),
            OdmVertex(x, max_y, max_z),
            OdmVertex(x, min_y, max_z),
        ]
    else:
        y = (front_center_y + back_center_y) // 2
        if min_x >= max_x:
            center_x = (front_center_x + back_center_x) // 2
            min_x = center_x - 512
            max_x = center_x + 512
        vertices = [
            OdmVertex(min_x, y, min_z),
            OdmVertex(max_x, y, min_z),
            OdmVertex(max_x, y, max_z),
            OdmVertex(min_x, y, max_z),
        ]

    return SourcePortal(
        front_room_id=front_room_id,
        back_room_id=back_room_id,
        material_name=material_name,
        vertices=vertices,
    )


def lt_point_to_openyamm_vertex(point: tuple[float, float, float], coordinate_scale: float) -> OdmVertex:
    return OdmVertex(
        int(round(point[0] * coordinate_scale)),
        int(round(point[2] * coordinate_scale)),
        int(round(point[1] * coordinate_scale)),
    )


def lt_dims_to_openyamm_tuple(dims: tuple[float, float, float], coordinate_scale: float) -> tuple[float, float, float]:
    return (
        abs(dims[0] * coordinate_scale),
        abs(dims[2] * coordinate_scale),
        abs(dims[1] * coordinate_scale),
    )


def room_center(bounds: tuple[int, int, int, int, int, int]) -> tuple[float, float, float]:
    return (
        (bounds[0] + bounds[1]) * 0.5,
        (bounds[2] + bounds[3]) * 0.5,
        (bounds[4] + bounds[5]) * 0.5,
    )


def portal_normal_axis(dims: tuple[float, float, float]) -> int:
    return min(range(3), key=lambda index: dims[index])


def choose_portal_rooms(
    center: OdmVertex,
    dims: tuple[float, float, float],
    bounds_by_room_id: dict[int, tuple[int, int, int, int, int, int]],
) -> tuple[int, int] | None:
    if len(bounds_by_room_id) < 2:
        return None

    center_values = (float(center.x), float(center.y), float(center.z))
    axis = portal_normal_axis(dims)
    negative_side: list[tuple[float, int]] = []
    positive_side: list[tuple[float, int]] = []
    distances: list[tuple[float, int]] = []
    for room_id, bounds in bounds_by_room_id.items():
        candidate_center = room_center(bounds)
        axis_delta = candidate_center[axis] - center_values[axis]
        distance = (
            (candidate_center[0] - center_values[0]) ** 2
            + (candidate_center[1] - center_values[1]) ** 2
            + (candidate_center[2] - center_values[2]) ** 2
        )
        distances.append((distance, room_id))
        if axis_delta < 0:
            negative_side.append((abs(axis_delta), room_id))
        elif axis_delta > 0:
            positive_side.append((abs(axis_delta), room_id))

    if negative_side and positive_side:
        left_id = min(negative_side)[1]
        right_id = min(positive_side)[1]
        return tuple(sorted((left_id, right_id)))

    nearest = sorted(distances)[:2]
    if len(nearest) < 2:
        return None
    return tuple(sorted((nearest[0][1], nearest[1][1])))


def build_user_portal_quad(
    portal: UserPortal,
    front_room_id: int,
    back_room_id: int,
    source_model_index: int,
    source_portal_index: int,
    material_name: str,
    coordinate_scale: float,
) -> SourcePortal | None:
    center = lt_point_to_openyamm_vertex(portal.center, coordinate_scale)
    dims = lt_dims_to_openyamm_tuple(portal.dims, coordinate_scale)
    axis = portal_normal_axis(dims)
    axes = [0, 1, 2]
    axes.remove(axis)

    center_values = [center.x, center.y, center.z]
    spans = [max(128.0, dims[index]) for index in range(3)]

    vertices = []
    for sign_a, sign_b in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        values = list(center_values)
        values[axes[0]] = int(round(center_values[axes[0]] + sign_a * spans[axes[0]]))
        values[axes[1]] = int(round(center_values[axes[1]] + sign_b * spans[axes[1]]))
        vertices.append(OdmVertex(values[0], values[1], values[2]))

    if len({(vertex.x, vertex.y, vertex.z) for vertex in vertices}) < 4:
        return None

    return SourcePortal(
        front_room_id=front_room_id,
        back_room_id=back_room_id,
        material_name=material_name,
        vertices=vertices,
        source_kind="mm9_user_portal",
        source_name=portal.name,
        source_model_index=source_model_index,
        source_portal_index=source_portal_index,
    )


def add_user_portals_to_layout(
    layout: SourceLayout,
    dat_world: DatWorld,
    portal_material_name: str,
    coordinate_scale: float,
) -> SourceLayout:
    if len(layout.rooms) < 2:
        layout.diagnostics["dat_user_portals"] = sum(len(model.user_portals) for model in dat_world.world_models)
        layout.diagnostics["dat_user_portals_emitted"] = 0
        layout.diagnostics["dat_user_portals_skipped"] = layout.diagnostics["dat_user_portals"]
        return layout

    bounds_by_room_id = {room.room_id: room_bounds(room) for room in layout.rooms}
    user_portals: list[SourcePortal] = []
    skipped = 0
    duplicate_pairs: set[tuple[int, int]] = set()

    for model_index, model in enumerate(dat_world.world_models):
        for portal_index, portal in enumerate(model.user_portals):
            center = lt_point_to_openyamm_vertex(portal.center, coordinate_scale)
            dims = lt_dims_to_openyamm_tuple(portal.dims, coordinate_scale)
            room_pair = choose_portal_rooms(center, dims, bounds_by_room_id)
            if room_pair is None or room_pair[0] == room_pair[1]:
                skipped += 1
                continue
            source_portal = build_user_portal_quad(
                portal,
                room_pair[0],
                room_pair[1],
                model_index,
                portal_index,
                portal_material_name,
                coordinate_scale,
            )
            if source_portal is None:
                skipped += 1
                continue
            if any(
                existing.source_kind == "mm9_user_portal"
                and tuple(sorted((existing.front_room_id, existing.back_room_id))) == room_pair
                and existing.source_name == source_portal.source_name
                for existing in user_portals
            ):
                duplicate_pairs.add(room_pair)
                skipped += 1
                continue
            user_portals.append(source_portal)

    user_portal_pairs = {
        tuple(sorted((portal.front_room_id, portal.back_room_id)))
        for portal in user_portals
    }
    retained_portals = [
        portal
        for portal in layout.portals
        if portal.source_kind != "synthetic"
        or tuple(sorted((portal.front_room_id, portal.back_room_id))) not in user_portal_pairs
    ]
    removed_synthetic = len(layout.portals) - len(retained_portals)
    layout.portals = retained_portals + user_portals
    layout.diagnostics["dat_user_portals"] = sum(len(model.user_portals) for model in dat_world.world_models)
    layout.diagnostics["dat_user_portals_emitted"] = len(user_portals)
    layout.diagnostics["dat_user_portals_skipped"] = skipped
    layout.diagnostics["dat_user_portal_duplicate_pairs"] = len(duplicate_pairs)
    layout.diagnostics["synthetic_portals_replaced_by_dat_user_portals"] = removed_synthetic
    layout.diagnostics["portals"] = len(layout.portals)
    return layout


def build_spatial_grid_layout(bmodels: list[OdmBModel], grid_size: int, portal_material_name: str) -> SourceLayout:
    grid_size = max(1, grid_size)
    if grid_size == 1:
        return build_one_room_layout(bmodels)

    centroids: list[tuple[OdmBModel, OdmFace, tuple[float, float, float]]] = []
    for bmodel in bmodels:
        for face in bmodel.faces:
            centroids.append((bmodel, face, face_centroid(bmodel.vertices, face)))

    if not centroids:
        return build_one_room_layout(bmodels)

    min_x = min(centroid[0] for _, _, centroid in centroids)
    max_x = max(centroid[0] for _, _, centroid in centroids)
    min_y = min(centroid[1] for _, _, centroid in centroids)
    max_y = max(centroid[1] for _, _, centroid in centroids)
    width = max(1.0, max_x - min_x)
    depth = max(1.0, max_y - min_y)

    rooms_by_cell: dict[tuple[int, int], SourceRoom] = {}
    for bmodel, face, centroid in centroids:
        grid_x = min(grid_size - 1, max(0, int((centroid[0] - min_x) * grid_size / width)))
        grid_y = min(grid_size - 1, max(0, int((centroid[1] - min_y) * grid_size / depth)))
        cell = (grid_x, grid_y)
        room = rooms_by_cell.get(cell)
        if room is None:
            room = SourceRoom(room_id=len(rooms_by_cell))
            rooms_by_cell[cell] = room
        append_face_triangle(room, bmodel, face)

    rooms = sorted(rooms_by_cell.values(), key=lambda room: room.room_id)
    room_id_by_cell = {cell: room.room_id for cell, room in rooms_by_cell.items()}
    bounds_by_room_id = {room.room_id: room_bounds(room) for room in rooms}
    portal_pairs: set[tuple[int, int]] = set()

    for cell, room_id in room_id_by_cell.items():
        for neighbor in ((cell[0] + 1, cell[1]), (cell[0], cell[1] + 1)):
            neighbor_room_id = room_id_by_cell.get(neighbor)
            if neighbor_room_id is not None:
                portal_pairs.add(tuple(sorted((room_id, neighbor_room_id))))

    bridged_pairs: set[tuple[int, int]] = set()
    connected = {0}
    remaining = {room.room_id for room in rooms if room.room_id != 0}
    while remaining:
        best_pair: tuple[int, int] | None = None
        best_distance = float("inf")
        for left_id in connected:
            left_bounds = bounds_by_room_id[left_id]
            left_center = ((left_bounds[0] + left_bounds[1]) * 0.5, (left_bounds[2] + left_bounds[3]) * 0.5)
            for right_id in remaining:
                right_bounds = bounds_by_room_id[right_id]
                right_center = ((right_bounds[0] + right_bounds[1]) * 0.5, (right_bounds[2] + right_bounds[3]) * 0.5)
                distance = (left_center[0] - right_center[0]) ** 2 + (left_center[1] - right_center[1]) ** 2
                if distance < best_distance:
                    best_distance = distance
                    best_pair = (left_id, right_id)
        if best_pair is None:
            break
        pair = tuple(sorted(best_pair))
        portal_pairs.add(pair)
        bridged_pairs.add(pair)
        connected.add(best_pair[1])
        remaining.remove(best_pair[1])

    portals = [
        build_portal_quad(
            left_id,
            right_id,
            bounds_by_room_id[left_id],
            bounds_by_room_id[right_id],
            portal_material_name,
        )
        for left_id, right_id in sorted(portal_pairs)
    ]

    return SourceLayout(
        rooms=rooms,
        portals=portals,
        diagnostics={
            "sector_mode": "spatial_grid",
            "grid_size": grid_size,
            "rooms": len(rooms),
            "portals": len(portals),
            "synthetic_bridge_portals": len(bridged_pairs),
            "source_triangles": len(centroids),
        },
    )


def grid_cell_for_point(
    point: tuple[float, float, float],
    min_x: float,
    max_x: float,
    min_y: float,
    max_y: float,
    grid_size: int,
) -> tuple[int, int]:
    width = max(1.0, max_x - min_x)
    depth = max(1.0, max_y - min_y)
    grid_x = min(grid_size - 1, max(0, int((point[0] - min_x) * grid_size / width)))
    grid_y = min(grid_size - 1, max(0, int((point[1] - min_y) * grid_size / depth)))
    return grid_x, grid_y


def bounds_from_face_records(records: list[FaceRecord]) -> tuple[float, float, float, float]:
    return (
        min(record.centroid[0] for record in records),
        max(record.centroid[0] for record in records),
        min(record.centroid[1] for record in records),
        max(record.centroid[1] for record in records),
    )


def leaf_ref_keys(leaf: WorldLeaf) -> list[tuple[int, int]]:
    return [(polygon_ref.world_model_index, polygon_ref.poly_index) for polygon_ref in leaf.polygon_refs()]


def build_leaf_grid_layout(
    dat_world: DatWorld,
    bmodels: list[OdmBModel],
    grid_size: int,
    portal_material_name: str,
    coordinate_scale: float = 1.0,
) -> SourceLayout:
    grid_size = max(1, grid_size)
    records = build_face_records(bmodels)
    if grid_size == 1 or not records:
        return build_one_room_layout(bmodels)

    vis_model = next((model for model in dat_world.world_models if model.name == "VisBSP" and model.leaves), None)
    if vis_model is None:
        fallback = build_spatial_grid_layout(bmodels, grid_size, portal_material_name)
        fallback.diagnostics["requested_sector_mode"] = "leaf_grid"
        fallback.diagnostics["leaf_grid_fallback_reason"] = "missing_visbsp_leaves"
        return add_user_portals_to_layout(fallback, dat_world, portal_material_name, coordinate_scale)

    poly_records: dict[tuple[int, int], list[FaceRecord]] = defaultdict(list)
    for record in records:
        poly_records[record.poly_key].append(record)

    min_x, max_x, min_y, max_y = bounds_from_face_records(records)
    cell_triangles: dict[tuple[int, int], list[SourceTriangle]] = defaultdict(list)
    assigned_face_keys: set[FaceRecordKey] = set()
    valid_leaf_ref_count = 0
    matched_leaf_ref_count = 0
    invalid_model_ref_count = 0
    invalid_poly_ref_count = 0
    leaves_with_geometry = 0

    for leaf in vis_model.leaves:
        leaf_records: list[FaceRecord] = []
        for polygon_ref in leaf.polygon_refs():
            if polygon_ref.world_model_index >= len(dat_world.world_models):
                invalid_model_ref_count += 1
                continue
            referenced_model = dat_world.world_models[polygon_ref.world_model_index]
            if polygon_ref.poly_index >= len(referenced_model.polies):
                invalid_poly_ref_count += 1
                continue
            valid_leaf_ref_count += 1
            matching_records = poly_records.get((polygon_ref.world_model_index, polygon_ref.poly_index), [])
            if not matching_records:
                continue
            matched_leaf_ref_count += 1
            leaf_records.extend(matching_records)

        unique_leaf_records = []
        seen_leaf_face_keys: set[FaceRecordKey] = set()
        for record in leaf_records:
            if record.key in seen_leaf_face_keys:
                continue
            seen_leaf_face_keys.add(record.key)
            unique_leaf_records.append(record)
        if not unique_leaf_records:
            continue

        leaves_with_geometry += 1
        leaf_center = (
            sum(record.centroid[0] for record in unique_leaf_records) / len(unique_leaf_records),
            sum(record.centroid[1] for record in unique_leaf_records) / len(unique_leaf_records),
            sum(record.centroid[2] for record in unique_leaf_records) / len(unique_leaf_records),
        )
        cell = grid_cell_for_point(leaf_center, min_x, max_x, min_y, max_y, grid_size)
        for record in unique_leaf_records:
            if record.key in assigned_face_keys:
                continue
            assigned_face_keys.add(record.key)
            cell_triangles[cell].append(SourceTriangle(
                material_name=record.face.texture_alias,
                vertices=[record.bmodel.vertices[index] for index in record.face.vertex_indices],
                uvs=list(zip(record.face.texture_us, record.face.texture_vs)),
            ))

    unassigned_face_count = 0
    for record in records:
        if record.key in assigned_face_keys:
            continue
        cell = grid_cell_for_point(record.centroid, min_x, max_x, min_y, max_y, grid_size)
        cell_triangles[cell].append(SourceTriangle(
            material_name=record.face.texture_alias,
            vertices=[record.bmodel.vertices[index] for index in record.face.vertex_indices],
            uvs=list(zip(record.face.texture_us, record.face.texture_vs)),
        ))
        unassigned_face_count += 1

    layout = build_layout_from_cell_triangles(
        cell_triangles,
        portal_material_name,
        {
            "sector_mode": "leaf_grid",
            "grid_size": grid_size,
            "visbsp_leaves": len(vis_model.leaves),
            "visbsp_leaf_polygon_entries": sum(len(leaf.polygon_entries) for leaf in vis_model.leaves),
            "valid_leaf_polygon_refs": valid_leaf_ref_count,
            "matched_leaf_polygon_refs": matched_leaf_ref_count,
            "invalid_leaf_model_refs": invalid_model_ref_count,
            "invalid_leaf_poly_refs": invalid_poly_ref_count,
            "leaves_with_geometry": leaves_with_geometry,
            "unassigned_source_triangles": unassigned_face_count,
            "source_triangles": len(records),
        },
    )
    return add_user_portals_to_layout(layout, dat_world, portal_material_name, coordinate_scale)


def build_source_layout(
    dat_world: DatWorld,
    bmodels: list[OdmBModel],
    sector_mode: str,
    sector_grid: int,
    aliases: dict[str, dict[str, Any]],
    coordinate_scale: float,
) -> SourceLayout:
    portal_material_name = next(iter(sorted(aliases)), "DEFAULT")
    if sector_mode == "one_room":
        return build_one_room_layout(bmodels)
    if sector_mode == "leaf_grid":
        return build_leaf_grid_layout(dat_world, bmodels, sector_grid, portal_material_name, coordinate_scale)
    if sector_mode == "spatial_grid":
        layout = build_spatial_grid_layout(bmodels, sector_grid, portal_material_name)
        return add_user_portals_to_layout(layout, dat_world, portal_material_name, coordinate_scale)
    raise ValueError(f"unknown sector mode: {sector_mode}")


def append_mesh_from_triangles(
    builder: GltfBuilder,
    name: str,
    triangles_by_material: dict[str, list[SourceTriangle]],
    material_indices: dict[str, int],
) -> tuple[int, int]:
    primitives = []
    total_vertices = 0
    total_triangles = 0

    for material_name, triangles in sorted(triangles_by_material.items()):
        if not triangles:
            continue
        vertex_lookup: dict[tuple[int, int, int, int, int], int] = {}
        positions_list: list[tuple[float, float, float]] = []
        texcoords_list: list[tuple[float, float]] = []
        indices_list: list[int] = []

        for triangle in triangles:
            for vertex, uv in zip(triangle.vertices, triangle.uvs):
                key = (vertex.x, vertex.y, vertex.z, uv[0], uv[1])
                vertex_index = vertex_lookup.get(key)

                if vertex_index is None:
                    vertex_index = len(positions_list)
                    vertex_lookup[key] = vertex_index
                    positions_list.append((float(vertex.x), float(vertex.y), float(vertex.z)))
                    texcoords_list.append((float(uv[0]) / 256.0, float(uv[1]) / 256.0))

                indices_list.append(vertex_index)

        positions = np.array(
            positions_list,
            dtype=np.float32,
        )
        texcoords = np.array(
            texcoords_list,
            dtype=np.float32,
        )
        indices = np.array(indices_list, dtype=np.uint32)
        position_accessor = builder.add_accessor(positions, FLOAT, "VEC3", ARRAY_BUFFER)
        texcoord_accessor = builder.add_accessor(texcoords, FLOAT, "VEC2", ARRAY_BUFFER)
        index_accessor = builder.add_accessor(indices, UNSIGNED_INT, "SCALAR", ELEMENT_ARRAY_BUFFER)
        primitives.append(Primitive(
            attributes={
                "POSITION": position_accessor,
                "TEXCOORD_0": texcoord_accessor,
            },
            indices=index_accessor,
            material=material_indices[material_name],
            mode=GL_TRIANGLES,
        ))
        total_vertices += len(positions)
        total_triangles += len(indices) // 3

    if not primitives:
        return 0, 0

    mesh_index = len(builder.gltf.meshes)
    builder.gltf.meshes.append(Mesh(name=name, primitives=primitives))
    builder.gltf.nodes.append(Node(name=name, mesh=mesh_index))
    builder.gltf.scenes[0].nodes.append(len(builder.gltf.nodes) - 1)
    return total_vertices, total_triangles


def write_source_glb(path: Path, layout: SourceLayout) -> dict[str, int]:
    builder = GltfBuilder()
    builder.gltf.asset.generator = "OpenYAMM MM9 DAT indoor source converter"

    material_names = {triangle.material_name for room in layout.rooms for triangle in room.triangles}
    material_names.update(portal.material_name for portal in layout.portals)

    material_indices: dict[str, int] = {}
    for material_name in sorted(material_names):
        material_indices[material_name] = len(builder.gltf.materials)
        builder.gltf.materials.append(Material(name=material_name))

    total_vertices = 0
    total_triangles = 0

    for room in layout.rooms:
        triangles_by_material: dict[str, list[SourceTriangle]] = defaultdict(list)
        for triangle in room.triangles:
            triangles_by_material[triangle.material_name].append(triangle)
        vertices, triangles = append_mesh_from_triangles(
            builder,
            f"ROOM_{room.room_id}",
            triangles_by_material,
            material_indices,
        )
        total_vertices += vertices
        total_triangles += triangles

    for portal_index, portal in enumerate(layout.portals):
        triangles = [
            SourceTriangle(
                material_name=portal.material_name,
                vertices=[portal.vertices[0], portal.vertices[1], portal.vertices[2]],
                uvs=[(0, 0), (256, 0), (256, 256)],
            ),
            SourceTriangle(
                material_name=portal.material_name,
                vertices=[portal.vertices[0], portal.vertices[2], portal.vertices[3]],
                uvs=[(0, 0), (256, 256), (0, 256)],
            ),
        ]
        vertices, emitted_triangles = append_mesh_from_triangles(
            builder,
            portal_node_name(portal_index, portal),
            {portal.material_name: triangles},
            material_indices,
        )
        total_vertices += vertices
        total_triangles += emitted_triangles

    align_blob(builder.blob)
    builder.gltf.buffers = [Buffer(byteLength=len(builder.blob))]
    builder.gltf.set_binary_blob(bytes(builder.blob))
    path.parent.mkdir(parents=True, exist_ok=True)
    builder.gltf.save_binary(str(path))
    return {
        "source_glb_vertices": total_vertices,
        "source_glb_triangles": total_triangles,
        "source_glb_materials": len(material_indices),
        "source_glb_rooms": len(layout.rooms),
        "source_glb_portals": len(layout.portals),
    }


def write_geometry_metadata(
    path: Path,
    output_name: str,
    source_glb_name: str,
    aliases: dict[str, dict[str, Any]],
    layout: SourceLayout,
) -> None:
    lines = [
        "format_version: 2",
        'kind: "indoor_geometry"',
        f"map_file: {yaml_scalar(output_name + '.blv')}",
        "source:",
        f"  asset_path: {yaml_scalar(source_glb_name)}",
        '  coordinate_system: "openyamm_mm9_lithtech_dat"',
        "  unit_scale: 1",
        "import:",
        '  source_format: "glb"',
        "  merge_vertices_epsilon: 0",
        "  merge_coplanar_faces: true",
        "  triangulate_ngons: true",
        "  generate_bsp: false",
        "  generate_outlines: false",
        "  generate_portals: false",
        "materials:",
    ]
    for alias in sorted(aliases):
        lines.extend([
            f"  - id: {yaml_scalar(alias.lower())}",
            f"    source_material: {yaml_scalar(alias)}",
            f"    texture: {yaml_scalar(alias)}",
        ])
    lines.append("rooms:")
    for room in layout.rooms:
        lines.extend([
            f'  - id: "room_{room.room_id}"',
            f'    name: "MM9 DAT sector {room.room_id}"',
            f"    room_id: {room.room_id + 1}",
            "    source_nodes:",
            f'      - "ROOM_{room.room_id}"',
            f"    runtime_sector_index: {room.room_id}",
        ])

    if layout.portals:
        lines.append("portals:")
        for portal_index, portal in enumerate(layout.portals):
            portal_id = f"portal_{portal_index}_{portal.front_room_id}_{portal.back_room_id}"
            source_node = portal_node_name(portal_index, portal)
            lines.extend([
                f"  - id: {yaml_scalar(portal_id)}",
                f"    source_node: {yaml_scalar(source_node)}",
                f'    front_room: "room_{portal.front_room_id}"',
                f'    back_room: "room_{portal.back_room_id}"',
                f"    portal_id: {portal_index + 1}",
                f"    source_kind: {yaml_scalar(portal.source_kind)}",
            ])
            if portal.source_name:
                lines.append(f"    source_name: {yaml_scalar(portal.source_name)}")
            if portal.source_model_index >= 0:
                lines.append(f"    source_model_index: {portal.source_model_index}")
            if portal.source_portal_index >= 0:
                lines.append(f"    source_portal_index: {portal.source_portal_index}")
    else:
        lines.append("portals: []")

    lines.extend([
        "surfaces: []",
        "mechanisms: []",
        "entities: []",
        "lights: []",
        "spawns: []",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_scene_yml(path: Path, output_name: str) -> None:
    zero_outline_hex = "00" * 875
    zero_map_vars = ", ".join(["0"] * 75)
    zero_decor_vars = ", ".join(["0"] * 125)
    path.write_text(
        f"""format_version: 1
kind: "indoor_scene"
source:
  geometry_file: "{output_name}.blv"
runtime_restrictions:
  allow_save_game: false
  allow_lloyds_beacon: false
  arena: false
environment:
  last_visit_time: 0
  sky_texture: ""
  day_bits_raw: 0
  map_extra_bits_raw: 0
  flags:
    foggy: false
    raining: false
    snowing: false
    underwater: false
    no_terrain: false
    always_dark: false
    always_light: false
    always_foggy: false
    red_fog: false
  fog:
    weak_distance: 0
    strong_distance: 0
  ceiling: 32767
  map_extra_reserved_hex: "000000000000ff7f00000000000000000000000000000000"
spawns: []
initial_state:
  location:
    respawn_count: 0
    last_respawn_day: 0
    reputation: 0
    alert_status: 0
  visible_outlines:
    bitset_hex: "{zero_outline_hex}"
  face_attribute_overrides: []
  decoration_flags: []
  actors: []
  sprite_objects: []
  chests: []
  doors: []
  variables:
    map: [{zero_map_vars}]
    decor: [{zero_decor_vars}]
""",
        encoding="utf-8",
    )


def write_bsp_diagnostics(path: Path, dat_world: DatWorld, layout: SourceLayout) -> None:
    lines = [
        "format_version: 1",
        'kind: "mm9_bsp_diagnostics"',
        "source:",
        f"  source_dat: {yaml_scalar(str(dat_world.path))}",
        "layout:",
    ]
    for key, value in layout.diagnostics.items():
        lines.append(f"  {key}: {yaml_scalar(value) if isinstance(value, str) else value}")
    lines.append("world_models:")
    for index, model in enumerate(dat_world.world_models):
        leaf_polygon_entry_count = sum(len(leaf.polygon_entries) for leaf in model.leaves)
        leaf_portal_data_count = sum(len(leaf.portal_data) for leaf in model.leaves)
        indexed_leaf_count = sum(1 for leaf in model.leaves if leaf.index is not None)
        polygon_refs = [
            polygon_ref
            for leaf in model.leaves
            for polygon_ref in leaf.polygon_refs()
        ]
        invalid_model_refs = sum(
            1
            for polygon_ref in polygon_refs
            if polygon_ref.world_model_index >= len(dat_world.world_models)
        )
        invalid_poly_refs = sum(
            1
            for polygon_ref in polygon_refs
            if polygon_ref.world_model_index < len(dat_world.world_models)
            and polygon_ref.poly_index >= len(dat_world.world_models[polygon_ref.world_model_index].polies)
        )
        valid_global_refs = len(polygon_refs) - invalid_model_refs - invalid_poly_refs
        referenced_model_indices = sorted({polygon_ref.world_model_index for polygon_ref in polygon_refs})
        lines.extend([
            f"  - index: {index}",
            f"    name: {yaml_scalar(model.name)}",
            f"    points: {len(model.points)}",
            f"    polies: {len(model.polies)}",
            f"    planes: {len(model.planes)}",
            f"    surfaces: {len(model.surfaces)}",
            f"    nodes: {len(model.nodes)}",
            f"    leaves: {len(model.leaves)}",
            f"    user_portals: {len(model.user_portals)}",
            f"    section_count: {model.section_count}",
            f"    leaf_list_count: {model.counts.get('leaf_list_count', 0)}",
            f"    total_vis_list_size: {model.counts.get('total_vis_list_size', 0)}",
            f"    leaf_portal_data_entries: {leaf_portal_data_count}",
            f"    indexed_leaf_references: {indexed_leaf_count}",
            f"    leaf_polygon_entries: {leaf_polygon_entry_count}",
            f"    leaf_polygon_ref_poly_min: {min((ref.poly_index for ref in polygon_refs), default=0)}",
            f"    leaf_polygon_ref_poly_max: {max((ref.poly_index for ref in polygon_refs), default=0)}",
            f"    leaf_polygon_valid_global_refs: {valid_global_refs}",
            f"    leaf_polygon_invalid_model_refs: {invalid_model_refs}",
            f"    leaf_polygon_invalid_poly_refs: {invalid_poly_refs}",
            "    leaf_polygon_ref_world_models_sample: ["
            + ", ".join(str(value) for value in referenced_model_indices[:32])
            + "]",
        ])
        if model.leaves:
            first_leaf = model.leaves[0]
            lines.extend([
                "    first_leaf:",
                f"      count: {first_leaf.count}",
                f"      index: {first_leaf.index if first_leaf.index is not None else -1}",
                f"      portal_data_entries: {len(first_leaf.portal_data)}",
                f"      polygon_entries: {len(first_leaf.polygon_entries)}",
                "      polygon_ref_indices_sample: ["
                + ", ".join(str(value) for value in first_leaf.polygon_ref_indices()[:16])
                + "]",
                "      polygon_refs_sample:",
            ])
            for polygon_ref in first_leaf.polygon_refs()[:8]:
                lines.extend([
                    f"        - world_model_index: {polygon_ref.world_model_index}",
                    f"          poly_index: {polygon_ref.poly_index}",
                    f"          raw_entry: {polygon_ref.raw_entry}",
                ])
        if model.nodes:
            first_node = model.nodes[0]
            lines.extend([
                "    first_node:",
                f"      poly_index: {first_node.poly_index}",
                f"      leaf_index: {first_node.leaf_index}",
                f"      front_index: {first_node.front_index}",
                f"      back_index: {first_node.back_index}",
            ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_source_metadata(
    path: Path,
    source_dat: Path,
    output_name: str,
    bitmap_dir: Path,
    coordinate_scale: float,
    layout: SourceLayout,
    dat_world: DatWorld,
    stats: dict[str, Any],
    source_glb_stats: dict[str, int],
) -> None:
    lines = [
        "format_version: 1",
        'kind: "mm9_indoor_source_metadata"',
        "source:",
        '  source_kind: "mm9_dat"',
        f"  source_dat: {yaml_scalar(str(source_dat))}",
        f"  coordinate_scale: {coordinate_scale:.8g}",
        "target:",
        '  classification: "indoor_like"',
        '  strategy: "sectorized_blv_prototype"',
        f"  geometry_file: {yaml_scalar(output_name + '.blv')}",
        f"  scene_file: {yaml_scalar(output_name + '.scene.yml')}",
        f"  source_glb: {yaml_scalar(output_name + '.source.glb')}",
        f"  geometry_metadata: {yaml_scalar(output_name + '.geometry.yml')}",
        f"  bsp_diagnostics: {yaml_scalar(output_name + '.bsp.yml')}",
        f"  bitmap_alias_dir: {yaml_scalar(str(bitmap_dir))}",
        f"source_world_models: {len(dat_world.world_models)}",
        f"source_objects: {len(dat_world.objects)}",
        "layout:",
    ]
    for key, value in layout.diagnostics.items():
        lines.append(f"  {key}: {yaml_scalar(value) if isinstance(value, str) else value}")
    lines.extend([
        "stats:",
    ])
    for key, value in {**stats, **source_glb_stats}.items():
        lines.append(f"  {key}: {value}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def compile_blv(compile_tool: Path, source_glb: Path, geometry_metadata: Path, output_blv: Path) -> None:
    subprocess.run(
        [str(compile_tool), str(source_glb), str(geometry_metadata), str(output_blv)],
        check=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Transcode an MM9 LithTech DAT dungeon into a BLV prototype.")
    parser.add_argument("--dat", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--name", default=None)
    parser.add_argument(
        "--scale",
        default=MM9_TO_OPENYAMM_COORDINATE_SCALE,
        type=float,
        help="Coordinate scale from LithTech units to OpenYAMM units",
    )
    parser.add_argument("--extracted-root", default=Path("mm9/extracted"), type=Path)
    parser.add_argument(
        "--sector-mode",
        choices=("one_room", "spatial_grid", "leaf_grid"),
        default="leaf_grid",
        help="BLV sector authoring strategy. leaf_grid uses decoded VisBSP leaf polygon references when present.",
    )
    parser.add_argument(
        "--sector-grid",
        default=4,
        type=int,
        help="Grid resolution for --sector-mode spatial_grid.",
    )
    parser.add_argument(
        "--bitmap-dir",
        type=Path,
        help=(
            "Directory for generated BLV texture aliases. Defaults to the sibling world textures directory "
            "because indoor BLV lookup resolves Data/bitmaps through package textures."
        ),
    )
    parser.add_argument(
        "--compile-tool",
        type=Path,
        help="Optional mm9_compile_indoor_source executable. When supplied, writes the .blv too.",
    )
    args = parser.parse_args()

    output_name = args.name or args.dat.stem.lower()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    dat_world = read_dat_world(args.dat)
    texture_sizes = build_texture_size_index(args.extracted_root)
    bmodels, alias_metadata, stats = transcode_geometry(dat_world, args.scale, texture_sizes)

    source_glb_path = args.output_dir / f"{output_name}.source.glb"
    geometry_metadata_path = args.output_dir / f"{output_name}.geometry.yml"
    scene_path = args.output_dir / f"{output_name}.scene.yml"
    source_metadata_path = args.output_dir / f"{output_name}.mm9.yml"
    bsp_diagnostics_path = args.output_dir / f"{output_name}.bsp.yml"
    aliases_path = args.output_dir / f"{output_name}.material_aliases.yml"
    raw_objects_path = args.output_dir / f"{output_name}.raw_objects.yml"
    blv_path = args.output_dir / f"{output_name}.blv"
    bitmap_dir = args.bitmap_dir or (args.output_dir.parent / "textures")

    layout = build_source_layout(dat_world, bmodels, args.sector_mode, args.sector_grid, alias_metadata, args.scale)
    source_glb_stats = write_source_glb(source_glb_path, layout)
    bitmap_modes = write_alias_bitmaps(bitmap_dir, alias_metadata)
    write_geometry_metadata(geometry_metadata_path, output_name, source_glb_path.name, alias_metadata, layout)
    write_scene_yml(scene_path, output_name)
    write_source_metadata(
        source_metadata_path,
        args.dat,
        output_name,
        bitmap_dir,
        args.scale,
        layout,
        dat_world,
        stats,
        source_glb_stats,
    )
    write_bsp_diagnostics(bsp_diagnostics_path, dat_world, layout)
    write_material_aliases(aliases_path, args.dat, alias_metadata, stats, bitmap_modes)
    write_raw_objects(raw_objects_path, dat_world)

    if args.compile_tool:
        compile_blv(args.compile_tool, source_glb_path, geometry_metadata_path, blv_path)

    print(f"wrote {source_glb_path}")
    print(f"wrote {geometry_metadata_path}")
    print(f"wrote {scene_path}")
    print(f"wrote {source_metadata_path}")
    print(f"wrote {bsp_diagnostics_path}")
    print(f"wrote {aliases_path}")
    print(f"wrote {raw_objects_path}")
    print(f"wrote {len(bitmap_modes)} bitmap aliases under {bitmap_dir}")
    if blv_path.exists():
        print(f"wrote {blv_path} ({blv_path.stat().st_size} bytes)")
    print(json.dumps({**stats, **source_glb_stats, **layout.diagnostics}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
