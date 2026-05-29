#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = REPO_ROOT / "tools/mm9_import_discovery/check_mm9_active_gate.py"

spec = importlib.util.spec_from_file_location("check_mm9_active_gate", CHECKER_PATH)
assert spec is not None
check_mm9_active_gate = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = check_mm9_active_gate
spec.loader.exec_module(check_mm9_active_gate)


ZERO_KEYS = [
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


def active_report(map_id: str, inert_count: int) -> dict[str, Any]:
    report: dict[str, Any] = {
        "map_id": map_id,
        "clean": True,
        "source_mutation_snapshot_verified": True,
        "source_mutation_snapshot_files": 10,
        "source_dat_hash_verified": True,
        "source_manifest_expected_files": 20,
        "source_manifest_actual_files": 20,
        "document_paths_total": 8,
        "raw_objects": 10,
        "script_includes": 2,
        "script_labels": 4,
        "script_include_references": 2,
        "script_resolved_includes": 2,
        "asset_graph_total": 12,
        "asset_graph_resolved": 12,
        "asset_graph_required_total": 9,
        "asset_graph_required_resolved": 9,
        "asset_graph_optional_total": 3,
        "asset_graph_optional_resolved": 3,
        "raw_object_asset_refs": 9,
        "required_raw_object_asset_refs": 7,
        "optional_raw_object_asset_refs": 2,
        "object_source_transforms": 10,
        "readonly_source_paths": 2,
        "generated_paths": 3,
        "authored_paths": 2,
        "authored_override_paths": 1,
        "compatibility_paths": 1,
        "material_textures": 4,
        "resolved_dtx": 2,
        "source_dtx_paths": 2,
        "default_helper_materials": 1,
        "placeholder_missing_source_materials": 1,
        "dtx_headers": 2,
        "dtx_headers_matching_sidecar": 2,
        "dtx_user_flag_records": 2,
        "dtx_extra_byte_records": 24,
        "dtx_mip_payloads": 8,
        "dtx_decoded_preview_mips": 8,
        "dtx_command_strings": 1,
        "decoded_cache_determinism_checked": 2,
        "decoded_cache_source_decoded": 2,
        "decoded_cache_image_decoded": 2,
        "decoded_cache_matches_source": 2,
        "sprite_materials": 1,
        "resolved_sprite_materials": 1,
        "sprite_frame_textures": 3,
        "resolved_sprite_frame_textures": 3,
        "actor_variant_candidates": 2,
        "actor_variant_gameplay_identity_rows": 2,
        "actor_variant_foot_sound_fields": 2,
        "actor_variant_resolved_foot_sounds": 2,
        "actor_variant_source_sound_references": 1,
        "actor_variant_resolved_source_sound_references": 1,
        "actor_variant_source_voice_references": 1,
        "actor_variant_resolved_source_voice_references": 1,
        "native_filter_visual": 5,
        "native_filter_invisible": 1,
        "native_filter_water": 3,
        "native_filter_visible_water": 1,
        "native_filter_water_volume": 2,
        "native_filter_rail": 2,
        "native_filter_helper": 10,
        "native_filter_physics": 3,
        "native_filter_visibility": 2,
        "native_filter_portals": 0,
        "mechanism_sound_slots": 5,
        "mechanism_authored_sound_references": 2,
        "mechanism_empty_sound_references": 3,
        "mechanism_inert_mechanisms": inert_count,
        "mechanism_inert_preview_entries": inert_count,
        "mechanism_activation_start_open_fields": 2,
        "mechanism_activation_locked_fields": 2,
        "mechanism_activation_push_open_fields": 2,
        "mechanism_activation_touch_to_open_fields": 2,
        "mechanism_activation_lock_on_close_fields": 0,
        "mechanism_activation_reopen_on_contact_fields": 2,
        "mechanism_rotation_open_away_fields": 1,
        "mechanism_timing_move_delay_fields": 2,
        "mechanism_timing_open_wait_fields": 2,
    }

    for key in ZERO_KEYS:
        report[key] = 0

    return report


def active_summary() -> dict[str, Any]:
    summary: dict[str, Any] = {
        "kind": "mm9_asset_validation_summary",
        "scope": "active_two_map_slice",
        "clean": True,
        "report_count": 2,
        "clean_reports": 2,
        "dirty_reports": 0,
        "source_mutation_snapshot_verified_reports": 2,
        "source_mutation_snapshot_files": 20,
        "source_dat_hash_verified_reports": 2,
        "source_manifest_expected_files": 40,
        "source_manifest_actual_files": 40,
        "document_paths_total": 16,
        "raw_objects": 20,
        "script_includes": 4,
        "script_labels": 8,
        "script_include_references": 4,
        "script_resolved_includes": 4,
        "asset_graph_total": 24,
        "asset_graph_resolved": 24,
        "asset_graph_required_total": 18,
        "asset_graph_required_resolved": 18,
        "asset_graph_optional_total": 6,
        "asset_graph_optional_resolved": 6,
        "raw_object_asset_refs": 18,
        "required_raw_object_asset_refs": 14,
        "optional_raw_object_asset_refs": 4,
        "object_source_transforms": 20,
        "readonly_source_paths": 4,
        "generated_paths": 6,
        "authored_paths": 4,
        "authored_override_paths": 2,
        "compatibility_paths": 2,
        "material_textures": 8,
        "resolved_dtx": 4,
        "source_dtx_paths": 4,
        "default_helper_materials": 2,
        "placeholder_missing_source_materials": 2,
        "dtx_headers": 4,
        "dtx_headers_matching_sidecar": 4,
        "dtx_user_flag_records": 4,
        "dtx_extra_byte_records": 48,
        "dtx_mip_payloads": 16,
        "dtx_decoded_preview_mips": 16,
        "dtx_command_strings": 2,
        "decoded_cache_determinism_checked": 4,
        "decoded_cache_source_decoded": 4,
        "decoded_cache_image_decoded": 4,
        "decoded_cache_matches_source": 4,
        "sprite_materials": 2,
        "resolved_sprite_materials": 2,
        "sprite_frame_textures": 6,
        "resolved_sprite_frame_textures": 6,
        "native_renderable_triangles": 100,
        "world_model_overlay_vertices": 10,
        "world_model_overlay_pick_candidates": 2,
        "selected_polygon_overlay_vertices": 3,
        "selected_surface_overlay_vertices": 3,
        "native_filter_visual": 10,
        "native_filter_invisible": 2,
        "native_filter_water": 6,
        "native_filter_visible_water": 2,
        "native_filter_water_volume": 4,
        "native_filter_rail": 4,
        "native_filter_helper": 20,
        "native_filter_physics": 6,
        "native_filter_visibility": 4,
        "native_filter_portals": 1,
        "object_bounds_evidence": 4,
        "object_overlay_vertices": 5,
        "object_overlay_pick_candidates": 1,
        "light_objects": 1,
        "light_overlay_vertices": 6,
        "sound_objects": 1,
        "sound_overlay_vertices": 6,
        "sound_references": 2,
        "resolved_sound_references": 2,
        "actor_variant_candidates": 4,
        "actor_variant_gameplay_identity_rows": 4,
        "actor_variant_foot_sound_fields": 4,
        "actor_variant_resolved_foot_sounds": 4,
        "actor_variant_source_sound_references": 2,
        "actor_variant_resolved_source_sound_references": 2,
        "actor_variant_source_voice_references": 2,
        "actor_variant_resolved_source_voice_references": 2,
        "spawn_source_objects": 1,
        "spawn_overlay_vertices": 6,
        "model_instances": 2,
        "model_instances_in_camera_frame": 2,
        "mechanism_target_marker_candidates": 8,
        "mechanism_target_gizmo_candidates": 8,
        "mechanism_los_checked_candidates": 8,
        "mechanism_motion_path_markers": 3,
        "mechanism_preview_candidates": 3,
        "mechanism_preview_changed_bounds": 3,
        "mechanism_sound_slots": 10,
        "mechanism_authored_sound_references": 4,
        "mechanism_empty_sound_references": 6,
        "mechanism_inert_mechanisms": 5,
        "mechanism_inert_preview_entries": 5,
        "mechanism_activation_start_open_fields": 4,
        "mechanism_activation_locked_fields": 4,
        "mechanism_activation_push_open_fields": 4,
        "mechanism_activation_touch_to_open_fields": 4,
        "mechanism_activation_lock_on_close_fields": 0,
        "mechanism_activation_reopen_on_contact_fields": 4,
        "mechanism_rotation_open_away_fields": 2,
        "mechanism_timing_move_delay_fields": 4,
        "mechanism_timing_open_wait_fields": 4,
        "diagnostic_warnings": 1,
        "reports": [
            active_report("thjorgard", 2),
            active_report("thjorgardcity", 3),
        ],
    }

    for key in ZERO_KEYS:
        summary[key] = 0

    return summary


class Mm9ActiveGateTests(unittest.TestCase):
    def test_accepts_valid_active_two_map_summary(self) -> None:
        self.assertEqual(check_mm9_active_gate.check_summary(active_summary()), [])

    def test_rejects_missing_active_map(self) -> None:
        summary = active_summary()
        summary["reports"][1]["map_id"] = "drangheim"

        failures = check_mm9_active_gate.check_summary(summary)

        self.assertTrue(any("reports map ids expected" in failure for failure in failures))

    def test_rejects_dirty_required_counter(self) -> None:
        summary = active_summary()
        summary["asset_graph_required_unresolved"] = 1

        failures = check_mm9_active_gate.check_summary(summary)

        self.assertIn("asset_graph_required_unresolved expected 0, got 1", failures)

    def test_rejects_missing_inert_preview_details(self) -> None:
        summary = active_summary()
        summary["mechanism_inert_preview_entries"] = 4

        failures = check_mm9_active_gate.check_summary(summary)

        self.assertIn("mechanism_inert_preview_entries must equal mechanism_inert_mechanisms", failures)

    def test_rejects_unproven_preview_bounds_change(self) -> None:
        summary = active_summary()
        summary["mechanism_preview_changed_bounds"] = 2

        failures = check_mm9_active_gate.check_summary(summary)

        self.assertIn(
            "mechanism_preview_changed_bounds must equal mechanism_preview_candidates when candidates exist",
            failures,
        )

    def test_rejects_incomplete_mechanism_motion(self) -> None:
        summary = active_summary()
        summary["mechanism_incomplete_linear_motion"] = 1

        failures = check_mm9_active_gate.check_summary(summary)

        self.assertIn("mechanism_incomplete_linear_motion expected 0, got 1", failures)

    def test_rejects_unresolved_mechanism_trigger_output(self) -> None:
        summary = active_summary()
        summary["mechanism_unresolved_trigger_outputs"] = 1

        failures = check_mm9_active_gate.check_summary(summary)

        self.assertIn("mechanism_unresolved_trigger_outputs expected 0, got 1", failures)

    def test_rejects_mechanism_sound_slot_partition_drift(self) -> None:
        summary = active_summary()
        summary["mechanism_empty_sound_references"] = 5

        failures = check_mm9_active_gate.check_summary(summary)

        self.assertIn(
            "mechanism_authored_sound_references + mechanism_empty_sound_references must equal mechanism_sound_slots",
            failures,
        )

    def test_rejects_missing_mechanism_activation_state_evidence(self) -> None:
        summary = active_summary()
        summary["mechanism_activation_push_open_fields"] = 3

        failures = check_mm9_active_gate.check_summary(summary)

        self.assertIn("mechanism activation state fields must have matching active counts", failures)

    def test_rejects_missing_mechanism_timing_evidence(self) -> None:
        summary = active_summary()
        summary["mechanism_timing_open_wait_fields"] = 3

        failures = check_mm9_active_gate.check_summary(summary)

        self.assertIn(
            "mechanism_timing_open_wait_fields must equal mechanism_activation_start_open_fields",
            failures,
        )

    def test_rejects_missing_mechanism_rotation_open_away_evidence(self) -> None:
        summary = active_summary()
        summary["mechanism_rotation_open_away_fields"] = 0

        failures = check_mm9_active_gate.check_summary(summary)

        self.assertIn("mechanism_rotation_open_away_fields must be positive", failures)

    def test_rejects_missing_native_filter_evidence(self) -> None:
        summary = active_summary()
        summary["native_filter_rail"] = 0

        failures = check_mm9_active_gate.check_summary(summary)

        self.assertIn(
            "native_filter_rail expected nonzero because native_renderable_triangles=100, got 0",
            failures,
        )

    def test_rejects_native_water_filter_partition_drift(self) -> None:
        summary = active_summary()
        summary["native_filter_water_volume"] = 3

        failures = check_mm9_active_gate.check_summary(summary)

        self.assertIn(
            "native_filter_visible_water + native_filter_water_volume must equal native_filter_water",
            failures,
        )

    def test_rejects_native_helper_filter_missing_helper_roles(self) -> None:
        summary = active_summary()
        summary["native_filter_helper"] = 10

        failures = check_mm9_active_gate.check_summary(summary)

        self.assertIn(
            "native_filter_helper must cover physics, visibility, rail, and water-volume helpers",
            failures,
        )

    def test_rejects_missing_overlay_pick_evidence(self) -> None:
        summary = active_summary()
        summary["world_model_overlay_pick_candidates"] = 0

        failures = check_mm9_active_gate.check_summary(summary)

        self.assertIn(
            "world_model_overlay_pick_candidates expected nonzero because world_model_overlay_vertices=10, got 0",
            failures,
        )

    def test_rejects_unresolved_required_sound_reference(self) -> None:
        summary = active_summary()
        summary["unresolved_required_sound_references"] = 1

        failures = check_mm9_active_gate.check_summary(summary)

        self.assertIn("unresolved_required_sound_references expected 0, got 1", failures)

    def test_rejects_unresolved_sound_reference_count(self) -> None:
        summary = active_summary()
        summary["resolved_sound_references"] = 1

        failures = check_mm9_active_gate.check_summary(summary)

        self.assertIn("resolved_sound_references must equal sound_references", failures)

    def test_rejects_missing_actor_variant_gameplay_identity(self) -> None:
        summary = active_summary()
        summary["actor_variant_gameplay_identity_rows"] = 3

        failures = check_mm9_active_gate.check_summary(summary)

        self.assertIn("actor_variant_gameplay_identity_rows must equal actor_variant_candidates", failures)

    def test_rejects_unresolved_actor_variant_foot_sound(self) -> None:
        summary = active_summary()
        summary["actor_variant_resolved_foot_sounds"] = 3

        failures = check_mm9_active_gate.check_summary(summary)

        self.assertIn("actor_variant_resolved_foot_sounds must equal actor_variant_foot_sound_fields", failures)

    def test_rejects_unresolved_actor_variant_source_sound_reference(self) -> None:
        summary = active_summary()
        summary["actor_variant_resolved_source_sound_references"] = 1

        failures = check_mm9_active_gate.check_summary(summary)

        self.assertIn(
            "actor_variant_resolved_source_sound_references must equal actor_variant_source_sound_references",
            failures,
        )

    def test_rejects_unresolved_actor_variant_source_voice_reference(self) -> None:
        summary = active_summary()
        summary["actor_variant_resolved_source_voice_references"] = 1

        failures = check_mm9_active_gate.check_summary(summary)

        self.assertIn(
            "actor_variant_resolved_source_voice_references must equal actor_variant_source_voice_references",
            failures,
        )

    def test_rejects_unverified_source_snapshot(self) -> None:
        summary = active_summary()
        summary["source_mutation_snapshot_verified_reports"] = 1

        failures = check_mm9_active_gate.check_summary(summary)

        self.assertIn("source_mutation_snapshot_verified_reports must equal report_count", failures)

    def test_rejects_source_manifest_count_drift(self) -> None:
        summary = active_summary()
        summary["source_manifest_actual_files"] = 39

        failures = check_mm9_active_gate.check_summary(summary)

        self.assertIn("source_manifest_expected_files must equal source_manifest_actual_files", failures)

    def test_rejects_missing_required_document_path(self) -> None:
        summary = active_summary()
        summary["document_paths_missing_required"] = 1

        failures = check_mm9_active_gate.check_summary(summary)

        self.assertIn("document_paths_missing_required expected 0, got 1", failures)

    def test_rejects_invalid_dat_world_source_index_reference(self) -> None:
        summary = active_summary()
        summary["dat_world_invalid_poly_vertex_refs"] = 1

        failures = check_mm9_active_gate.check_summary(summary)

        self.assertIn("dat_world_invalid_poly_vertex_refs expected 0, got 1", failures)

    def test_rejects_raw_object_sidecar_issue(self) -> None:
        summary = active_summary()
        summary["raw_object_sidecar_issues"] = 1

        failures = check_mm9_active_gate.check_summary(summary)

        self.assertIn("raw_object_sidecar_issues expected 0, got 1", failures)

    def test_rejects_unresolved_optional_raw_object_asset_reference(self) -> None:
        summary = active_summary()
        summary["unresolved_optional_raw_object_asset_refs"] = 1

        failures = check_mm9_active_gate.check_summary(summary)

        self.assertIn("unresolved_optional_raw_object_asset_refs expected 0, got 1", failures)

    def test_rejects_unresolved_optional_asset_graph_reference(self) -> None:
        summary = active_summary()
        summary["asset_graph_optional_unresolved"] = 1

        failures = check_mm9_active_gate.check_summary(summary)

        self.assertIn("asset_graph_optional_unresolved expected 0, got 1", failures)

    def test_rejects_asset_graph_total_partition_drift(self) -> None:
        summary = active_summary()
        summary["asset_graph_resolved"] = 23

        failures = check_mm9_active_gate.check_summary(summary)

        self.assertIn(
            "asset_graph_total must equal asset_graph_resolved + asset_graph_unresolved + asset_graph_ambiguous",
            failures,
        )

    def test_rejects_asset_graph_required_optional_partition_drift(self) -> None:
        summary = active_summary()
        summary["asset_graph_optional_total"] = 5

        failures = check_mm9_active_gate.check_summary(summary)

        self.assertIn(
            "asset_graph_required_total + asset_graph_optional_total must equal asset_graph_total",
            failures,
        )

    def test_rejects_raw_object_asset_reference_partition_drift(self) -> None:
        summary = active_summary()
        summary["required_raw_object_asset_refs"] = 13

        failures = check_mm9_active_gate.check_summary(summary)

        self.assertIn(
            "raw_object_asset_refs must equal required_raw_object_asset_refs + optional_raw_object_asset_refs",
            failures,
        )

    def test_rejects_missing_object_source_transform(self) -> None:
        summary = active_summary()
        summary["object_source_transforms"] = 19

        failures = check_mm9_active_gate.check_summary(summary)

        self.assertIn("object_source_transforms must equal raw_objects", failures)

    def test_rejects_missing_script_include_evidence(self) -> None:
        summary = active_summary()
        summary["script_includes"] = 0

        failures = check_mm9_active_gate.check_summary(summary)

        self.assertIn("script_includes must be positive", failures)

    def test_rejects_missing_script_label_evidence(self) -> None:
        summary = active_summary()
        summary["script_labels"] = 0

        failures = check_mm9_active_gate.check_summary(summary)

        self.assertIn("script_labels must be positive", failures)

    def test_rejects_unresolved_script_include(self) -> None:
        summary = active_summary()
        summary["script_resolved_includes"] = 3

        failures = check_mm9_active_gate.check_summary(summary)

        self.assertIn("script_resolved_includes must equal script_include_references", failures)

    def test_rejects_script_include_reference_partition_drift(self) -> None:
        summary = active_summary()
        summary["script_include_references"] = 3

        failures = check_mm9_active_gate.check_summary(summary)

        self.assertIn("script_include_references must equal script_includes", failures)

    def test_rejects_missing_dtx_header(self) -> None:
        summary = active_summary()
        summary["dtx_headers"] = 3

        failures = check_mm9_active_gate.check_summary(summary)

        self.assertIn("dtx_headers must equal resolved_dtx", failures)

    def test_rejects_unclassified_material_row(self) -> None:
        summary = active_summary()
        summary["default_helper_materials"] = 1

        failures = check_mm9_active_gate.check_summary(summary)

        self.assertIn(
            "material_textures must equal resolved_dtx + resolved_sprite_materials + default_helper_materials",
            failures,
        )

    def test_rejects_placeholder_material_without_helper_classification(self) -> None:
        summary = active_summary()
        summary["placeholder_missing_source_materials"] = 1
        summary["default_helper_materials"] = 2

        failures = check_mm9_active_gate.check_summary(summary)

        self.assertIn("placeholder_missing_source_materials must be at least default_helper_materials", failures)

    def test_rejects_missing_dtx_mip_preview(self) -> None:
        summary = active_summary()
        summary["dtx_decoded_preview_mips"] = 15

        failures = check_mm9_active_gate.check_summary(summary)

        self.assertIn("dtx_decoded_preview_mips must equal dtx_mip_payloads", failures)

    def test_rejects_decoded_cache_mismatch(self) -> None:
        summary = active_summary()
        summary["decoded_cache_matches_source"] = 3

        failures = check_mm9_active_gate.check_summary(summary)

        self.assertIn("decoded_cache_matches_source must equal decoded_cache_determinism_checked", failures)


if __name__ == "__main__":
    unittest.main()
