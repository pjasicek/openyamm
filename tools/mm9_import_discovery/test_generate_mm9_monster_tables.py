#!/usr/bin/env python3
from __future__ import annotations

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_mm9_monster_tables as generator


# MONSTERS.txt's Bonus column (Y), which MM9 loads and never reads.
BONUS_COLUMN = 24


def source_row(bonus: str = "0", **values: str) -> list[str]:
    row = ["0"] * generator.SOURCE_COLUMN_COUNT
    row[BONUS_COLUMN] = bonus
    defaults = {
        "number": "1", "name": "Test Monster", "level": "20", "hp": "120", "ac": "30",
        "experience": "900", "treasure_type": "Item", "fly": "0", "move": "5",
        "walk_velocity": "75", "run_velocity": "250", "fly_velocity": "0",
        "recovery": "30", "attack1_type": "Elem",
        "attack1_damage": "3D7+4", "attack1_projectile": "GreenThingy",
        "attack2_chance": "50", "attack2_type": "Phys", "attack2_damage": "2D6",
        "attack2_projectile": "0", "spell1_chance": "0", "spell1": "0",
        "spell2_chance": "0", "spell2": "0", "elemental_resistance": "30",
        "spirit_resistance": "40", "dark_resistance": "50", "light_resistance": "60",
        "physical_resistance": "70", "script": "baserange.scr", "is_monster": "1",
        "hostility_group": "4", "treasure_level": "3", "attack3_projectile": "0",
        "attack3_chance": "0", "attack3_type": "0", "attack3_damage": "0", "resurrect": "0",
    }
    defaults.update(values)
    for name, value in defaults.items():
        row[generator.SOURCE_COLUMN[name]] = value
    return row


class Mm9MonsterTableGenerationTests(unittest.TestCase):
    def test_source_stats_and_resistance_families_are_preserved(self) -> None:
        row = generator.build_data_row(1, source_row(), ["0"] * 39)

        self.assertEqual(row[3:7], ["20", "120", "30", "900"])
        self.assertEqual(row[13], "320")
        # Recovery 30 MM9 game seconds of 33 ms: 0.99 s, 59 ticks of 1/60 s.
        self.assertEqual(row[14], "59")
        self.assertEqual(row[17:20], ["Earth", "3D7+4", "Earth"])
        self.assertEqual(row[28:32], ["30", "30", "30", "30"])
        self.assertEqual(row[32:35], ["40", "40", "40"])
        self.assertEqual(row[35:38], ["60", "50", "70"])

    def test_farm_animals_wander_friendly_but_the_evil_mouse_does_not(self) -> None:
        animal = source_row(move="0", walk_velocity="25", run_velocity="150", is_monster="0", hostility_group="2")
        row = generator.build_data_row(267, animal, ["0"] * 39)
        self.assertEqual(row[10:13], ["Med", "Wimp", "0"])
        self.assertEqual(row[13], "192")

        row = generator.build_data_row(300, animal, ["0"] * 39)
        self.assertEqual(row[10:13], ["Short", "Aggress", "4"])

    def test_move_zero_moves_and_only_zero_velocities_are_stationary(self) -> None:
        # MM9 never reads Move: a Magreeb (Move 0, 50/150) walks; a Lobber (Move 4, no velocity) never moves.
        magreeb = source_row(move="0", walk_velocity="50", run_velocity="150", script="Magreeb.scr")
        self.assertEqual(generator.build_data_row(277, magreeb, ["0"] * 39)[10], "Short")
        lobber = source_row(move="4", walk_velocity="0", run_velocity="0", fly_velocity="0", script="lobber.scr")
        self.assertEqual(generator.build_data_row(86, lobber, ["0"] * 39)[10:12], ["Stationary", "Normal"])

    def test_immunity_and_physical_projectile_adaptation(self) -> None:
        source = source_row(
            attack1_type="Phys", attack1_projectile="Axe",
            elemental_resistance="1000", spirit_resistance="1000",
        )
        row = generator.build_data_row(1, source, ["0"] * 39)

        self.assertEqual(row[19], "MM9Axe")
        self.assertEqual(row[28:35], ["Imm"] * 7)

    def test_two_spells_split_every_cast_by_spell_use_one(self) -> None:
        source = source_row(
            attack1_projectile="Spell", attack2_chance="0", spell1_chance="50", spell1="40,E,6,4 (Sparks)",
            spell2_chance="0", spell2="12,E,6,1 (Elemental Bolt)",
        )
        row = generator.build_data_row(1, source, ["0"] * 39)

        # No attack 2: every RangeAttack casts. Spell 1 by SpellUse%1, else spell 2 (sequential: 50, then 100).
        # Sparks E6 (7 sparks) fires at Master (7 sparks), skill kept; Elemental Bolt E6 (21) as Lightning Bolt (4.5 s).
        self.assertEqual(row[24:28], ["50", "Sparks,M,6", "100", "Lightning Bolt,E,5"])

    def test_spell_chance_is_the_complement_of_att_with_attack_two(self) -> None:
        # The Oculus: Att% 50 with attack 2, Paralyze at SpellUse%1 25, Curse: 12.5 % and 37.5 % of the shots.
        oculus = source_row(
            attack1_projectile="BlueLine", attack2_chance="50", attack2_dice="10", attack2_sides="20",
            attack2_bonus="10", spell1_chance="25", spell1="29,E,10,1 (Paralyze)",
            spell2_chance="75", spell2="5,M,8,5 (Curse)",
        )
        self.assertEqual(generator.build_data_row(230, oculus, ["0"] * 39)[24:28],
                         ["13", "Paralyze,E,10", "43", "Dark Grasp,M,8"])
        # A lone spell takes the whole share whatever SpellUse%1 holds (the Honk: SpellUse%1 0, Att% 75).
        honk = source_row(
            attack1_projectile="Egg", attack2_chance="75", attack2_dice="6", attack2_sides="10",
            spell1_chance="0", spell1="41,M,10,1 (SpellReaver)",
        )
        self.assertEqual(generator.build_data_row(186, honk, ["0"] * 39)[24:26], ["25", "Dispel Magic,M,10"])
        # Att% without attack 2 damage does not count: the Dragonfly-like row casts on every shot.
        no_attack2 = source_row(attack1_projectile="BlueThingy", attack2_chance="50", spell1_chance="100",
                                spell1="12,N,1,1 (Elemental Bolt)")
        self.assertEqual(generator.build_data_row(1, no_attack2, ["0"] * 39)[24], "100")

    def test_sequential_chances_reproduce_mm9_two_rolls(self) -> None:
        self.assertEqual(generator.sequential_spell_chances(50, 25, True, True), (13, 43))
        self.assertEqual(generator.sequential_spell_chances(85, 20, True, True), (17, 82))
        self.assertEqual(generator.sequential_spell_chances(100, 95, True, True), (95, 100))
        self.assertEqual(generator.sequential_spell_chances(100, 100, True, True), (100, 0))
        self.assertEqual(generator.sequential_spell_chances(25, 0, True, False), (25, 0))
        self.assertEqual(generator.sequential_spell_chances(100, 0, True, True), (0, 100))
        self.assertEqual(generator.sequential_spell_chances(60, 30, False, True), (0, 60))
        for total in range(0, 101, 5):
            for share in range(0, 101, 5):
                spell1, spell2 = generator.sequential_spell_chances(total, share, True, True)
                cast = spell1 + (100 - spell1) * spell2 / 100
                self.assertAlmostEqual(cast, total, delta=1.0)
                self.assertAlmostEqual(spell1, total * share / 100, delta=0.5)

    def test_two_non_offensive_spells_are_never_cast(self) -> None:
        reverend = source_row(
            attack1_projectile="Spell", attack2_chance="0", spell1_chance="85", spell1="27,M,10,2 (Natural Armor)",
            spell2_chance="0", spell2="23,M,7,1 (Heal)",
        )
        self.assertEqual(generator.build_data_row(125, reverend, ["0"] * 39)[24:28], ["0", "0", "0", "0"])
        monk = source_row(
            attack1_projectile="Spell", attack2_chance="0", spell1_chance="95", spell1="40,E,6,1 (Sparks)",
            spell2_chance="0", spell2="1,E,7,3 (Bless)",
        )
        self.assertEqual(generator.build_data_row(124, monk, ["0"] * 39)[24:28],
                         ["95", "Sparks,M,6", "100", "Bless,E,7"])

    def test_concat_spell_is_an_ordinary_spell_with_no_on_hit_rider(self) -> None:
        # The Basilisk: `concat` parses as SpellUse%1 0, the lone spell takes 100 - Att%; its Bonus is not read.
        basilisk = source_row(
            attack1_type="Elem", attack1_projectile="GreenYellowThingy", attack2_chance="50", attack2_dice="3",
            attack2_sides="6", bonus="Poison2", spell1_chance="concat", spell1="31,N,2,1 (Poison)",
        )
        row = generator.build_data_row(150, basilisk, ["0"] * 39)
        self.assertEqual(row[16], "0")
        self.assertEqual(row[24:28], ["50", "Poison Spray,N,2", "0", "0"])
        # A wolf's script never calls RangeAttack: no spell and no rider.
        wolf = source_row(attack1_type="Phys", attack1_projectile="0", attack2_dice="2", attack2_sides="6",
                          spell1_chance="concat", spell1="29,E,7,1 (Paralyze bite)")
        row = generator.build_data_row(116, wolf, ["0"] * 39)
        self.assertEqual(row[16], "0")
        self.assertEqual(row[24:28], ["0", "0", "0", "0"])
        # Att% 100 with attack 2 never casts (the Dripper).
        dripper = source_row(attack1_projectile="Goo2", attack2_chance="100", attack2_dice="2", attack2_sides="8",
                             spell1_chance="concat", spell1="8,E,5,1 (Disease)")
        self.assertEqual(generator.build_data_row(181, dripper, ["0"] * 39)[24:28], ["0", "0", "0", "0"])

    def test_lobber_pods_only_melee(self) -> None:
        # lobberpod.scr never enables its range attack: the pods' projectiles are never fired.
        pod = source_row(attack1_type="Phys", attack1_projectile="BlueThingy", attack2_chance="100",
                         attack2_projectile="BlueThingy")
        for source_number in (84, 85, 105):
            row = generator.build_data_row(source_number, pod, ["0"] * 39)
            self.assertEqual((row[19], row[23]), ("0", "0"), source_number)

    def test_bonus_column_gives_no_on_hit_special_attack(self) -> None:
        # MM9 loads the Bonus column and never reads it (MM9_AI_NATIVE_RE.md section 7.2.2): a blow is always physical.
        for bonus in ("Poison2", "BrkArmor", "Paralyze/Afraid", "Disease3", "Stealx2", "Uncon"):
            self.assertEqual(generator.build_data_row(1, source_row(bonus=bonus), ["0"] * 39)[16], "0", bonus)

    def test_skills_match_mm9_average_damage(self) -> None:
        cases = {
            "12,N,4,4 (Elemental Bolt)": ("RedThingy", "Fire Bolt,N,5"),
            "12,E,6,1(Elemental Bolt)": ("BlueThingy2", "Ice Bolt,E,8"),
            "4,G,15,15 (Column-of-Fire)": ("Spell", "Incinerate,G,8"),
            "47,M,8,1 (Wound)": ("Spell", "Harm,M,28"),
            "39,G,12,4, (Souldrinker)": ("Spell", "Dragon Breath,G,6"),
            "7,G,15,15": ("Spell", "Spirit Lash,G,11"),
            "40,N,4,1 (Sparks)": ("Spell", "Sparks,E,4"),
            "40,M,9,7 (Sparks)": ("Spell", "Sparks,G,9"),
            "40,G,9,7 (Sparks)": ("Spell", "Sparks,G,9"),
            "31,N,3,1 (Poison)": ("GreenThingy", "Poison Spray,N,4"),
            "27,M,10,2 (Natural Armor)": ("Spell", "Stone Skin,M,5"),
            "8,G,15,15": ("Spell", "Toxic Cloud,G,15"),
            "19,E,4,1 (fear)": ("Spell", "Fear,E,4"),
            "29,E,10,1 (Paralyze)": ("Spell", "Paralyze,E,10"),
            "5,M,8,5 (Curse)": ("Spell", "Dark Grasp,M,8"),
            "2,M,10,1 (Chain Lightning)": ("Spell", "Lightning Bolt,M,10"),
        }
        for cell, (projectile, expected) in cases.items():
            source = source_row(attack1_projectile=projectile, spell1_chance="100", spell1=cell)
            self.assertEqual(generator.build_data_row(1, source, ["0"] * 39)[25], expected, cell)

    def test_sorcerers_cast_fire_bolts_and_spells_mm9_never_casts_are_dropped(self) -> None:
        sorcerer = source_row(attack1_projectile="Spell", spell1_chance="100", spell1="12,E,8,1(Elemental Bolt)")
        self.assertEqual(generator.build_data_row(157, sorcerer, ["0"] * 39)[24:26], ["100", "Fire Bolt,E,14"])
        self.assertEqual(generator.build_data_row(160, sorcerer, ["0"] * 39)[25], "Lightning Bolt,E,6")

        icky = source_row(attack1_projectile="0", spell1_chance="100", spell1="31,N,1,1 (Poison)")
        self.assertEqual(generator.build_data_row(89, icky, ["0"] * 39)[24:28], ["0", "0", "0", "0"])
        # The Ghoul: its spell 1 Paralyze has SpellUse%1 0 (`concat`), so every cast is its spell 2 Disease.
        ghoul = source_row(
            attack1_projectile="Spell", attack2_chance="0", attack2_dice="2", attack2_sides="8",
            bonus="Paralyze/Afraid", spell1_chance="concat", spell1="29,E,5,1 (Paralyze)",
            spell2_chance="100", spell2="8,E,5,1 (Disease)",
        )
        row = generator.build_data_row(175, ghoul, ["0"] * 39)
        self.assertEqual(row[16], "0")
        self.assertEqual(row[24:28], ["0", "0", "100", "Toxic Cloud,E,1"])
        self.assertEqual(generator.spell_conditions(ghoul, 175), {})

    def test_debuff_casts_name_their_spell_conditions(self) -> None:
        lich_king = source_row(
            attack1_projectile="Spell", spell1_chance="50", spell1="6,M,10,1 (DarkGrasp)",
            spell2_chance="0", spell2="5,M,8,5 (Curse)",
        )
        self.assertEqual(generator.spell_conditions(lich_king, 209), {"spell1": "weak", "spell2": "cursed"})
        wolf = source_row(spell1_chance="concat", spell1="29,E,7,1 (Paralyze bite)")
        self.assertEqual(generator.spell_conditions(wolf, 116), {})

    def test_unknown_tokens_fail_loudly(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported projectile"):
            generator.build_data_row(
                1, source_row(attack1_projectile="UnmappedProjectile"), ["0"] * 39,
            )

    def test_flying_velocity_and_third_projectile_are_adapted(self) -> None:
        source = source_row(
            fly="1", walk_velocity="0", run_velocity="0", fly_velocity="250",
            attack3_projectile="DragonBreath2", attack3_type="Elem",
            attack3_damage="24D10+100",
        )
        row = generator.build_data_row(1, source, ["0"] * 39)

        self.assertEqual(row[13], "320")
        self.assertEqual(row[21:24], ["Fire", "24D10+100", "Fire"])


class Mm9MonsterFamilyTests(unittest.TestCase):
    def sources(self) -> dict[int, list[str]]:
        return {
            number: source_row(number=str(number), name=name)
            for number, name in ((75, "Dragonfly Mite"), (76, "Dragonfly"), (77, "Fire Dragonfly"),
                                 (100, "Burglar"), (212, "Dragon King"))
        }

    def families(self, document: str) -> generator.MonsterFamilies:
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "families.yml"
            path.write_text(document, encoding="utf-8")
            return generator.load_families(path, self.sources())

    def test_family_rows_get_tier_pictures_and_others_stay_unique(self) -> None:
        families = self.families(
            "families:\n  - {id: dragonfly, name: Dragonfly, tiers: [75, 76, 77]}\n"
            "mapstats_aliases:\n  Burgler: 100\n"
        )
        pictures = generator.picture_names(self.sources(), families)

        self.assertEqual(pictures[75], "MM9 Dragonfly A")
        self.assertEqual(pictures[77], "MM9 Dragonfly C")
        self.assertEqual(pictures[212], "MM9 212 Dragon King")
        row = generator.build_data_row(75, self.sources()[75], ["0"] * 39, pictures[75])
        self.assertEqual(row[1:3], ["Dragonfly Mite", "MM9 Dragonfly A"])

    def test_mapstats_names_resolve_to_families(self) -> None:
        families = self.families(
            "families:\n  - {id: dragonfly, name: Dragonfly, tiers: [75, 76, 77]}\n"
            "mapstats_aliases:\n  Burgler: 100\n"
        )
        sources = self.sources()

        self.assertEqual(generator.mapstats_family("DragonFlyMite", sources, families).picture_base, "MM9 Dragonfly")
        self.assertIsNone(generator.mapstats_family("Burgler", sources, families))
        self.assertIsNone(generator.mapstats_family("DragonKing", sources, families))
        with self.assertRaisesRegex(ValueError, "matches no"):
            generator.mapstats_family("Unknown", sources, families)

    def test_npc_actor_rows_join_the_sources_with_unique_pictures(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "MONSTERS.txt"
            header = ["h"] * generator.SOURCE_COLUMN_COUNT
            rows = [source_row(number="75", name="Dragonfly Mite"),
                    source_row(number="252", name="Forad Darre", is_monster="0"),
                    source_row(number="253", name="Other NPC", is_monster="0")]
            source.write_text("\n".join("\t".join(r) for r in [header] + rows) + "\n", encoding="cp1252")
            npc_path = Path(directory) / "npc.tsv"
            npc_path.write_text("mm9_source_number\tlegacy_actor_id\tnote\n252\t586\tForad\n", encoding="utf-8")
            npc = generator.npc_actor_ids(npc_path)
            sources = generator.source_monsters(source, frozenset(npc))

        self.assertEqual(npc, {252: 586})
        self.assertEqual(sorted(sources), [75, 252])
        families = self.families("families: []\n")
        self.assertEqual(generator.picture_names(sources, families)[252], "MM9 252 Forad Darre")

    def test_invalid_families_fail_loudly(self) -> None:
        with self.assertRaisesRegex(ValueError, "not an IsMonster row"):
            self.families("families:\n  - {id: x, name: X, tiers: [75, 999]}\n")
        with self.assertRaisesRegex(ValueError, "is in families"):
            self.families(
                "families:\n  - {id: x, name: X, tiers: [75, 76]}\n  - {id: y, name: Y, tiers: [76, 77]}\n"
            )



class Mm9MonsterBodyTests(unittest.TestCase):
    """MM9's own bodies (mm9_monster_bodies.py) replace the copied legacy sizes, also on regeneration."""

    def test_overrides_replace_copied_columns_and_empty_cells_keep(self) -> None:
        import tempfile
        rows = [["#", "InternalName", "Height", "Radius", "MovementSpeed", "ToHitRadius"],
                ["9237", "MM9 Terror A", "256", "160", "140", "160"],
                ["9054", "MM9 54 Shopkeeper", "110", "44", "1", "0"]]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bodies.tsv"
            path.write_text("# comment\nrow\tsource\tHeight\tRadius\tToHitRadius\n"
                            "9237\tTerror\t256\t64\t0\n9054\tShopkeeper\t174\t\t\n", encoding="utf-8")
            overrides = generator.read_body_overrides(path)
        generator.apply_body_overrides(rows, overrides)

        self.assertEqual(rows[1], ["9237", "MM9 Terror A", "256", "64", "140", "0"])
        self.assertEqual(rows[2], ["9054", "MM9 54 Shopkeeper", "174", "44", "1", "0"])
        with self.assertRaisesRegex(ValueError, "does not write"):
            generator.apply_body_overrides(rows, {9999: {3: "10"}})

    def test_mm9_rule_replaces_the_row_scale_with_a_dat_scale(self) -> None:
        import mm9_monster_bodies as bodies

        self.assertEqual(bodies.effective_scale(0.5, 1.0), 0.5)
        self.assertEqual(bodies.effective_scale(0.5, 1.2), 1.2)
        # Terror.abc static_model (25, 50, 25) LT at Scale 1; ColloidalWarrior.abc (35, 40, 35) at Scale 2
        self.assertEqual(bodies.native_body((25.0, 50.0, 25.0), 1.0), (256, 64))
        self.assertEqual(bodies.native_body((35.0, 40.0, 35.0), 2.0), (410, 179))
        # the wider horizontal half extent sizes the round body (cow.abc 15 x 35)
        self.assertEqual(bodies.native_body((15.0, 26.0, 35.0), 1.0), (133, 90))

    def test_generated_descriptors_carry_the_mm9_bodies(self) -> None:
        """A regeneration with the repository's inputs keeps MM9's sizes (no silent revert to the stand-ins)."""
        import tempfile
        root = Path(__file__).resolve().parents[2]
        source = root / "mm9/extracted/DATA/DATA/MONSTERS.txt"
        if not source.exists():
            self.skipTest("MM9 extracted data not present")
        here = Path(__file__).resolve().parent
        with tempfile.TemporaryDirectory() as directory:
            generator.generate_tables(
                source, here / "mm9_monster_legacy_replacements.tsv", here / "mm9_monster_families.yml",
                root / "assets_dev/engine/data_tables/monster_data.txt",
                root / "assets_dev/engine/data_tables/monster_descriptors.txt", Path(directory),
                here / "mm9_npc_actor_rows.tsv", here / "mm9_monster_body_overrides.tsv")
            text = (Path(directory) / "monster_descriptors.txt").read_text(encoding="utf-8")
        rows = {int(r[0]): r for r in (line.split("\t") for line in text.splitlines()) if r[0].isdigit()}

        self.assertEqual(rows[9237][2:6], ["256", "64", "140", "0"])   # Amphibious Terror
        self.assertEqual(rows[9212][2:4], ["1700", "512"])             # Dragon King
        self.assertEqual(rows[9173][2:4], ["256", "51"])               # Gezzampt Elder


if __name__ == "__main__":
    unittest.main()
