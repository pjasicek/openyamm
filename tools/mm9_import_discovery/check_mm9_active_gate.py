#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml


YAML_LOADER = getattr(yaml, "CSafeLoader", yaml.SafeLoader)

DEFAULT_SUMMARY_PATH = Path("assets_dev/worlds/mm9/import/validation/active_slice.validation_summary.yml")
EXPECTED_MAP_IDS = {"thjorgard", "thjorgardcity"}


def scalar_int(data: dict[str, Any], key: str) -> int:
    value = data.get(key, 0)
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    raise ValueError(f"{key} is not an integer: {value!r}")


def scalar_bool(data: dict[str, Any], key: str) -> bool:
    value = data.get(key, False)
    if isinstance(value, bool):
        return value
    raise ValueError(f"{key} is not a boolean: {value!r}")


def require(condition: bool, failures: list[str], message: str) -> None:
    if not condition:
        failures.append(message)


def require_zero(data: dict[str, Any], failures: list[str], key: str, prefix: str = "") -> None:
    value = scalar_int(data, key)
    require(value == 0, failures, f"{prefix}{key} expected 0, got {value}")


def require_positive_when(
    data: dict[str, Any],
    failures: list[str],
    source_key: str,
    target_key: str,
    prefix: str = "",
) -> None:
    source_value = scalar_int(data, source_key)
    target_value = scalar_int(data, target_key)
    if source_value != 0:
        require(
            target_value != 0,
            failures,
            f"{prefix}{target_key} expected nonzero because {source_key}={source_value}, got 0",
        )


def check_summary(summary: dict[str, Any]) -> list[str]:
    failures: list[str] = []

    require(summary.get("kind") == "mm9_asset_validation_summary", failures, "kind is not mm9_asset_validation_summary")
    require(summary.get("scope") == "active_two_map_slice", failures, "scope is not active_two_map_slice")
    require(scalar_bool(summary, "clean"), failures, "summary clean is not true")
    require(scalar_int(summary, "report_count") == 2, failures, "report_count expected 2")
    require(scalar_int(summary, "clean_reports") == 2, failures, "clean_reports expected 2")
    require_zero(summary, failures, "dirty_reports")

    zero_keys = [
        "level_load_diagnostics",
        "source_dat_hash_diagnostics",
        "source_manifest_diagnostics",
        "source_manifest_count_drift_families",
        "source_manifest_missing_directories",
        "document_paths_missing",
        "document_paths_missing_required",
        "dat_world_reference_issues",
        "dat_world_invalid_leaf_references",
        "dat_world_invalid_surface_texture_refs",
        "dat_world_invalid_poly_surface_refs",
        "dat_world_invalid_poly_plane_refs",
        "dat_world_invalid_poly_vertex_refs",
        "dat_world_invalid_node_poly_refs",
        "dat_world_invalid_root_node_refs",
        "raw_object_sidecar_issues",
        "asset_graph_unresolved",
        "asset_graph_ambiguous",
        "asset_graph_stale",
        "asset_graph_required_unresolved",
        "asset_graph_required_ambiguous",
        "asset_graph_optional_unresolved",
        "asset_graph_optional_ambiguous",
        "unresolved_required_raw_object_asset_refs",
        "unresolved_optional_raw_object_asset_refs",
        "stale_caches",
        "viewport_native_missing_material_triangles",
        "viewport_native_placeholder_material_triangles",
        "viewport_native_unresolved_material_triangles",
        "ambiguous_dtx",
        "decoded_cache_mismatches",
        "unresolved_sprite_frame_textures",
        "ambiguous_sprite_frame_textures",
        "unresolved_required_sound_references",
        "missing_model_instance_assets",
        "missing_drawable_model_instance_geometry",
        "actor_variant_unresolved",
        "actor_variant_unresolved_foot_sounds",
        "actor_variant_unresolved_source_sound_references",
        "actor_variant_unresolved_source_voice_references",
        "missing_scripted_object_collision_visuals",
        "mechanism_unresolved_required_targets",
        "mechanism_incomplete_linear_motion",
        "mechanism_incomplete_rotation_motion",
        "mechanism_unresolved_trigger_outputs",
        "mechanism_world_model_targets_missing_model",
        "mechanism_world_model_targets_missing_polygon_group",
        "mechanism_world_model_targets_mismatched_polygon_group",
        "script_unresolved_includes",
        "script_ambiguous_includes",
        "diagnostic_errors",
    ]

    for key in zero_keys:
        require_zero(summary, failures, key)

    report_count = scalar_int(summary, "report_count")
    require(
        scalar_int(summary, "source_mutation_snapshot_verified_reports") == report_count,
        failures,
        "source_mutation_snapshot_verified_reports must equal report_count",
    )
    require(
        scalar_int(summary, "source_dat_hash_verified_reports") == report_count,
        failures,
        "source_dat_hash_verified_reports must equal report_count",
    )
    require(
        scalar_int(summary, "source_manifest_expected_files")
        == scalar_int(summary, "source_manifest_actual_files"),
        failures,
        "source_manifest_expected_files must equal source_manifest_actual_files",
    )
    require(
        scalar_int(summary, "source_mutation_snapshot_files") > 0,
        failures,
        "source_mutation_snapshot_files must be positive",
    )
    require(scalar_int(summary, "document_paths_total") > 0, failures, "document_paths_total must be positive")
    require(scalar_int(summary, "raw_objects") > 0, failures, "raw_objects must be positive")
    require(scalar_int(summary, "script_includes") > 0, failures, "script_includes must be positive")
    require(scalar_int(summary, "script_labels") > 0, failures, "script_labels must be positive")
    require(
        scalar_int(summary, "script_include_references") == scalar_int(summary, "script_includes"),
        failures,
        "script_include_references must equal script_includes",
    )
    require(
        scalar_int(summary, "script_resolved_includes") == scalar_int(summary, "script_include_references"),
        failures,
        "script_resolved_includes must equal script_include_references",
    )
    require(scalar_int(summary, "asset_graph_total") > 0, failures, "asset_graph_total must be positive")
    require(
        scalar_int(summary, "asset_graph_resolved")
        + scalar_int(summary, "asset_graph_unresolved")
        + scalar_int(summary, "asset_graph_ambiguous")
        == scalar_int(summary, "asset_graph_total"),
        failures,
        "asset_graph_total must equal asset_graph_resolved + asset_graph_unresolved + asset_graph_ambiguous",
    )
    require(
        scalar_int(summary, "asset_graph_required_total")
        + scalar_int(summary, "asset_graph_optional_total")
        == scalar_int(summary, "asset_graph_total"),
        failures,
        "asset_graph_required_total + asset_graph_optional_total must equal asset_graph_total",
    )
    require(
        scalar_int(summary, "asset_graph_required_resolved")
        + scalar_int(summary, "asset_graph_required_unresolved")
        + scalar_int(summary, "asset_graph_required_ambiguous")
        == scalar_int(summary, "asset_graph_required_total"),
        failures,
        "asset_graph_required_total must equal required resolved + unresolved + ambiguous",
    )
    require(
        scalar_int(summary, "asset_graph_optional_resolved")
        + scalar_int(summary, "asset_graph_optional_unresolved")
        + scalar_int(summary, "asset_graph_optional_ambiguous")
        == scalar_int(summary, "asset_graph_optional_total"),
        failures,
        "asset_graph_optional_total must equal optional resolved + unresolved + ambiguous",
    )
    require(scalar_int(summary, "raw_object_asset_refs") > 0, failures, "raw_object_asset_refs must be positive")
    require(
        scalar_int(summary, "raw_object_asset_refs")
        == scalar_int(summary, "required_raw_object_asset_refs")
        + scalar_int(summary, "optional_raw_object_asset_refs"),
        failures,
        "raw_object_asset_refs must equal required_raw_object_asset_refs + optional_raw_object_asset_refs",
    )
    require(
        scalar_int(summary, "object_source_transforms") == scalar_int(summary, "raw_objects"),
        failures,
        "object_source_transforms must equal raw_objects",
    )
    require(
        scalar_int(summary, "readonly_source_paths") >= report_count * 2,
        failures,
        "readonly_source_paths must be at least two per active report",
    )
    require(scalar_int(summary, "generated_paths") > 0, failures, "generated_paths must be positive")
    require(scalar_int(summary, "authored_paths") > 0, failures, "authored_paths must be positive")
    require(scalar_int(summary, "authored_override_paths") > 0, failures, "authored_override_paths must be positive")
    require(scalar_int(summary, "compatibility_paths") > 0, failures, "compatibility_paths must be positive")

    require(scalar_int(summary, "resolved_dtx") > 0, failures, "resolved_dtx must be positive")
    require(
        scalar_int(summary, "source_dtx_paths") == scalar_int(summary, "resolved_dtx"),
        failures,
        "source_dtx_paths must equal resolved_dtx",
    )
    require(
        scalar_int(summary, "material_textures")
        == scalar_int(summary, "resolved_dtx")
        + scalar_int(summary, "resolved_sprite_materials")
        + scalar_int(summary, "default_helper_materials"),
        failures,
        "material_textures must equal resolved_dtx + resolved_sprite_materials + default_helper_materials",
    )
    require(
        scalar_int(summary, "placeholder_missing_source_materials")
        >= scalar_int(summary, "default_helper_materials"),
        failures,
        "placeholder_missing_source_materials must be at least default_helper_materials",
    )
    require(
        scalar_int(summary, "dtx_headers") == scalar_int(summary, "resolved_dtx"),
        failures,
        "dtx_headers must equal resolved_dtx",
    )
    require(
        scalar_int(summary, "dtx_user_flag_records") == scalar_int(summary, "dtx_headers"),
        failures,
        "dtx_user_flag_records must equal dtx_headers",
    )
    require(
        scalar_int(summary, "dtx_extra_byte_records") >= scalar_int(summary, "dtx_headers"),
        failures,
        "dtx_extra_byte_records must be at least dtx_headers",
    )
    require(
        scalar_int(summary, "dtx_mip_payloads") >= scalar_int(summary, "dtx_headers"),
        failures,
        "dtx_mip_payloads must be at least dtx_headers",
    )
    require(
        scalar_int(summary, "dtx_decoded_preview_mips") == scalar_int(summary, "dtx_mip_payloads"),
        failures,
        "dtx_decoded_preview_mips must equal dtx_mip_payloads",
    )
    require(
        scalar_int(summary, "decoded_cache_source_decoded")
        == scalar_int(summary, "decoded_cache_determinism_checked"),
        failures,
        "decoded_cache_source_decoded must equal decoded_cache_determinism_checked",
    )
    require(
        scalar_int(summary, "decoded_cache_image_decoded")
        == scalar_int(summary, "decoded_cache_determinism_checked"),
        failures,
        "decoded_cache_image_decoded must equal decoded_cache_determinism_checked",
    )
    require(
        scalar_int(summary, "decoded_cache_matches_source")
        == scalar_int(summary, "decoded_cache_determinism_checked"),
        failures,
        "decoded_cache_matches_source must equal decoded_cache_determinism_checked",
    )
    if scalar_int(summary, "sprite_materials") != 0:
        require(
            scalar_int(summary, "resolved_sprite_materials") == scalar_int(summary, "sprite_materials"),
            failures,
            "resolved_sprite_materials must equal sprite_materials",
        )
        require(
            scalar_int(summary, "resolved_sprite_frame_textures")
            == scalar_int(summary, "sprite_frame_textures"),
            failures,
            "resolved_sprite_frame_textures must equal sprite_frame_textures",
        )

    require(
        scalar_int(summary, "mechanism_inert_preview_entries")
        == scalar_int(summary, "mechanism_inert_mechanisms"),
        failures,
        "mechanism_inert_preview_entries must equal mechanism_inert_mechanisms",
    )
    require(
        scalar_int(summary, "mechanism_authored_sound_references")
        + scalar_int(summary, "mechanism_empty_sound_references")
        == scalar_int(summary, "mechanism_sound_slots"),
        failures,
        "mechanism_authored_sound_references + mechanism_empty_sound_references must equal mechanism_sound_slots",
    )
    require(scalar_int(summary, "mechanism_activation_start_open_fields") > 0, failures,
            "mechanism_activation_start_open_fields must be positive")
    require(
        scalar_int(summary, "mechanism_activation_start_open_fields")
        == scalar_int(summary, "mechanism_activation_locked_fields")
        == scalar_int(summary, "mechanism_activation_push_open_fields")
        == scalar_int(summary, "mechanism_activation_touch_to_open_fields")
        == scalar_int(summary, "mechanism_activation_reopen_on_contact_fields"),
        failures,
        "mechanism activation state fields must have matching active counts",
    )
    require(
        scalar_int(summary, "mechanism_timing_move_delay_fields")
        == scalar_int(summary, "mechanism_activation_start_open_fields"),
        failures,
        "mechanism_timing_move_delay_fields must equal mechanism_activation_start_open_fields",
    )
    require(
        scalar_int(summary, "mechanism_timing_open_wait_fields")
        == scalar_int(summary, "mechanism_activation_start_open_fields"),
        failures,
        "mechanism_timing_open_wait_fields must equal mechanism_activation_start_open_fields",
    )
    require(
        scalar_int(summary, "mechanism_rotation_open_away_fields") > 0,
        failures,
        "mechanism_rotation_open_away_fields must be positive",
    )
    require(
        scalar_int(summary, "mechanism_rotation_open_away_fields")
        <= scalar_int(summary, "mechanism_activation_start_open_fields"),
        failures,
        "mechanism_rotation_open_away_fields must not exceed mechanism_activation_start_open_fields",
    )

    preview_candidates = scalar_int(summary, "mechanism_preview_candidates")
    preview_changed_bounds = scalar_int(summary, "mechanism_preview_changed_bounds")
    if preview_candidates != 0:
        require(
            preview_changed_bounds == preview_candidates,
            failures,
            "mechanism_preview_changed_bounds must equal mechanism_preview_candidates when candidates exist",
        )

    require(
        scalar_int(summary, "resolved_sound_references") == scalar_int(summary, "sound_references"),
        failures,
        "resolved_sound_references must equal sound_references",
    )
    if scalar_int(summary, "actor_variant_candidates") != 0:
        require(
            scalar_int(summary, "actor_variant_gameplay_identity_rows")
            == scalar_int(summary, "actor_variant_candidates"),
            failures,
            "actor_variant_gameplay_identity_rows must equal actor_variant_candidates",
        )
    require(
        scalar_int(summary, "actor_variant_resolved_foot_sounds")
        == scalar_int(summary, "actor_variant_foot_sound_fields"),
        failures,
        "actor_variant_resolved_foot_sounds must equal actor_variant_foot_sound_fields",
    )
    require(
        scalar_int(summary, "actor_variant_resolved_source_sound_references")
        == scalar_int(summary, "actor_variant_source_sound_references"),
        failures,
        "actor_variant_resolved_source_sound_references must equal actor_variant_source_sound_references",
    )
    require(
        scalar_int(summary, "actor_variant_resolved_source_voice_references")
        == scalar_int(summary, "actor_variant_source_voice_references"),
        failures,
        "actor_variant_resolved_source_voice_references must equal actor_variant_source_voice_references",
    )

    require_positive_when(summary, failures, "world_model_overlay_vertices", "world_model_overlay_pick_candidates")
    require_positive_when(summary, failures, "native_renderable_triangles", "selected_polygon_overlay_vertices")
    require_positive_when(summary, failures, "native_renderable_triangles", "selected_surface_overlay_vertices")
    require_positive_when(summary, failures, "native_renderable_triangles", "native_filter_visual")
    require_positive_when(summary, failures, "native_renderable_triangles", "native_filter_helper")
    require_positive_when(summary, failures, "native_renderable_triangles", "native_filter_physics")
    require_positive_when(summary, failures, "native_renderable_triangles", "native_filter_visibility")
    require_positive_when(summary, failures, "native_renderable_triangles", "native_filter_rail")
    require_positive_when(summary, failures, "native_filter_water", "native_filter_water_volume")
    require_positive_when(summary, failures, "object_bounds_evidence", "object_overlay_vertices")
    require_positive_when(summary, failures, "object_overlay_vertices", "object_overlay_pick_candidates")
    require_positive_when(summary, failures, "light_objects", "light_overlay_vertices")
    require_positive_when(summary, failures, "sound_objects", "sound_overlay_vertices")
    require_positive_when(summary, failures, "spawn_source_objects", "spawn_overlay_vertices")
    require_positive_when(summary, failures, "model_instances", "model_instances_in_camera_frame")

    require(
        scalar_int(summary, "mechanism_target_marker_candidates")
        == scalar_int(summary, "mechanism_target_gizmo_candidates"),
        failures,
        "mechanism_target_marker_candidates must equal mechanism_target_gizmo_candidates",
    )
    require(
        scalar_int(summary, "mechanism_target_gizmo_candidates")
        == scalar_int(summary, "mechanism_los_checked_candidates"),
        failures,
        "mechanism_target_gizmo_candidates must equal mechanism_los_checked_candidates",
    )
    require(
        scalar_int(summary, "mechanism_motion_path_markers")
        == scalar_int(summary, "mechanism_preview_candidates"),
        failures,
        "mechanism_motion_path_markers must equal mechanism_preview_candidates",
    )
    require(
        scalar_int(summary, "native_filter_visible_water") + scalar_int(summary, "native_filter_water_volume")
        == scalar_int(summary, "native_filter_water"),
        failures,
        "native_filter_visible_water + native_filter_water_volume must equal native_filter_water",
    )
    require(
        scalar_int(summary, "native_filter_helper")
        >= scalar_int(summary, "native_filter_physics")
        + scalar_int(summary, "native_filter_visibility")
        + scalar_int(summary, "native_filter_rail")
        + scalar_int(summary, "native_filter_water_volume"),
        failures,
        "native_filter_helper must cover physics, visibility, rail, and water-volume helpers",
    )
    require(scalar_int(summary, "native_filter_portals") > 0, failures, "native_filter_portals must be positive")

    reports = summary.get("reports", [])
    require(isinstance(reports, list), failures, "reports is not a list")
    if isinstance(reports, list):
        map_ids = {report.get("map_id") for report in reports if isinstance(report, dict)}
        require(map_ids == EXPECTED_MAP_IDS, failures, f"reports map ids expected {EXPECTED_MAP_IDS}, got {map_ids}")

        for report in reports:
            if not isinstance(report, dict):
                failures.append(f"report is not a mapping: {report!r}")
                continue

            prefix = f"reports[{report.get('map_id', '<unknown>')}]."
            require(scalar_bool(report, "clean"), failures, f"{prefix}clean is not true")
            require(
                scalar_bool(report, "source_mutation_snapshot_verified"),
                failures,
                f"{prefix}source_mutation_snapshot_verified is not true",
            )
            require(
                scalar_bool(report, "source_dat_hash_verified"),
                failures,
                f"{prefix}source_dat_hash_verified is not true",
            )
            for key in zero_keys:
                if key in report:
                    require_zero(report, failures, key, prefix)
            if "source_manifest_expected_files" in report or "source_manifest_actual_files" in report:
                require(
                    scalar_int(report, "source_manifest_expected_files")
                    == scalar_int(report, "source_manifest_actual_files"),
                    failures,
                    f"{prefix}source_manifest_expected_files must equal source_manifest_actual_files",
                )
            if "source_mutation_snapshot_files" in report:
                require(
                    scalar_int(report, "source_mutation_snapshot_files") > 0,
                    failures,
                    f"{prefix}source_mutation_snapshot_files must be positive",
                )
            if "document_paths_total" in report:
                require(
                    scalar_int(report, "document_paths_total") > 0,
                    failures,
                    f"{prefix}document_paths_total must be positive",
                )
            if "raw_objects" in report:
                require(
                    scalar_int(report, "raw_objects") > 0,
                    failures,
                    f"{prefix}raw_objects must be positive",
                )
                require(
                    scalar_int(report, "object_source_transforms") == scalar_int(report, "raw_objects"),
                    failures,
                    f"{prefix}object_source_transforms must equal raw_objects",
                )
            if "script_includes" in report:
                require(
                    scalar_int(report, "script_includes") > 0,
                    failures,
                    f"{prefix}script_includes must be positive",
                )
            if "script_labels" in report:
                require(
                    scalar_int(report, "script_labels") > 0,
                    failures,
                    f"{prefix}script_labels must be positive",
                )
            if "script_include_references" in report:
                require(
                    scalar_int(report, "script_include_references") == scalar_int(report, "script_includes"),
                    failures,
                    f"{prefix}script_include_references must equal script_includes",
                )
            if "script_resolved_includes" in report:
                require(
                    scalar_int(report, "script_resolved_includes")
                    == scalar_int(report, "script_include_references"),
                    failures,
                    f"{prefix}script_resolved_includes must equal script_include_references",
                )
            if "asset_graph_total" in report:
                require(
                    scalar_int(report, "asset_graph_total") > 0,
                    failures,
                    f"{prefix}asset_graph_total must be positive",
                )
                require(
                    scalar_int(report, "asset_graph_resolved")
                    + scalar_int(report, "asset_graph_unresolved")
                    + scalar_int(report, "asset_graph_ambiguous")
                    == scalar_int(report, "asset_graph_total"),
                    failures,
                    f"{prefix}asset_graph_total must equal asset_graph_resolved"
                    " + asset_graph_unresolved + asset_graph_ambiguous",
                )
                require(
                    scalar_int(report, "asset_graph_required_total")
                    + scalar_int(report, "asset_graph_optional_total")
                    == scalar_int(report, "asset_graph_total"),
                    failures,
                    f"{prefix}asset_graph_required_total + asset_graph_optional_total"
                    " must equal asset_graph_total",
                )
                require(
                    scalar_int(report, "asset_graph_required_resolved")
                    + scalar_int(report, "asset_graph_required_unresolved")
                    + scalar_int(report, "asset_graph_required_ambiguous")
                    == scalar_int(report, "asset_graph_required_total"),
                    failures,
                    f"{prefix}asset_graph_required_total must equal required resolved"
                    " + unresolved + ambiguous",
                )
                require(
                    scalar_int(report, "asset_graph_optional_resolved")
                    + scalar_int(report, "asset_graph_optional_unresolved")
                    + scalar_int(report, "asset_graph_optional_ambiguous")
                    == scalar_int(report, "asset_graph_optional_total"),
                    failures,
                    f"{prefix}asset_graph_optional_total must equal optional resolved"
                    " + unresolved + ambiguous",
                )
            if "raw_object_asset_refs" in report:
                require(
                    scalar_int(report, "raw_object_asset_refs") > 0,
                    failures,
                    f"{prefix}raw_object_asset_refs must be positive",
                )
                require(
                    scalar_int(report, "raw_object_asset_refs")
                    == scalar_int(report, "required_raw_object_asset_refs")
                    + scalar_int(report, "optional_raw_object_asset_refs"),
                    failures,
                    f"{prefix}raw_object_asset_refs must equal required_raw_object_asset_refs"
                    " + optional_raw_object_asset_refs",
                )
            if "readonly_source_paths" in report:
                require(
                    scalar_int(report, "readonly_source_paths") >= 2,
                    failures,
                    f"{prefix}readonly_source_paths must be at least two",
                )
            for key in ["generated_paths", "authored_paths", "authored_override_paths", "compatibility_paths"]:
                if key in report:
                    require(scalar_int(report, key) > 0, failures, f"{prefix}{key} must be positive")
            if "resolved_dtx" in report:
                require(scalar_int(report, "resolved_dtx") > 0, failures, f"{prefix}resolved_dtx must be positive")
            if "source_dtx_paths" in report or "resolved_dtx" in report:
                require(
                    scalar_int(report, "source_dtx_paths") == scalar_int(report, "resolved_dtx"),
                    failures,
                    f"{prefix}source_dtx_paths must equal resolved_dtx",
                )
            if "material_textures" in report:
                require(
                    scalar_int(report, "material_textures")
                    == scalar_int(report, "resolved_dtx")
                    + scalar_int(report, "resolved_sprite_materials")
                    + scalar_int(report, "default_helper_materials"),
                    failures,
                    f"{prefix}material_textures must equal resolved_dtx + resolved_sprite_materials"
                    " + default_helper_materials",
                )
            if "placeholder_missing_source_materials" in report:
                require(
                    scalar_int(report, "placeholder_missing_source_materials")
                    >= scalar_int(report, "default_helper_materials"),
                    failures,
                    f"{prefix}placeholder_missing_source_materials must be at least default_helper_materials",
                )
            if "dtx_headers" in report or "resolved_dtx" in report:
                require(
                    scalar_int(report, "dtx_headers") == scalar_int(report, "resolved_dtx"),
                    failures,
                    f"{prefix}dtx_headers must equal resolved_dtx",
                )
            if "dtx_user_flag_records" in report or "dtx_headers" in report:
                require(
                    scalar_int(report, "dtx_user_flag_records") == scalar_int(report, "dtx_headers"),
                    failures,
                    f"{prefix}dtx_user_flag_records must equal dtx_headers",
                )
            if "dtx_extra_byte_records" in report or "dtx_headers" in report:
                require(
                    scalar_int(report, "dtx_extra_byte_records") >= scalar_int(report, "dtx_headers"),
                    failures,
                    f"{prefix}dtx_extra_byte_records must be at least dtx_headers",
                )
            if "dtx_mip_payloads" in report or "dtx_headers" in report:
                require(
                    scalar_int(report, "dtx_mip_payloads") >= scalar_int(report, "dtx_headers"),
                    failures,
                    f"{prefix}dtx_mip_payloads must be at least dtx_headers",
                )
            if "dtx_decoded_preview_mips" in report or "dtx_mip_payloads" in report:
                require(
                    scalar_int(report, "dtx_decoded_preview_mips") == scalar_int(report, "dtx_mip_payloads"),
                    failures,
                    f"{prefix}dtx_decoded_preview_mips must equal dtx_mip_payloads",
                )
            if "decoded_cache_source_decoded" in report or "decoded_cache_determinism_checked" in report:
                require(
                    scalar_int(report, "decoded_cache_source_decoded")
                    == scalar_int(report, "decoded_cache_determinism_checked"),
                    failures,
                    f"{prefix}decoded_cache_source_decoded must equal decoded_cache_determinism_checked",
                )
                require(
                    scalar_int(report, "decoded_cache_image_decoded")
                    == scalar_int(report, "decoded_cache_determinism_checked"),
                    failures,
                    f"{prefix}decoded_cache_image_decoded must equal decoded_cache_determinism_checked",
                )
                require(
                    scalar_int(report, "decoded_cache_matches_source")
                    == scalar_int(report, "decoded_cache_determinism_checked"),
                    failures,
                    f"{prefix}decoded_cache_matches_source must equal decoded_cache_determinism_checked",
                )
            if "sprite_materials" in report and scalar_int(report, "sprite_materials") != 0:
                require(
                    scalar_int(report, "resolved_sprite_materials") == scalar_int(report, "sprite_materials"),
                    failures,
                    f"{prefix}resolved_sprite_materials must equal sprite_materials",
                )
                require(
                    scalar_int(report, "resolved_sprite_frame_textures")
                    == scalar_int(report, "sprite_frame_textures"),
                    failures,
                    f"{prefix}resolved_sprite_frame_textures must equal sprite_frame_textures",
                )
            require(
                scalar_int(report, "mechanism_inert_preview_entries")
                == scalar_int(report, "mechanism_inert_mechanisms"),
                failures,
                f"{prefix}mechanism_inert_preview_entries must equal mechanism_inert_mechanisms",
            )
            if "mechanism_sound_slots" in report:
                require(
                    scalar_int(report, "mechanism_authored_sound_references")
                    + scalar_int(report, "mechanism_empty_sound_references")
                    == scalar_int(report, "mechanism_sound_slots"),
                    failures,
                    f"{prefix}mechanism_authored_sound_references + mechanism_empty_sound_references"
                    " must equal mechanism_sound_slots",
                )
            if "mechanism_activation_start_open_fields" in report:
                require(
                    scalar_int(report, "mechanism_activation_start_open_fields") > 0,
                    failures,
                    f"{prefix}mechanism_activation_start_open_fields must be positive",
                )
                require(
                    scalar_int(report, "mechanism_activation_start_open_fields")
                    == scalar_int(report, "mechanism_activation_locked_fields")
                    == scalar_int(report, "mechanism_activation_push_open_fields")
                    == scalar_int(report, "mechanism_activation_touch_to_open_fields")
                    == scalar_int(report, "mechanism_activation_reopen_on_contact_fields"),
                    failures,
                    f"{prefix}mechanism activation state fields must have matching active counts",
                )
                require(
                    scalar_int(report, "mechanism_timing_move_delay_fields")
                    == scalar_int(report, "mechanism_activation_start_open_fields"),
                    failures,
                    f"{prefix}mechanism_timing_move_delay_fields must equal"
                    " mechanism_activation_start_open_fields",
                )
                require(
                    scalar_int(report, "mechanism_timing_open_wait_fields")
                    == scalar_int(report, "mechanism_activation_start_open_fields"),
                    failures,
                    f"{prefix}mechanism_timing_open_wait_fields must equal"
                    " mechanism_activation_start_open_fields",
                )
                require(
                    scalar_int(report, "mechanism_rotation_open_away_fields") > 0,
                    failures,
                    f"{prefix}mechanism_rotation_open_away_fields must be positive",
                )
                require(
                    scalar_int(report, "mechanism_rotation_open_away_fields")
                    <= scalar_int(report, "mechanism_activation_start_open_fields"),
                    failures,
                    f"{prefix}mechanism_rotation_open_away_fields must not exceed"
                    " mechanism_activation_start_open_fields",
                )
            if "resolved_sound_references" in report or "sound_references" in report:
                require(
                    scalar_int(report, "resolved_sound_references") == scalar_int(report, "sound_references"),
                    failures,
                    f"{prefix}resolved_sound_references must equal sound_references",
                )
            if "native_filter_water" in report:
                require(
                    scalar_int(report, "native_filter_visible_water")
                    + scalar_int(report, "native_filter_water_volume")
                    == scalar_int(report, "native_filter_water"),
                    failures,
                    f"{prefix}native_filter_visible_water + native_filter_water_volume"
                    " must equal native_filter_water",
                )
                require(
                    scalar_int(report, "native_filter_helper")
                    >= scalar_int(report, "native_filter_physics")
                    + scalar_int(report, "native_filter_visibility")
                    + scalar_int(report, "native_filter_rail")
                    + scalar_int(report, "native_filter_water_volume"),
                    failures,
                    f"{prefix}native_filter_helper must cover physics, visibility, rail,"
                    " and water-volume helpers",
                )
            if "actor_variant_candidates" in report and scalar_int(report, "actor_variant_candidates") != 0:
                require(
                    scalar_int(report, "actor_variant_gameplay_identity_rows")
                    == scalar_int(report, "actor_variant_candidates"),
                    failures,
                    f"{prefix}actor_variant_gameplay_identity_rows must equal actor_variant_candidates",
                )
            if "actor_variant_foot_sound_fields" in report:
                require(
                    scalar_int(report, "actor_variant_resolved_foot_sounds")
                    == scalar_int(report, "actor_variant_foot_sound_fields"),
                    failures,
                    f"{prefix}actor_variant_resolved_foot_sounds must equal actor_variant_foot_sound_fields",
                )
            if "actor_variant_source_sound_references" in report:
                require(
                    scalar_int(report, "actor_variant_resolved_source_sound_references")
                    == scalar_int(report, "actor_variant_source_sound_references"),
                    failures,
                    f"{prefix}actor_variant_resolved_source_sound_references"
                    " must equal actor_variant_source_sound_references",
                )
            if "actor_variant_source_voice_references" in report:
                require(
                    scalar_int(report, "actor_variant_resolved_source_voice_references")
                    == scalar_int(report, "actor_variant_source_voice_references"),
                    failures,
                    f"{prefix}actor_variant_resolved_source_voice_references"
                    " must equal actor_variant_source_voice_references",
                )

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the focused MM9 active two-map editor gate summary.")
    parser.add_argument(
        "--summary",
        type=Path,
        default=DEFAULT_SUMMARY_PATH,
        help=f"Path to active_slice.validation_summary.yml, default: {DEFAULT_SUMMARY_PATH}",
    )
    args = parser.parse_args()

    if not args.summary.exists():
        print(f"MM9 active gate failed: summary does not exist: {args.summary}", file=sys.stderr)
        return 1

    with args.summary.open("r", encoding="utf-8") as stream:
        summary = yaml.load(stream, Loader=YAML_LOADER)

    if not isinstance(summary, dict):
        print(f"MM9 active gate failed: summary is not a mapping: {args.summary}", file=sys.stderr)
        return 1

    failures = check_summary(summary)
    if failures:
        print(f"MM9 active gate failed: {args.summary}", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1

    print(
        "MM9 active gate passed:"
        f" reports={scalar_int(summary, 'report_count')}"
        f" native_triangles={scalar_int(summary, 'native_renderable_triangles')}"
        f" model_instances={scalar_int(summary, 'model_instances')}"
        f" mechanism_preview_candidates={scalar_int(summary, 'mechanism_preview_candidates')}"
        f" mechanism_inert_preview_entries={scalar_int(summary, 'mechanism_inert_preview_entries')}"
        f" warnings={scalar_int(summary, 'diagnostic_warnings')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
