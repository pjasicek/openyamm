#!/usr/bin/env python3
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from generate_model_registry import source_path_to_virtual
from rewrite_scene_model_assets import ModelRegistry, rewrite_entry
from mm9_generate_actor_billboards import load_registry


def sample_registry() -> dict:
    return {
        "schema": "openyamm.mm9.model_registry.v2",
        "world": "mm9",
        "models": [
            {
                "model_id": "highwayman",
                "roles": ["actor_model"],
                "source_model": "models/highwayman.abc",
                "model_asset": "models/highwayman.glb",
                "model_sidecar": "models/highwayman.model.yml",
                "skin_bindings": [
                    {
                        "id": "highwayman_bandit",
                        "source_skins": ["skins/highwayman1.dtx"],
                        "actor_rows": [
                            {
                                "table": "ACTOR",
                                "row": 1,
                                "number": "1",
                                "monster_name": "Bandit",
                                "type_picture": "Highwayman",
                            }
                        ],
                    },
                    {
                        "id": "highwayman_cutpurse",
                        "source_skins": ["skins/highwayman2.dtx"],
                        "actor_rows": [
                            {
                                "table": "MONSTERS",
                                "row": 2,
                                "number": "2",
                                "monster_name": "Cutpurse",
                                "type_picture": "Highwayman",
                            }
                        ],
                    },
                ],
            }
        ],
    }


def sample_fallback_registry() -> dict:
    return {
        "schema": "openyamm.mm9.model_registry.v2",
        "world": "mm9",
        "models": [
            {
                "model_id": "spellbook1",
                "roles": ["static_model"],
                "source_model": "models/props/spellbook1.abc",
                "model_asset": "models/props/spellbook1.glb",
                "model_sidecar": "models/props/spellbook1.model.yml",
            },
            {
                "model_id": "sheep",
                "roles": ["actor_model"],
                "source_model": "models/sheep.abc",
                "model_asset": "models/sheep.glb",
                "model_sidecar": "models/sheep.model.yml",
                "skin_bindings": [
                    {
                        "id": "sheep_placeholder",
                        "source_skins": [],
                        "actor_rows": [
                            {
                                "table": "ACTOR",
                                "row": 57,
                                "number": "57",
                                "monster_name": "Commoner",
                                "type_picture": "Peasant Half-Orc Male A",
                                "base_name": "",
                            }
                        ],
                    }
                ],
            },
            {
                "model_id": "peasanthom1",
                "roles": ["actor_model"],
                "source_model": "models/peasanthom1.abc",
                "model_asset": "models/peasanthom1.glb",
                "model_sidecar": "models/peasanthom1.model.yml",
                "skin_bindings": [
                    {
                        "id": "peasanthom1_a",
                        "source_skins": ["skins/peasanthom1a.dtx"],
                        "actor_rows": [
                            {
                                "table": "MONSTERS",
                                "row": 57,
                                "number": "57",
                                "monster_name": "Commoner",
                                "type_picture": "Peasant Half-Orc Male A",
                                "base_name": "PeasantHOM",
                            }
                        ],
                    }
                ],
            },
        ],
    }


class ModelRegistryLayoutTests(unittest.TestCase):
    def test_source_path_to_virtual_preserves_original_model_subtree(self) -> None:
        self.assertEqual(
            source_path_to_virtual("mm9/extracted/MODELS/MODELS/PROPS/PLANTSANDTREES/TREE04.abc"),
            "models/props/plantsandtrees/tree04.abc",
        )
        self.assertEqual(source_path_to_virtual("MODELS/MODELS/HIGHWAYMAN.abc"), "models/highwayman.abc")

    def test_registry_resolves_actor_skin_bindings_without_variant_paths(self) -> None:
        registry = ModelRegistry(sample_registry())

        model_asset, skin_binding, resolution = registry.resolve("MODELS/HIGHWAYMAN.abc", "SKINS/HIGHWAYMAN2.dtx")
        self.assertEqual(model_asset, "models/highwayman.glb")
        self.assertEqual(skin_binding, "highwayman_cutpurse")
        self.assertIsNone(resolution)

        model_asset, skin_binding, resolution = registry.resolve("models/highwayman.abc", "", "Bandit")
        self.assertEqual(model_asset, "models/highwayman.glb")
        self.assertEqual(skin_binding, "highwayman_bandit")
        self.assertIsNone(resolution)

    def test_rewrite_keeps_geometry_asset_when_skin_binding_is_ambiguous(self) -> None:
        registry = ModelRegistry(sample_registry())
        entry = {"source_model": "models/highwayman.abc"}

        self.assertTrue(rewrite_entry(entry, registry))

        self.assertEqual(entry["model_asset"], "models/highwayman.glb")
        self.assertNotIn("model_skin_binding", entry)
        self.assertEqual(entry["model_resolution"]["status"], "skin_ambiguous")
        self.assertEqual(
            sorted(candidate["id"] for candidate in entry["model_resolution"]["candidates"]),
            ["highwayman_bandit", "highwayman_cutpurse"],
        )

    def test_resolver_uses_unique_stem_when_dat_folder_alias_differs(self) -> None:
        registry = ModelRegistry(sample_fallback_registry())

        model_asset, skin_binding, resolution = registry.resolve("models/pickupitems/spellbook1.abc", "")

        self.assertEqual(model_asset, "models/props/spellbook1.glb")
        self.assertEqual(skin_binding, "")
        self.assertIsNone(resolution)

    def test_resolver_prefers_authored_monster_row_over_actor_placeholder(self) -> None:
        registry = ModelRegistry(sample_fallback_registry())

        model_asset, skin_binding, resolution = registry.resolve(
            "models/peasantmale.abc",
            "",
            "CommonerHalfOrcMaleA",
        )

        self.assertEqual(model_asset, "models/peasanthom1.glb")
        self.assertEqual(skin_binding, "peasanthom1_a")
        self.assertIsNone(resolution)

    def test_billboard_registry_reader_accepts_v2_skin_bindings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            registry_path = Path(temp_dir) / "model_registry.yml"
            registry_path.write_text(yaml.safe_dump(sample_registry(), sort_keys=False), encoding="utf-8")

            variants = load_registry(registry_path, Path(temp_dir))

        self.assertEqual([variant.variant_id for variant in variants], ["highwayman_bandit", "highwayman_cutpurse"])
        self.assertEqual({variant.model_asset for variant in variants}, {"models/highwayman.glb"})
        self.assertEqual(variants[0].model_asset_path.as_posix(), f"{temp_dir}/models/highwayman.glb")


if __name__ == "__main__":
    raise SystemExit(unittest.main())
