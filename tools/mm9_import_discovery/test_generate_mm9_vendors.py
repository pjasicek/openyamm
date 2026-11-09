import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))

import generate_mm9_skill_trainers
import generate_mm9_vendors


class GenerateMm9VendorsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[2]

    def arguments(self, output_root: Path) -> SimpleNamespace:
        return SimpleNamespace(
            shops=self.root / "mm9/extracted/DATA/DATA/MMIXSHOPS.txt",
            concats=self.root / "mm9/extracted/DATA/DATA/CONCAT.csv",
            world_manifest=self.root / "assets_dev/worlds/mm9/world.yml",
            rude_directory=self.root / "assets_dev/worlds/mm9/dialogue/rude",
            mm9_items=self.root / "assets_dev/worlds/mm9/data_tables/items.txt",
            special_enchants=self.root / "assets_dev/engine/data_tables/special_item_enchants.txt",
            output_directory=output_root / "data_tables",
            audit=output_root / "state/vendor_stock_audit.yml",
        )

    def test_generation_is_complete_deterministic_and_runtime_quality_free(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_root = Path(temporary_directory)
            arguments = self.arguments(output_root)
            generate_mm9_vendors.generate(arguments)
            first_outputs = {
                path.relative_to(output_root): path.read_bytes()
                for path in sorted(output_root.rglob("*"))
                if path.is_file()
            }
            generate_mm9_vendors.generate(arguments)
            second_outputs = {
                path.relative_to(output_root): path.read_bytes()
                for path in sorted(output_root.rglob("*"))
                if path.is_file()
            }
            self.assertEqual(first_outputs, second_outputs)
            checked_in_root = self.root / "assets_dev/worlds/mm9"
            checked_in_outputs = {
                relative_path: (checked_in_root / relative_path).read_bytes()
                for relative_path in first_outputs
            }
            self.assertEqual(first_outputs, checked_in_outputs)

            with (arguments.output_directory / "vendors.txt").open(encoding="utf-8", newline="") as source_file:
                vendors = list(csv.DictReader(source_file, delimiter="\t"))
            # MMIXSHOPS's 48 and the world's added shops (ADDED_VENDORS: Hallvard's Tomes, Yorwick)
            self.assertEqual(len(vendors), 48 + len(generate_mm9_vendors.ADDED_VENDORS))
            self.assertEqual({row["source_type"] for row in vendors}, generate_mm9_vendors.SELLING_TYPES)
            self.assertEqual(sum(row["source_type"] == "Library" for row in vendors), 6)
            self.assertEqual(sum(row["source_type"] == "Magic" for row in vendors), 16)
            self.assertTrue(all(row["normalized_service_type"] == "Shop" for row in vendors))
            self.assertTrue(all(row["legacy_house_audio_policy"] == "Disabled" for row in vendors))
            self.assertTrue(all(row["legacy_house_video_policy"] == "Disabled" for row in vendors))
            self.assertTrue(all(row["buy_view"] == "Ledger" for row in vendors))

            with (arguments.output_directory / "service_venues.txt").open(
                encoding="utf-8", newline=""
            ) as source_file:
                service_venues = list(csv.DictReader(source_file, delimiter="\t"))
            self.assertEqual(len(service_venues), 30)
            self.assertEqual(sum(row["service_type"] == "Training" for row in service_venues), 8)
            self.assertEqual(sum(row["service_type"] == "Temple" for row in service_venues), 8)
            self.assertTrue(all(row["training_max_level"] == "0" for row in service_venues))
            self.assertEqual(sum(row["service_type"] == "Tavern" for row in service_venues), 7)
            self.assertEqual(sum(row["service_type"] == "Bank" for row in service_venues), 7)
            self.assertTrue(all((row["can_learn_skills"] == "1") == (row["service_type"] != "Bank")
                                for row in service_venues))
            inn = next(row for row in service_venues if row["source_service_id"] == "57")
            self.assertEqual((inn["price_multiplier"], inn["skill_price_multiplier"]), ("12", "1.2"))
            hall = next(row for row in service_venues if row["source_service_id"] == "62")
            self.assertEqual((hall["price_multiplier"], hall["skill_price_multiplier"]), ("10", "1"))
            fres_gift = next(row for row in service_venues if row["name"] == "Fre's Gift")
            self.assertEqual((fres_gift["price_multiplier"], fres_gift["skill_price_multiplier"]), ("12", "1.2"))
            self.assertTrue(any(row["source_service_id"] == "339" for row in service_venues))
            temple = next(row for row in service_venues if row["service_type"] == "Temple")
            self.assertEqual(temple["learn_skills"], "Regeneration|Meditation|Unarmed|Dodging")
            spirit_shop = next(row for row in vendors if row["magic_school"] == "Spirit")
            self.assertEqual(spirit_shop["learn_skills"], "SpiritMagic|MindMagic|BodyMagic|Meditation|Learning")
            # every skill the MM9 world trains has a Normal source in some venue (Blaster and the racial abilities
            # are the untaught exceptions; the racial classes start with theirs)
            learnable = {skill for row in vendors + service_venues for skill in row["learn_skills"].split("|") if skill}
            self.assertEqual(
                learnable,
                set(generate_mm9_skill_trainers.TRAINABLE_SKILLS) - set(generate_mm9_skill_trainers.UNTAUGHT_SKILLS))
            midwife = next(row for row in service_venues if row["source_service_id"] == "241")
            self.assertEqual(midwife["can_heal"], "1")
            self.assertEqual(midwife["can_donate"], "0")

            with (arguments.output_directory / "vendor_stock.txt").open(encoding="utf-8", newline="") as source_file:
                reader = csv.DictReader(source_file, delimiter="\t")
                self.assertNotIn("quality", reader.fieldnames)
                self.assertNotIn("source_q", reader.fieldnames)
                stock_rows = list(reader)
            self.assertGreater(len(stock_rows), 3000)
            self.assertTrue(all(int(row["item_id"]) > 0 for row in stock_rows))

            audit = json.loads(arguments.audit.read_text(encoding="utf-8"))
            self.assertEqual(audit["vendor_count"], 48 + len(generate_mm9_vendors.ADDED_VENDORS))
            with arguments.shops.open(encoding="cp1252", newline="") as source_file:
                source_rows = list(csv.reader(source_file, delimiter="\t"))
            self.assertEqual(audit["source_header"], source_rows[0])
            self.assertEqual(audit["source_row_count"], len(source_rows) - 1)
            reconstructed_source_rows = [
                [row["raw_fields"][field] for field in audit["source_field_names"]]
                for row in audit["source_rows"]
            ]
            self.assertEqual(reconstructed_source_rows, source_rows[1:])
            with arguments.concats.open(encoding="cp1252", newline="") as source_file:
                source_concat_rows = list(csv.reader(source_file))
            self.assertEqual(audit["concat_source_file"],
                             "mm9/extracted/DATA/DATA/CONCAT.csv")
            self.assertFalse(audit["concat_source_has_header"])
            self.assertEqual(audit["concat_source_field_count"], 25)
            self.assertEqual(audit["concat_source_row_count"], 104)
            self.assertEqual(
                [row["raw_fields"] for row in audit["concat_source_rows"]],
                source_concat_rows,
            )
            self.assertEqual(
                {row["source_concat_id"] for row in audit["concat_source_rows"]},
                {int(row[0]) for row in source_concat_rows},
            )
            with (arguments.output_directory / "vendor_concat_mappings.txt").open(
                encoding="utf-8", newline=""
            ) as source_file:
                concat_mappings = list(csv.DictReader(source_file, delimiter="\t"))
            self.assertEqual({row["source_concat_id"] for row in concat_mappings}, {"4", "49"})
            self.assertTrue(all(row["owner"] and row["reason"] for row in concat_mappings))
            self.assertEqual(
                {row["disposition"] for row in audit["source_rows"]},
                {"selling_vendor", "reachable_service_venue", "non_stock_service"},
            )
            self.assertEqual(audit["service_venue_count"], 30)
            self.assertEqual(audit["selling_vendors_without_rude_shop_row"], [138])
            self.assertEqual(audit["rude_shop_rows_without_selling_vendor"], [])
            self.assertEqual(audit["ordinary_effective_tier_cap"], 6)
            self.assertEqual(
                audit["quality_policy"]["quality_offsets"],
                {"Normal": 0, "Good": 1, "Excellent": 2},
            )
            self.assertFalse(audit["quality_policy"]["runtime_quality_fields_emitted"])
            self.assertFalse(audit["quality_policy"]["runtime_source_q_field_emitted"])
            self.assertEqual(audit["vendor_id_domain"]["begin"], 30000)
            self.assertEqual(audit["vendor_id_domain"]["end"], 30999)
            self.assertTrue(audit["vendor_id_domain"]["all_unique_and_in_range"])
            self.assertEqual(len(audit["vendor_id_domain"]["validated_canonical_ids"]), 79)
            self.assertEqual(audit["balance_boundary"]["artifact_relic_reserved_tier"], 7)
            self.assertFalse(audit["balance_boundary"]["rare_and_set_rows_admitted"])
            self.assertEqual(audit["coverage"]["library_vendor_count"], 6)
            self.assertEqual(audit["coverage"]["magic_vendor_count"], 16)
            self.assertFalse(audit["coverage"]["missing_library_coverage"])
            self.assertFalse(audit["coverage"]["missing_magic_school_coverage"])
            self.assertTrue(all(
                decision["owner"] and decision["reason"]
                for decision in audit["reviewed_policy_decisions"]
            ))
            slots = [
                slot
                for vendor in audit["vendors"]
                for lane in vendor["lanes"].values()
                for slot in lane["slots"]
            ]
            self.assertTrue(all(slot["effective_tier"] <= 6 for slot in slots))
            self.assertTrue(all(
                "source_tier" in slot and "normalized_base_tier" in slot
                for slot in slots
            ))
            self.assertTrue(any(slot["effective_tier"] == 6 for slot in slots))
            self.assertTrue(all(slot["runtime_mapping"]["item_id"] > 0 for slot in slots))
            self.assertTrue(all(
                slot["quality_conversion"]["final_overlay_statistics"]["runtime_quality_field_emitted"]
                is False
                and slot["quality_conversion"]["final_overlay_statistics"]["runtime_source_q_field_emitted"]
                is False
                for slot in slots
            ))
            self.assertTrue(all(
                slot["quality_conversion"]["application_count"]
                == (0 if slot["source_quality"] == "NotApplicable" else 1)
                for slot in slots
            ))
            self.assertTrue(all(
                slot["balance_boundary_validation"]["ordinary_l7_boundary_preserved"]
                and not slot["balance_boundary_validation"]["rare_item_admitted"]
                and not slot["balance_boundary_validation"]["quest_or_unique_item_admitted"]
                and not slot["balance_boundary_validation"]["set_piece_admitted"]
                and not slot["balance_boundary_validation"]["runtime_artifact_id_emitted"]
                for slot in slots
            ))
            mm9_content_slots = [slot for slot in slots if slot["item_id"] >= 10000]
            self.assertTrue(mm9_content_slots)
            self.assertTrue(all(
                slot["quality_conversion"]["base_normalized_statistics"]["inventory_width"] > 0
                and slot["quality_conversion"]["base_normalized_statistics"]["inventory_height"] > 0
                and slot["quality_conversion"]["base_normalized_statistics"]["visual_status"]
                for slot in mm9_content_slots
            ))
            self.assertTrue(all(
                slot["quality_conversion"]["final_overlay_statistics"][field]
                for slot in slots
                for field in (
                    "canonical_item_identity_retained",
                    "inventory_dimensions_retained",
                    "visual_mapping_retained",
                    "class_restrictions_retained",
                )
            ))
            concat_slots = [slot for slot in slots if slot["concat"]]
            non_concat_slots = [slot for slot in slots if not slot["concat"]]
            self.assertTrue(concat_slots)
            self.assertTrue(all(slot["concat_mapping"] is not None for slot in concat_slots))
            self.assertTrue(all(slot["concat_mapping"] is None for slot in non_concat_slots))
            self.assertTrue(all(
                slot["concat_mapping"]["applicable"]
                and slot["concat_mapping"]["source_tier"] <= slot["effective_tier"]
                and slot["concat_mapping"]["target_special_enchant_id"]
                == slot["runtime_mapping"]["special_enchant_id"]
                for slot in concat_slots
            ))
            self.assertTrue(all(
                all(flag == 1 for flag in slot["concat_mapping"]["source_applicability_flags"])
                if slot["concat_mapping"]["source_concat_id"] == 49
                else all(
                    slot["concat_mapping"]["source_raw_fields"][column] == "1"
                    for column in generate_mm9_vendors.SOURCE_CONCAT_WEAPON_COLUMNS
                )
                for slot in concat_slots
            ))

            spellbooks = [
                item for item in generate_mm9_vendors.read_items(arguments.mm9_items, "utf-8", "mm9")
                if item.equip_stat == "Book" and item.spellbook_mastery]
            stocked_books = {
                source_id: [
                    item for item in spellbooks
                    if generate_mm9_vendors.spell_school(item) in schools
                    and item.spellbook_mastery in generate_mm9_vendors.SPELLBOOK_STOCKED_MASTERIES_BY_SHOP.get(
                        source_id, generate_mm9_vendors.SPELLBOOK_STOCKED_MASTERIES)]
                for source_id, schools in generate_mm9_vendors.SPELLBOOK_STOCKED_SCHOOLS.items()
            }
            library_tier_sets = set()
            for vendor in audit["vendors"]:
                # Each shelf stocks within its own range (equipment shops: the tiers their chapter's treasure level
                # yields, mm9_vendor_balance.py; the special shelf one level above the standard one), except the
                # spellbooks some shops stock whatever their range (SPELLBOOK_STOCKED_SCHOOLS).
                stocked_names = {
                    item.name for item in stocked_books.get(vendor["source_vendor_id"], [])}
                admission_tiers = set()
                for lane_name, lane in vendor["lanes"].items():
                    minimum = max(1, lane["stock_range"][0])
                    maximum = max(1, lane["stock_range"][1])
                    lane_tiers = {
                        slot["admission_tier"] for slot in lane["slots"] if slot["item_name"] not in stocked_names}
                    self.assertTrue(all(minimum <= tier <= maximum for tier in lane_tiers))
                    admission_tiers |= lane_tiers
                if vendor["profile"] == "Mm9Library":
                    library_tier_sets.add(tuple(sorted(admission_tiers)))
            self.assertGreaterEqual(len(library_tier_sets), 3)

            audit_by_source_id = {vendor["source_vendor_id"]: vendor for vendor in audit["vendors"]}
            # Equipment shops stock by their chapter's treasure level (mm9_vendor_balance.py): Sturmford's weapon shop
            # (chapter 1, level 1 like MM7's Harmondale) sells tier 1 on its standard shelf and up to tier 3 on its
            # special shelf (level 2), with no special enchants.
            sturmford_weapon = audit_by_source_id[53]
            self.assertTrue({slot["admission_tier"] for slot in sturmford_weapon["lanes"]["standard"]["slots"]}
                            <= {1, 2})
            self.assertTrue({slot["admission_tier"] for slot in sturmford_weapon["lanes"]["special"]["slots"]}
                            <= {1, 2, 3})
            self.assertTrue(all(slot["runtime_mapping"]["special_enchant_id"] == 0
                                for lane in sturmford_weapon["lanes"].values() for slot in lane["slots"]))
            # Arslegard (chapter 5, level 5, special shelf 6): weapon specials at level 6's 50%.
            arslegard_special = audit_by_source_id[340]["lanes"]["special"]["slots"]
            self.assertTrue(arslegard_special)
            enchanted = sum(slot["runtime_mapping"]["special_enchant_id"] != 0 for slot in arslegard_special)
            self.assertTrue(0.3 * len(arslegard_special) <= enchanted <= 0.7 * len(arslegard_special))
            low_concat_lanes = [
                lane
                for vendor in audit["vendors"]
                for lane in vendor["lanes"].values()
                if 0 < lane["expected_concat_percent"] < 10
            ]
            self.assertTrue(low_concat_lanes)
            self.assertTrue(all(
                lane["realized_concat_percent"] > 0
                for lane in low_concat_lanes
                if lane["concat_eligible_slot_count"] > 0
            ))

            equipment_slots = [slot for slot in slots if slot["source_quality"] != "NotApplicable"]
            other_slots = [slot for slot in slots if slot["source_quality"] == "NotApplicable"]
            self.assertTrue(equipment_slots)
            self.assertTrue(other_slots)
            self.assertTrue(all(slot["source_q"] is not None for slot in equipment_slots))
            self.assertTrue(all(slot["source_q"] is None for slot in other_slots))
            self.assertTrue(all(
                slot["runtime_mapping"]["standard_enchant_id"] == 0
                and slot["runtime_mapping"]["special_enchant_id"] == 0
                for slot in other_slots
            ))
            # Standard enchants on equipment carry a power in the MM6-MM8 range of some treasure level (+1 to +25).
            self.assertTrue(all(
                1 <= slot["runtime_mapping"]["standard_enchant_power"] <= 25
                for slot in equipment_slots if slot["runtime_mapping"]["standard_enchant_id"] != 0
            ))
            for vendor in audit["vendors"]:
                self.assertEqual(vendor["runtime_price_multiplier"], vendor["source_merchant_base"])
                self.assertEqual(vendor["normalized_service_type"], "Shop")
                self.assertEqual(vendor["dialogue_scene_policy"], "LiveGameplay")
                self.assertEqual(vendor["legacy_house_audio_policy"], "Disabled")
                self.assertEqual(vendor["legacy_house_video_policy"], "Disabled")
                self.assertEqual(vendor["source_pair_interpretation"],
                                 "both_pairs_one_merchant_list")
                if vendor["source_vendor_id"] == 138:
                    self.assertFalse(vendor["opening_policy_provenance"])
                else:
                    self.assertTrue(vendor["opening_policy_provenance"])
                    self.assertTrue(all(
                        row["source_file"].endswith(".rude")
                        and row["source_line"] > 0
                        and row["raw_fields"]
                        for row in vendor["opening_policy_provenance"]
                    ))
                self.assertTrue(all(
                    override["owner"] and override["reason"]
                    for override in vendor["reviewed_overrides"]
                ))
                for lane in vendor["lanes"].values():
                    self.assertGreater(lane["candidate_count"], 0)
                    self.assertTrue(lane["rejected_candidate_counts"])
                    self.assertEqual(lane["concat_rounding_rule"],
                                     "largest_remainder_half_up_with_nonzero_minimum")
                    self.assertEqual(
                        lane["concat_target_count"],
                        sum(slot["concat"] for slot in lane["slots"]),
                    )
                    self.assertTrue(all(
                        not slot["concat"] or slot["source_quality"] != "NotApplicable"
                        for slot in lane["slots"]
                    ))
                    if (lane["expected_concat_percent"] == 0
                            and vendor["profile"] in {"Spellbook", "Mm9Library"}):
                        self.assertTrue(all(
                            slot["runtime_mapping"]["standard_enchant_id"] == 0
                            and
                            slot["runtime_mapping"]["special_enchant_id"] == 0
                            for slot in lane["slots"]
                        ))

            vendor_by_id = {int(row["vendor_id"]): row for row in vendors}
            vendor_by_source_id = {int(row["source_vendor_id"]): row for row in vendors}
            self.assertEqual(vendor_by_source_id[200]["restock_days"], "56")
            self.assertEqual(vendor_by_source_id[250]["standard_max"], "1")
            self.assertEqual(vendor_by_source_id[247]["standard_max"], "2")
            stock_by_vendor: dict[int, list[dict[str, str]]] = {}
            for row in stock_rows:
                stock_by_vendor.setdefault(int(row["vendor_id"]), []).append(row)
            mm9_items = {
                item.item_id: item
                for item in generate_mm9_vendors.read_items(arguments.mm9_items, "utf-8", "mm9")
            }
            for vendor_id, vendor in vendor_by_id.items():
                rows = stock_by_vendor[vendor_id]
                if vendor["source_type"] == "Library":
                    self.assertTrue(all(
                        mm9_items[int(row["item_id"])].equip_stat == "LearnSkill"
                        and "SkillLearning" in mm9_items[int(row["item_id"])].content_flags
                        for row in rows
                    ))
                if vendor["source_type"] == "Magic":
                    # MM9's own spellbooks (mm9_spellbooks.py), never another world's.
                    self.assertTrue(all(
                        10901 <= int(row["item_id"]) <= 10999
                        and mm9_items[int(row["item_id"])].equip_stat == "Book"
                        and "World:mm9" in mm9_items[int(row["item_id"])].content_flags
                        for row in rows
                    ))
                    school = generate_mm9_vendors.magic_school(vendor["merchandise"])
                    self.assertTrue(all(
                        generate_mm9_vendors.spell_school(mm9_items[int(row["item_id"])]) == school
                        or school == "All"
                        or (school == "Elemental" and generate_mm9_vendors.spell_school(
                            mm9_items[int(row["item_id"])]) in {"Fire", "Air", "Water", "Earth"})
                        # MM9's Spirit school merges MM6-MM8 Spirit, Mind and Body.
                        or (school == "Spirit" and generate_mm9_vendors.spell_school(
                            mm9_items[int(row["item_id"])]) in {"Mind", "Body"})
                        for row in rows
                    ))
                    # One book per spell on each restock page, six spells for each school the shop sells (user
                    # decisions 2026-11-06).
                    pages: dict[str, list[str]] = {}
                    for row in rows:
                        pages.setdefault(row["page"], []).append(
                            mm9_items[int(row["item_id"])].skill_group)
                    self.assertTrue(all(len(spells) == len(set(spells)) for spells in pages.values()))
                    schools = generate_mm9_vendors.SCHOOL_COUNT_BY_MAGIC_SCHOOL[school]
                    # A shop of only its stocked books (SPELLBOOK_STOCKED_ONLY) is checked below.
                    stocked_only = int(vendor["source_vendor_id"]) in generate_mm9_vendors.SPELLBOOK_STOCKED_ONLY
                    self.assertTrue(stocked_only or all(
                        len(spells) >= generate_mm9_vendors.SPELLBOOK_SPELLS_PER_SCHOOL * schools
                        for spells in pages.values()))

            # Frosgard's and Lindisfarne's spellbook shops stock every Expert and Master book of their listed schools
            # on each restock (user decision 2026-11-09).
            for source_id, books in stocked_books.items():
                self.assertTrue(books)
                vendor_id = int(vendor_by_source_id[source_id]["vendor_id"])
                pages: dict[str, set[int]] = {}
                for row in stock_by_vendor[vendor_id]:
                    pages.setdefault(row["page"], set()).add(int(row["item_id"]))
                self.assertTrue(pages)
                self.assertTrue(all({item.item_id for item in books} <= stocked for stocked in pages.values()))
                if source_id in generate_mm9_vendors.SPELLBOOK_STOCKED_ONLY:
                    # Hallvard's Tomes, Yorwick (the user, 2026-11-09): every Master and Grandmaster book, nothing else.
                    self.assertTrue(all({item.item_id for item in books} == stocked for stocked in pages.values()))
                    self.assertEqual(
                        {item.spellbook_mastery for item in books}, {"master", "grandmaster"})
                    self.assertEqual(len({item.skill_group for item in books}), len(books))

            library_item_ids = {
                int(row["item_id"])
                for vendor_id, rows in stock_by_vendor.items()
                if vendor_by_id[vendor_id]["source_type"] == "Library"
                for row in rows
            }
            self.assertEqual(library_item_ids, set(range(10285, 10308)))

    def test_quality_conversion_is_offline_and_clamped(self) -> None:
        item = generate_mm9_vendors.Item(
            item_id=1,
            name="Test armor",
            equip_stat="Armor",
            skill_group="",
            normalized_tier=4,
            source_item_id=1,
            source_treasure_tier=4,
            content_flags=frozenset(),
            rarity="Common",
            set_id="",
            source_equip_type="Armor",
            value=100,
        )
        vendor = generate_mm9_vendors.SourceVendor(
            source_line=1,
            name="Test",
            source_id=1,
            source_type="Armor",
            merchandise="Armor",
            wealth="Average",
            merchant_base=1.0,
            standard_min=3,
            standard_max=4,
            standard_concat=0,
            special_min=3,
            special_max=4,
            special_concat=0,
            source_quantity="",
            restock_text="2 Weeks",
        )
        self.assertEqual(generate_mm9_vendors.QUALITY_OFFSET, {"Normal": 0, "Good": 1, "Excellent": 2})
        self.assertEqual(generate_mm9_vendors.quality_for(vendor, "special", 0, item), "Excellent")
        effective_tier = min(6, item.normalized_tier + generate_mm9_vendors.QUALITY_OFFSET["Excellent"])
        self.assertEqual(effective_tier, 6)

        shield = generate_mm9_vendors.Item(
            item_id=2,
            name="Test shield",
            equip_stat="Shield",
            skill_group="Shield",
            normalized_tier=3,
            source_item_id=2,
            source_treasure_tier=3,
            content_flags=frozenset(),
            rarity="Common",
            set_id="",
            source_equip_type="Shield",
            value=100,
        )
        self.assertEqual(
            generate_mm9_vendors.mapped_enchants(shield, "Good", False, 4, 0),
            (10, 4, 0),
        )


if __name__ == "__main__":
    unittest.main()
