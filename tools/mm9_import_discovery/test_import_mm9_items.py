from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import yaml
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))

from import_mm9_items import (
    import_items,
    load_body_equipment_visual_overlay,
    load_equipment_visual_overlay,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def run_import(tmp_path: Path, equipment_visual_overlay: Path | None = None) -> Path:
    source_root = REPOSITORY_ROOT / "mm9" / "extracted"
    output_root = tmp_path / "mm9"
    args = argparse.Namespace(
        source_root=source_root,
        output_root=output_root,
        master_items=source_root / "DATA" / "DATA" / "MASTERITEMLIST.csv",
        readable_text=source_root / "DATA" / "DATA" / "BOOK AND SCROLL TEXT.csv",
        icon_root=source_root / "ART" / "ART" / "INVENTORYICONS",
        script_root=source_root / "SCRIPTS" / "SCRIPTS",
        item_effects=REPOSITORY_ROOT / "tools" / "mm9_import_discovery" / "mm9_item_effects.yml",
        equipment_visual_overlay=equipment_visual_overlay,
        object_table=REPOSITORY_ROOT / "assets_dev" / "engine" / "data_tables" / "object_list.txt",
    )
    counts = import_items(args)
    assert counts == {"excluded": 131, "imported": 391, "mapped": 8}
    return output_root


def test_mm9_item_import_classifies_every_source_row(tmp_path: Path) -> None:
    output_root = run_import(tmp_path)
    report = yaml.safe_load((output_root / "state" / "item_import_report.yml").read_text(encoding="utf-8"))
    assert report["source_table_row_count"] == 529
    assert report["source_override_count"] == 1
    assert report["effective_row_count"] == 530
    assert sum(report["counts"].values()) == 530

    statuses = {entry["raw_mm9_id"]: entry["status"] for entry in report["items"]}
    assert statuses[253] == "mapped"
    assert statuses[347] == "mapped"
    assert {raw_id: statuses[raw_id] for raw_id in (511, 523, 532, 547, 548, 555)} == {
        raw_id: "mapped" for raw_id in (511, 523, 532, 547, 548, 555)
    }
    assert statuses[307] == "imported"
    assert statuses[504] == "excluded"
    assert statuses[590] == "imported"


def test_mm9_item_import_emits_stable_rows_and_readable_text(tmp_path: Path) -> None:
    output_root = run_import(tmp_path)
    with (output_root / "data_tables" / "items.txt").open(encoding="utf-8", newline="") as source_file:
        rows = list(csv.reader(source_file, delimiter="\t"))
    assert len(rows) == 392 + 99    # MASTERITEMLIST's imported items and MM9's own spellbooks
    by_id = {int(row[0]): row for row in rows[1:]}
    # MM9's spellbooks (mm9_spellbooks.py): one per spell, drawn by mastery, World:mm9.
    assert by_id[10901][1:3] == ["mm9_spellbook_normal", "Torch Light"]
    assert by_id[10911][1:3] == ["mm9_spellbook_grandmaster", "Incinerate"]
    assert by_id[10921][1:3] == ["mm9_spellbook_master", "Fleet Foot"]    # Fly's slot is MM9's Fleet Foot
    assert by_id[10921][18] == "mm9:item/spellbook_fly"
    assert {row[20] for item_id, row in by_id.items() if item_id >= 10901} == {"World:mm9"}
    assert by_id[10002][18] == "mm9:item/poor_sword"
    assert by_id[10002][3] == "40"   # the MM6-MM8 price of its 5.0 average damage
    assert by_id[10002][14:16] == ["14", "136"]
    assert by_id[10002][29:32] == ["1", "5", "generated_equipped_anchor_candidate"]
    assert by_id[10075][14:16] == ["4", "113"]
    assert by_id[10142][14:16] == ["30", "33"]
    assert by_id[10034][5] == "Throwing"
    assert by_id[10307][22] == "LearnSkill"
    assert by_id[10307][23] == "Throwing"
    assert by_id[10285][2] == "Blade Skill"
    assert by_id[10285][22] == "LearnSkill"
    assert by_id[10285][23] == "Sword|Dagger"
    assert by_id[10285][32] == "285"
    assert by_id[10285][43] == "reviewed_source_override"
    assert by_id[10285][44].endswith("mm9:item_source_override/blade_skill_285")
    assert by_id[10298][11] == "78"
    assert by_id[10370][11] == "20370"
    assert by_id[10371][11] == "20371"
    assert by_id[10590][4] == "Misc"
    assert by_id[10590][12] == "1"
    assert by_id[10590][22] == "GrantSkillPoints"
    assert by_id[10558][3] == "0"
    assert "Quest" in by_id[10558][20]
    assert by_id[10579][22] == "ReadText"
    assert by_id[10579][11] == "20579"
    assert by_id[10197][4] == "Weapon2"
    assert by_id[10197][5] == "Mace"
    assert set(by_id[10197][20].split("|")) >= {"Quest", "NoRandom", "NoShop"}
    assert "NoDrop" not in by_id[10197][20].split("|")
    assert by_id[10197][27] == "60"
    assert by_id[10160][29:31] == ["1", "2"]
    assert by_id[10155][29:31] == ["1", "1"]
    assert by_id[10133][29:31] == ["1", "2"]
    assert by_id[10132][29:31] == ["2", "2"]
    assert by_id[10086][29:31] == ["3", "3"]
    assert by_id[10086][31] == "generated_body_variants_reviewed"
    assert by_id[10108][29:31] == ["2", "3"]
    assert by_id[10056][29:31] == ["1", "9"]
    assert by_id[10061][29:31] == ["2", "9"]
    assert {by_id[10000 + raw_id][26] for raw_id in range(219, 224)} == {"Cavalier"}
    assert {by_id[10000 + raw_id][26] for raw_id in range(224, 229)} == {"Paladin"}
    assert {by_id[10000 + raw_id][26] for raw_id in range(229, 234)} == {"Necromancer"}
    assert {by_id[10000 + raw_id][26] for raw_id in range(234, 239)} == {"Cleric"}
    assert all(int(row[11]) > 0 for row in rows[1:])

    with (output_root / "data_tables" / "item_effects.txt").open(encoding="utf-8", newline="") as source_file:
        effect_rows = list(csv.reader(source_file, delimiter="\t"))
    effects_by_id = {int(row[0]): row for row in effect_rows[1:]}
    assert len(effects_by_id) == 63
    assert effects_by_id[10185][9] == "100"
    # Artifact effect lists come from the final effect, and MM9's typos are corrected (OY-588).
    assert effects_by_id[10200][3:5] == ["30", "30"]
    assert by_id[10200][16].endswith("(Effects: +30 Intellect, +30 Personality)")
    assert by_id[10179][16].endswith("(Effects: +40 Speed, +40 Accuracy, -50 SP)")
    assert "weilder" not in by_id[10175][16] and "wielder" in by_id[10175][16]

    with (output_root / "data_tables" / "item_sets.txt").open(encoding="utf-8", newline="") as source_file:
        set_rows = list(csv.reader(source_file, delimiter="\t"))
    assert len(set_rows) == 5

    with (output_root / "data_tables" / "readable_items.txt").open(encoding="utf-8", newline="") as source_file:
        readable_rows = list(csv.reader(source_file, delimiter="\t"))
    readable_by_id = {int(row[0]): row for row in readable_rows[1:]}
    assert readable_by_id[10579][2] == "Keyboard Layout"

    script_report = yaml.safe_load(
        (output_root / "state" / "item_script_reference_report.yml").read_text(encoding="utf-8"))
    assert script_report["counts"] == {
        "engine_mapping": 1,
        "mm9_mapping": 2,
        "world_definition": 164,
    }
    implosion_references = [
        entry for entry in script_report["references"]
        if entry["raw_mm9_id"] == 347
    ]
    assert len(implosion_references) == 2
    # Eye of the Storm is MM9's own Implosion book (mm9_spellbooks.py).
    assert {entry["resolution"] for entry in implosion_references} == {"mm9_mapping"}
    assert {entry["item_id"] for entry in implosion_references} == {10920}

    item_ids = yaml.safe_load(
        (output_root / "state" / "item_ids.yml").read_text(encoding="utf-8"))
    mappings = {
        entry["raw_mm9_id"]: entry["item_id"]
        for entry in item_ids["mappings"]
        if entry["kind"] in {"engine_mapping", "mm9_mapping"}
    }
    assert mappings == {
        253: 222,
        347: 10920,
        511: 317,
        523: 311,
        532: 306,
        547: 314,
        548: 379,
        555: 334,
    }

    import_report = yaml.safe_load(
        (output_root / "state" / "item_import_report.yml").read_text(encoding="utf-8"))
    poor_sword = next(entry for entry in import_report["items"] if entry["raw_mm9_id"] == 2)
    assert poor_sword["source_values"]["value"] == "50.00"
    assert poor_sword["normalized_values"]["value"] == 45
    assert "openyamm_category_tier_value_envelope" in poor_sword["balance_rule"]
    assert poor_sword["normalized_values"]["equip_x"] == 14
    assert poor_sword["normalized_values"]["equip_y"] == 136
    assert poor_sword["equipment_visual"] == {
        "reference_item_id": 3,
        "method": "reference_grip_transfer",
        "review_status": "candidate",
    }
    blade_skill = next(entry for entry in import_report["items"] if entry["raw_mm9_id"] == 285)
    assert blade_skill["source_override_id"] == "mm9:item_source_override/blade_skill_285"
    assert blade_skill["source_provenance"].startswith("SCRIPTS/SCRIPTS/SKILLBOOK.scr")

    icon_manifest = yaml.safe_load(
        (output_root / "state" / "item_icon_manifest.yml").read_text(encoding="utf-8"))
    poor_sword_icon = next(entry for entry in icon_manifest["icons"] if entry["raw_mm9_id"] == 2)
    assert poor_sword_icon["equip_anchor"] == [14, 136]
    assert poor_sword_icon["anchor_reference_item_id"] == 3
    assert poor_sword_icon["output"] == "icons_x2/mm9_item_10002.png"
    assert poor_sword_icon["scale"] == 2


def test_mm9_item_import_emits_complete_quest_misc_world_item_art(tmp_path: Path) -> None:
    output_root = run_import(tmp_path)
    manifest = yaml.safe_load(
        (output_root / "state" / "world_item_sprite_manifest.yml").read_text(encoding="utf-8"))
    assert manifest["kind"] == "mm9_world_item_sprite_manifest"
    assert manifest["item_count"] == 173
    assert manifest["visual_family_count"] == 49

    entries = manifest["items"]
    by_raw_id = {entry["raw_mm9_id"]: entry for entry in entries}
    assert len(by_raw_id) == 173
    assert set(by_raw_id) >= {197, 216, 239, 359, 369, 370, 371, 372, 398, 399, 557, 591, 600}
    assert 347 not in by_raw_id
    assert by_raw_id[370]["object_id"] == 20370
    assert by_raw_id[370]["sprite_id"] == 24370
    assert by_raw_id[370]["world_sprite"] == "sprites/mm9wi0370.png"

    with (output_root / "data_tables" / "object_descriptors.txt").open(
        encoding="utf-8", newline=""
    ) as source_file:
        object_rows = list(csv.DictReader(source_file, delimiter="\t"))
    assert len(object_rows) == 173
    assert {int(row["ObjectId"]) for row in object_rows} == {
        entry["object_id"] for entry in entries
    }
    assert {int(row["SpriteId"]) for row in object_rows} == {
        entry["sprite_id"] for entry in entries
    }

    sprite_frames = yaml.safe_load(
        (output_root / "rendering" / "sprite_frame_data_world_items.yml").read_text(encoding="utf-8"))
    assert len(sprite_frames["sprites"]) == 173
    assert {group["sprite_id"] for group in sprite_frames["sprites"]} == {
        entry["sprite_id"] for entry in entries
    }

    # The x2 inventory icon, halved to the x1 scale of world sprites.
    for entry in entries:
        with Image.open(output_root / entry["world_sprite"]) as world_sprite, \
                Image.open(output_root / entry["inventory_icon"]) as inventory_icon:
            assert world_sprite.size == tuple(-(-size // 2) for size in inventory_icon.size)


def test_mm9_equipment_visual_overlay_covers_every_imported_weapon_and_shield() -> None:
    overlay = load_equipment_visual_overlay(
        REPOSITORY_ROOT / "tools" / "mm9_import_discovery" / "mm9_item_equipment_visuals.yml")
    assert len(overlay) == 97
    assert set(definition["review_status"] for definition in overlay.values()) == {"candidate"}
    assert all(definition["method"] != "manual_grip_review" for definition in overlay.values())


def test_mm9_body_equipment_visual_overlay_covers_every_imported_armor() -> None:
    overlay = load_body_equipment_visual_overlay(
        REPOSITORY_ROOT / "tools" / "mm9_import_discovery" / "mm9_item_body_equipment_visuals.yml")
    assert len(overlay) == 35
    assert set(definition["review_status"] for definition in overlay.values()) == {"reviewed"}


def test_mm9_item_import_rejects_incomplete_equipment_visual_overlay(tmp_path: Path) -> None:
    overlay_path = REPOSITORY_ROOT / "tools" / "mm9_import_discovery" / "mm9_item_equipment_visuals.yml"
    overlay = yaml.safe_load(overlay_path.read_text(encoding="utf-8"))
    del overlay["items"][2]
    incomplete_path = tmp_path / "incomplete_equipment_visuals.yml"
    incomplete_path.write_text(yaml.safe_dump(overlay, sort_keys=False), encoding="utf-8")

    try:
        run_import(tmp_path / "output", incomplete_path)
    except ValueError as error:
        assert "coverage mismatch" in str(error)
        assert "missing=[2]" in str(error)
    else:
        raise AssertionError("incomplete equipment visual overlay was accepted")


def test_mm9_item_import_is_byte_deterministic(tmp_path: Path) -> None:
    first_root = run_import(tmp_path / "first")
    second_root = run_import(tmp_path / "second")
    relative_files = [
        Path("data_tables/items.txt"),
        Path("data_tables/readable_items.txt"),
        Path("data_tables/item_effects.txt"),
        Path("data_tables/item_sets.txt"),
        Path("data_tables/item_aliases.txt"),
        Path("state/item_ids.yml"),
        Path("state/item_import_report.yml"),
        Path("state/item_icon_manifest.yml"),
        Path("state/world_item_sprite_manifest.yml"),
        Path("state/item_script_reference_report.yml"),
        Path("icons_x2/mm9_item_10002.png"),
        Path("data_tables/object_descriptors.txt"),
        Path("rendering/sprite_frame_data_world_items.yml"),
        Path("sprites/mm9wi0370.png"),
    ]
    for relative_file in relative_files:
        assert (first_root / relative_file).read_bytes() == (second_root / relative_file).read_bytes()
