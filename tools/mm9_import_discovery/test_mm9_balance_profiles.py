#!/usr/bin/env python3
"""The MM9 balance rules (mm9_item_balance.py, mm9_monster_balance.py, mm9_vendor_balance.py;
devdocs/mm9_rework/BALANCE_PLAN.md section 3)."""
from __future__ import annotations

import sys
import unittest
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import mm9_chest_balance as chests  # noqa: E402
import mm9_density_targets as density  # noqa: E402
import mm9_ground_treasure as treasure  # noqa: E402
import mm9_item_balance as items     # noqa: E402
import mm9_monster_balance as monsters  # noqa: E402
import mm9_vendor_balance as vendors  # noqa: E402


class ItemBalanceTests(unittest.TestCase):
    def test_weapon_ladder_keeps_low_dice_and_grows_the_die_and_bonus(self) -> None:
        # Poor Sword (tier 1) keeps 2d4; Imperial Sword (tier 5, 3d3) gets two die sizes and the bonus to MM6-MM8's
        # tier 6 (20.3): MM9's top quality stands for their top pieces.
        self.assertEqual(items.ordinary_weapon("Sword 1H", 1, (2, 4))[:2], ("2d4", "0"))
        mod1, mod2, rule = items.ordinary_weapon("Sword 1H", 5, (3, 3))
        self.assertEqual((mod1, mod2), ("3d5", "11"))
        self.assertEqual(rule, "weapon_ladder:Sword1H")

    def test_dice_far_above_the_target_lose_die_size(self) -> None:
        self.assertEqual(items.ordinary_weapon("Mace 1H", 1, (2, 6))[:2], ("2d4", "0"))

    def test_halberds_follow_the_two_handed_ladder_and_spears_turn_one_or_two_handed(self) -> None:
        self.assertEqual(items.weapon_family("Weapon2", "Spear", "Halberd"), "Spear 2H")
        self.assertEqual(items.weapon_family("Weapon2", "Spear", "Spear"), "Spear")

    def test_armor_scales_to_the_target_and_keeps_the_order_within_a_tier(self) -> None:
        low = items.ordinary_armor("Chain", 4, 6, 10, 17.0)
        high = items.ordinary_armor("Chain", 4, 6, 12, 17.0)
        self.assertLess(int(low[0]) + int(low[1]), int(high[0]) + int(high[1]))
        self.assertAlmostEqual((int(low[0]) + int(low[1]) + int(high[0]) + int(high[1])) / 2, 20, delta=1)

    def test_top_ordinary_quality_stands_for_tier_six(self) -> None:
        self.assertEqual([items.reference_tier(tier) for tier in range(1, 6)], [1, 2, 3, 4, 6])
        self.assertEqual(items.armor_target("Chain", 5), 39)
        self.assertEqual(items.armor_target("Plate", 5), 59)
        self.assertEqual(items.armor_target("Plate", 4), 26)
        self.assertEqual(items.armor_target("Helm", 4), 9)   # hats and crowns no longer pull the helm median down

    def test_armor_prices_follow_the_mm6_mm8_curve_of_the_slot(self) -> None:
        self.assertEqual(items.armor_price("Plate", 18), 750)
        self.assertEqual(items.armor_price("Plate", 38), 2000)
        self.assertEqual(items.armor_price("Chain", 30), 1500)
        self.assertEqual(items.armor_price("Leather", 10), 450)
        self.assertEqual(items.armor_price("Helm", 15), 1100)
        self.assertEqual(items.armor_price("Boots", 1), 10)

    def test_prices_are_round(self) -> None:
        self.assertEqual([items.round_price(v) for v in (0, 12, 43, 437, 625, 1093, 1468, 25000)],
                         [0, 10, 45, 450, 650, 1100, 1500, 25000])

    def test_rare_armor_is_capped_by_slot(self) -> None:
        self.assertEqual(items.rare_armor("Plate", 202, 18, 75)[:2], ("18", "57"))   # Swordsbane 93 -> 75

    @staticmethod
    def engine_reference() -> items.EngineReference:
        item_rows = [["Item #", "Pic File", "Name", "Value", "Equip Stat", "Skill Group", "Mod1", "Mod2", "material",
                      "content_flags"],
                     ["1", "", "Longsword", "50", "Weapon", "Sword", "3d3", "0", "0", ""],
                     ["2", "", "Broadsword", "60", "Weapon", "Sword", "3d4", "0", "0", ""],
                     ["3", "", "Lionheart", "750", "Weapon", "Sword", "3d3", "15", "0", ""],
                     ["4", "", "Artifact Sword", "20000", "Weapon", "Sword", "3d3", "17", "Artifact", ""],
                     ["5", "", "Quest Ring", "100", "Ring", "Misc", "0", "0", "0", "NoRandom"],
                     ["6", "", "Copper Ring", "100", "Ring", "Misc", "0", "0", "0", ""],
                     ["7", "", "Silver Ring", "300", "Ring", "Misc", "0", "0", "0", ""],
                     ["8", "", "Potion", "10", "Bottle", "Misc", "0", "0", "0", ""]]
        random_rows = [["1", "", "8", "2", "0", "0", "0", "0"], ["2", "", "6", "4", "0", "0", "0", "0"],
                       ["3", "", "0", "0", "0", "0", "0", "5"], ["4", "", "0", "0", "0", "0", "0", "5"],
                       ["5", "", "0", "5", "0", "0", "0", "0"], ["6", "", "0", "10", "5", "0", "0", "0"],
                       ["7", "", "0", "8", "7", "0", "0", "0"], ["8", "", "20", "0", "0", "0", "0", "0"]]
        return items.EngineReference.from_tables(item_rows, random_rows)

    def test_mm9_items_weigh_like_mm6_mm8_items_of_their_family_and_tier(self) -> None:
        reference = self.engine_reference()
        self.assertEqual(reference.weights("Sword 1H", 1), [7, 3, 0, 0, 0, 0])   # mean of the two tier 1 swords
        self.assertEqual(reference.weights("Sword 1H", 5), [0, 0, 0, 0, 0, 5])   # the top quality as tier 6
        # No tier 1 ring: the lowest MM6-MM8 rings' weights (artifacts and NoRandom rows left out).
        self.assertEqual(reference.weights("Ring", 1), [0, 9, 6, 0, 0, 0])

    def test_random_item_rows_carry_the_reference_weights(self) -> None:
        header = ["Item #", "Pic File", "Name", "Equip Stat", "Skill Group", "material", "content_flags",
                  "normalized_tier", "x_mm9_source_name_type"]
        columns = {name: index for index, name in enumerate(header)}
        rows = [["10002", "a", "Poor Sword", "Weapon", "Sword", "8", "", "1", "Short Sword"],
                ["10009", "b", "Imperial Sword", "Weapon", "Sword", "8", "", "5", "Long Sword"],
                ["10175", "c", "Sing Sword", "Weapon", "Sword", "Artifact", "Unique", "7", "Short Sword"],
                ["10300", "d", "Potion", "Bottle", "Misc", "0", "", "1", ""]]
        out = {row[0]: [int(weight) for weight in row[2:8]]
               for row in items.random_item_rows(rows, columns, self.engine_reference())}
        self.assertEqual(out, {"10002": [7, 3, 0, 0, 0, 0], "10009": [0, 0, 0, 0, 0, 5]})

    def test_weapon_prices_follow_the_monotone_mm6_mm8_curve_of_the_family(self) -> None:
        reference = self.engine_reference()
        self.assertEqual(reference.weapon_price("Sword 1H", 6.0), 50)
        self.assertEqual(reference.weapon_price("Sword 1H", 21.0), 750)
        self.assertEqual(reference.weapon_price("Sword 1H", 13.5), 350)          # between 7.5 (60) and 21 (750)
        self.assertEqual(items.isotonic_curve([(1, 10), (2, 30), (3, 20), (4, 40)]),
                         [(1.0, 10.0), (2.5, 25.0), (4.0, 40.0)])

    def test_jewellery_costs_the_median_of_its_tier_or_the_lowest_tier_cheapest(self) -> None:
        reference = self.engine_reference()
        self.assertEqual(reference.tier_price("Ring", 2), 200)
        self.assertEqual(reference.tier_price("Ring", 1), 100)
        self.assertIsNone(reference.tier_price("Amulet", 3))

    def test_effects_regenerate_one_hit_point_a_second_and_the_pendant_gives_three_per_school(self) -> None:
        self.assertEqual(items.balance_effect(183, {"health_regen_per_second": 0.2})["health_regen_per_second"], 1.0)
        pendant = items.balance_effect(215, {"skill_bonuses": {"FireMagic": 5, "Learning": 3}})
        self.assertEqual(pendant["skill_bonuses"], {"FireMagic": 3, "Learning": 3})


class MonsterBalanceTests(unittest.TestCase):
    def test_dice_scale_bonus_first(self) -> None:
        self.assertEqual(monsters.scale_dice("1D9+2", 0.75), "1D8+1")   # 7.0 x 0.75 = 5.25; 1D8+1 averages 5.5

    def test_treasure_pays_gold_by_xp_with_the_item_kind_kept(self) -> None:
        treasure = monsters.treasure(16, 900, "25%L1Weapon")
        self.assertRegex(treasure, r"^\d+%\d+d\d+\+L3Weapon$")

    def test_treasure_levels_follow_mm7_stages_on_mm9_levels(self) -> None:
        self.assertEqual([monsters.treasure_level(level) for level in (1, 7, 8, 15, 16, 30, 31, 44, 45, 64, 65, 80)],
                         [1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6])

    def test_the_fire_hydra_spike_is_gone_from_the_41_55_items_rate(self) -> None:
        rates = {top: items_rate for top, _, items_rate in monsters.LOOT_BANDS}
        self.assertLessEqual(rates[55], 1.1 * max(rates[40], rates[80]))

    def test_bosses_always_drop_a_level_six_item(self) -> None:
        self.assertRegex(monsters.treasure(60, 6300, "0", boss=True), r"^100%\d+d\d+\+L6$")
        story_boss = ["9292", "Tamur Leng", "", "60", "720", "30", "6300", "0", "", "", "", "", "4", "", "192",
                      "", "", "", "4D3+30", "", "", "", "0", "", "0", "0", "0", "0"] + ["0"] * 11
        friendly = ["9249", "Sven Svenssen", "", "100", "900", "30", "16500", "0", "", "", "", "", "4", "", "192",
                    "", "", "", "4D3+30", "", "", "", "0", "", "0", "0", "0", "0"] + ["0"] * 11
        monsters.balance_monster_rows([story_boss, friendly], [])
        self.assertRegex(story_boss[monsters.TREASURE], r"^100%\d+d50\+L6$")
        self.assertEqual(friendly[monsters.TREASURE], "0")

    def test_families_give_one_immunity_strength_or_weakness(self) -> None:
        self.assertEqual(monsters.family_of("Skeleton Warrior"), (("mind",), ("body",), ("spirit",)))
        self.assertEqual(monsters.family_of("Jellyspore")[2], ("fire",))
        self.assertIsNone(monsters.family_of("Commoner"))

    def test_rows_change_only_for_combat_families(self) -> None:
        row = ["9135", "Skeleton", "", "16", "87", "10", "900", "25%L1Weapon", "", "", "", "", "4", "", "59", "", "",
               "", "2D12", "", "", "", "0", "", "100", "Fear,M,30", "0", "0"] + ["0"] * 11
        townsfolk = ["9001", "Commoner", "", "1", "4", "3", "17", "0", "", "", "", "", "4", "", "20", "", "", "",
                     "2D2", "", "", "", "0", "", "0", "0", "0", "0"] + ["0"] * 11
        monsters.balance_monster_rows([row, townsfolk], [])
        self.assertEqual(row[monsters.RECOVERY], "75")
        self.assertEqual(row[monsters.SPELL1_USE], "25")                   # a condition spell
        self.assertEqual(row[monsters.SCHOOLS["mind"]], "Imm")
        self.assertEqual(townsfolk[monsters.RECOVERY], "20")


@dataclass
class _Vendor:
    source_id: int
    profile: str
    standard_min: int = 1
    standard_max: int = 1
    special_min: int = 1
    special_max: int = 1


@dataclass
class _Item:
    equip_stat: str


class VendorBalanceTests(unittest.TestCase):
    def test_equipment_shops_take_their_city_tier(self) -> None:
        self.assertEqual(vendors.shop_tier(_Vendor(53, "Weapon"), "Sturmford"), 1)   # MM7's Harmondale: 1 and 2
        self.assertEqual(vendors.shop_tier(_Vendor(53, "Weapon"), "Yorwick"), 4)
        self.assertEqual(vendors.shop_tier(_Vendor(1, "Spellbook"), "Sturmford"), 0)
        widened = vendors.admitting_vendor(_Vendor(53, "Weapon"), 1)
        self.assertEqual((widened.standard_min, widened.standard_max), (1, 1))
        self.assertEqual((widened.special_min, widened.special_max), (1, 3))

    def test_special_shelf_rolls_enchants_like_loot_of_its_level(self) -> None:
        standard = [vendors.EnchantRow(1, {"Arm": 10}, "")]
        special = [vendors.EnchantRow(4, {"W1": 20}, "A")]

        def rolls(item: str, tier: int) -> list[tuple[int, int, int]]:
            return [vendors.roll_enchants(_Item(item), _Vendor(53, item), "special", page, slot, tier,
                                          standard, special) for page in range(10) for slot in range(30)]

        # Shop tier 1: the special shelf is treasure level 2, where weapons carry no specials (MM7).
        self.assertTrue(all(roll == (0, 0, 0) for roll in rolls("Weapon", 1)))
        # Shop tier 2: level 3, weapon specials at 10%, armour bonuses (power 3-8) at 40%.
        weapon_specials = sum(roll[2] == 4 for roll in rolls("Weapon", 2))
        self.assertTrue(10 <= weapon_specials <= 60)
        armour = [roll for roll in rolls("Armor", 2) if roll[0]]
        self.assertTrue(80 <= len(armour) <= 160)
        self.assertTrue(all(3 <= power <= 8 for _, power, _ in armour))


class DensityTargetTests(unittest.TestCase):
    ROWS = {9135: ("Skeleton", 16), 9001: ("Commoner", 1), 9200: ("Skeleton Lord", 200)}

    def actor(self, **fields) -> dict:
        return {"monster_info_id": 9135, "npc_id": 0, "hostility_type": 4, **fields}

    def test_counts_hostile_family_monsters_only(self) -> None:
        self.assertTrue(density.counted_actor(self.actor(), self.ROWS, "beethoven"))
        self.assertFalse(density.counted_actor(self.actor(monster_info_id=9001), self.ROWS, "beethoven"))
        self.assertFalse(density.counted_actor(self.actor(monster_info_id=9200), self.ROWS, "beethoven"))
        self.assertFalse(density.counted_actor(self.actor(npc_id=12), self.ROWS, "beethoven"))
        self.assertFalse(density.counted_actor(self.actor(mm9_ai={"profile": {"passive": True}}), self.ROWS, "x"))

    def test_swimmers_do_not_count_outdoors(self) -> None:
        # The Jellyspore family and the Sea Monsters stay in the sea and lakes outdoors (modifiers.yml movement swim;
        # the user, 2026-11-07), so a party need not fight them; in a dungeon's pools they count.
        rows = {9168: ("Jellyspore", 15), 9170: ("Nettle Spore", 25), 9177: ("Sea Monster Male", 50)}
        self.assertTrue({9168, 9169, 9170, 9177, 9178} <= density.swimmer_rows())
        for monster in rows:
            for stem in ("isleofashes", "sturmford", "thronheim", "thjorgard", "guberland"):
                self.assertFalse(density.counted_actor(self.actor(monster_info_id=monster), rows, stem))
            self.assertTrue(density.counted_actor(self.actor(monster_info_id=monster), rows, "bathhouse"))

    def test_the_temple_of_honk_counts_its_congregation_placed_non_hostile(self) -> None:
        self.assertFalse(density.counted_actor(self.actor(hostility_type=0), self.ROWS, "beethoven"))
        self.assertTrue(density.counted_actor(self.actor(hostility_type=0), self.ROWS, "templeofhonk"))


class ChestBalanceTests(unittest.TestCase):
    def chest(self, level: int, model: str = "models\\Props\\Chest1.ABC", **fields) -> dict:
        return {"random_treasure_level": level, "random": True, "gold_only": False, "source_model": model,
                "fixed_items": [], **fields}

    def test_black_chests_hold_one_artifact_record_and_fixed_ones_stay(self) -> None:
        black = self.chest(6, "models\\Props\\BlackChest.ABC")
        fixed = self.chest(0, "models\\Props\\BlackChest.ABC", random=False, fixed_items=[{"item_id": 10184}])
        chests.balance_loot_containers("lichlab", [black, fixed])
        self.assertEqual((black["random_treasure_level"], black["random_records"]), (7, 1))
        self.assertEqual(fixed["random_treasure_level"], 0)
        self.assertNotIn("random_records", fixed)

    def test_level_zero_takes_the_maps_most_common_level_and_every_chest_holds_mm7s_average(self) -> None:
        containers = [self.chest(0), self.chest(1), self.chest(1), self.chest(2)]
        chests.balance_loot_containers("thearena", containers)  # a map without TIERS
        self.assertEqual([c["random_treasure_level"] for c in containers], [1, 1, 1, 2])
        self.assertEqual({c["random_records"] for c in containers}, {3})

    def test_tier_floor_raises_records_to_the_level_the_maps_remap_turns_into_that_tier(self) -> None:
        # Ta'Sar Academy (map treasure level 2): record level 5 remaps to T3-T4; a black chest keeps its artifact
        containers = [self.chest(1), self.chest(2), self.chest(6, "models\\Props\\BlackChest.ABC")]
        chests.balance_loot_containers("tasaracademy", containers)
        self.assertEqual([c["random_treasure_level"] for c in containers], [5, 5, 7])
        for level, record in {2: 6, 3: 5, 4: 4, 5: 4, 6: 4}.items():
            self.assertEqual(chests.record_level_for_tiers((4, 4), level), record)
        with self.assertRaises(SystemExit):  # a level-1 map gives T2 at most
            chests.record_level_for_tiers((2, 3), 1)

    def test_every_maps_tiers_are_reachable_on_its_treasure_level(self) -> None:
        # Drangheim's T2-T3 needs its raised treasure level (2): level-3 records remap to T2 or T3
        self.assertEqual(chests.map_treasure_level("drangheim"), 2)
        self.assertEqual(chests.record_level_for_tiers((2, 3), 2), 3)
        for stem, tiers in chests.TIERS.items():
            chests.record_level_for_tiers(tiers, chests.map_treasure_level(stem))
        for (stem, _), tiers in chests.CONTAINER_TIERS.items():
            chests.record_level_for_tiers(tiers, chests.map_treasure_level(stem))

    def test_a_container_tier_replaces_its_maps_tier(self) -> None:
        # Verhoffin Ruins (map level 4): its chests T4-T5 (record 5), its first chest T4 (record 4)
        containers = [self.chest(5, source_name="TreasureChest3"), self.chest(5, source_name="TreasureChest4")]
        chests.balance_loot_containers("verhoffinruins", containers)
        self.assertEqual([c["random_treasure_level"] for c in containers], [4, 5])


class GroundTreasureTests(unittest.TestCase):
    def test_every_maps_marker_classes_are_reachable_and_ordered(self) -> None:
        for stem in treasure.COUNTS:
            tiers = treasure.marker_tiers(stem)
            for cls, rng in tiers.items():
                treasure.marker_index(stem, rng)           # raises when the map's level cannot give it
            self.assertGreaterEqual(sum(tiers["bonus"]), sum(tiers["main"]), stem)
            self.assertLessEqual(sum(tiers["lower"]), sum(tiers["main"]), stem)

    def test_a_bonus_is_one_tier_above_the_chests_where_the_map_reaches_it(self) -> None:
        self.assertEqual(treasure.marker_tiers("drangheim")["bonus"], (4, 4))        # chests T2-T3, map level 2
        self.assertEqual(treasure.marker_tiers("tasaracademy")["bonus"], (4, 4))     # chests T3-T4: T4 is its best
        self.assertEqual(treasure.marker_tiers("lichlab")["bonus"], (5, 5))
        self.assertEqual(treasure.marker_tiers("beethoven"), {"bonus": (2, 2), "main": (2, 2), "lower": (1, 1)})

    def test_class_counts_add_up(self) -> None:
        for stem in ("beethoven", "1000terrors"):
            for count in range(0, 30):
                for spots in (False, True):
                    counts = treasure.class_counts(stem, count, spots)
                    self.assertEqual(sum(counts.values()), count)
                    self.assertEqual(counts["bonus"] > 0, spots and count > 0)

    def test_1000_terrors_floor_items_are_60_percent_t5(self) -> None:
        counts = treasure.class_counts("1000terrors", treasure.COUNTS["1000terrors"], True)
        tiers = treasure.marker_tiers("1000terrors")
        self.assertEqual(tiers, {"bonus": (6, 6), "main": (6, 6), "lower": (5, 5)})
        self.assertEqual(counts, {"bonus": 4, "main": 7, "lower": 17})          # 17 T5, 11 T6 of 28


if __name__ == "__main__":
    unittest.main()
