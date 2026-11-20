#!/usr/bin/env python3
from __future__ import annotations

import csv
import sys
import unittest
from pathlib import Path

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_mm9_monster_sounds as sounds
import generate_mm9_monster_tables as tables


ROOT = Path(__file__).resolve().parents[2]


def row(**values: object) -> sounds.SoundRow:
    defaults: dict = {"source_number": 155, "name": "Count", "descriptor": "MM9 Nobleman C", "model": "nobleman.abc",
                      "base_name": "nobleman", "foot_sound": "dirt", "foot_radius": 350.0, "voice_radius": 1440.0,
                      "script": "basemelee.scr"}
    defaults.update(values)
    return sounds.SoundRow(**defaults)


def quaternion_about_z(angle: float) -> np.ndarray:
    return np.array([0.0, 0.0, np.sin(angle / 2.0), np.cos(angle / 2.0)])


def tracks(angles: list[float], seconds: float, bones: list[str], basis: np.ndarray | None = None) -> dict:
    times = np.linspace(0.0, seconds, len(angles))
    result = {}
    for index, bone in enumerate(bones):
        rotations = np.array([quaternion_about_z(angle * (index + 1)) for angle in angles])
        if basis is not None:   # a constant change of the bone's rest frame: q * basis
            x1, y1, z1, w1 = rotations.T
            x2, y2, z2, w2 = basis
            rotations = np.stack([w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
                                  w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2], 1)
        result[bone] = (times, rotations)
    return result


class Mm9MonsterSoundTests(unittest.TestCase):
    def test_key_strings_split_into_commands(self) -> None:
        self.assertEqual(sounds.key_commands("Velocity  2 0 -2; playanimsound"), ["velocity", "playanimsound"])
        self.assertEqual(sounds.key_commands("deaddims 0 0 0; PlayDeathSound"), ["deaddims", "playdeathsound"])

    def test_keys_resolve_to_the_rows_folder_and_the_animations_name(self) -> None:
        animation = sounds.SourceAnimation("hattack1", 1.2, [(0.0, "lunge"), (0.333, "speakanimsound"),
                                                             (0.366, "playsoundfx"), (0.6, "footstep")], {})
        available = {"animsounds/nobleman/hattack1", "animsounds/nobleman/fx_hattack1"}
        events = sounds.animation_events(animation, row(), available, 2.4, ("animsounds/footsteps/dirt1",))
        self.assertEqual([(e.at, e.kind, e.sounds) for e in events], [
            (0.666, "speak", ("animsounds/nobleman/hattack1",)),
            (0.732, "fx", ("animsounds/nobleman/fx_hattack1",)),
            (1.2, "footstep", ()),
        ])
        # A key whose file MM9 does not ship stays silent and is reported.
        died = sounds.SourceAnimation("die1", 1.0, [(0.1, "playanimsound"), (0.7, "playdeathsound")], {})
        events = sounds.animation_events(died, row(), {"deathsounds/nobleman/die1"}, 1.0, ())
        self.assertEqual([(e.kind, e.sounds, e.missing) for e in events], [
            ("play", (), "animsounds/nobleman/die1"), ("death", ("deathsounds/nobleman/die1",), "")])

    def test_guard_script_keys_play_its_idle_chatter(self) -> None:
        stand = sounds.SourceAnimation("stand", 1.7, [(0.206, "stand")], {})
        available = {f"animsounds/guard/stand{n}" for n in range(1, 8)}
        guard = row(base_name="guard", script="guardbase.scr")
        events = sounds.animation_events(stand, guard, available, 1.7, ())
        self.assertEqual(len(events), 1)
        self.assertEqual(len(events[0].sounds), 7)
        self.assertAlmostEqual(events[0].script.chance, 0.35)
        self.assertEqual(events[0].script.miss_gate, 50.0)
        self.assertEqual(sounds.animation_events(stand, row(base_name="guard"), available, 1.7, ()), [])

    def test_monk_pray_key_plays_its_prayers(self) -> None:
        # MONK.abc keys its pray animation PrayMumble (MonkSounds.inc MS_Init: AddModelKey PrayMumble OnPray).
        pray = sounds.SourceAnimation("pray", 3.0, [(1.0, "praymumble")], {})
        available = {f"animsounds/monk/pray{n}" for n in range(1, 5)}
        monk = row(base_name="monk", script="monkguardbasic.scr")
        events = sounds.animation_events(pray, monk, available, 3.0, ())
        self.assertEqual(len(events), 1)
        self.assertEqual(len(events[0].sounds), 4)
        self.assertAlmostEqual(events[0].script.chance, 0.4)
        self.assertEqual(events[0].script.miss_gate, 20.0)

    def test_clips_match_their_animation_by_pose_signature(self) -> None:
        bones = ["Bip01 Spine", "Bip01 Head", "Bip01 L Arm", "Bip01 R Arm"]
        swing = [0.0, 0.4, 0.9, 0.3, 0.0]
        wave = [0.0, -0.3, 0.2, 0.5, 0.1]
        animations = [
            sounds.SourceAnimation("hattack1", 1.2, [], sounds.bone_signatures(1.2, tracks(swing, 1.2, bones))),
            sounds.SourceAnimation("taunt", 1.2, [], sounds.bone_signatures(1.2, tracks(wave, 1.2, bones))),
            sounds.SourceAnimation("stand", 1.0, [], sounds.bone_signatures(1.0, tracks([0.0] * 5, 1.0, bones))),
        ]
        # Our clips: MM9's skeleton renamed and its rest frames changed, the attack replayed at half speed.
        ours = ["vampiresB Spine", "vampiresB Head", "vampiresB L Arm", "vampiresB R Arm"]
        basis = quaternion_about_z(0.7) + np.array([0.2, 0.0, 0.0, 0.0])
        basis /= np.linalg.norm(basis)
        clips = {
            "AttackMelee": (2.4, sounds.bone_signatures(2.4, tracks(swing, 2.4, ours, basis)), {}),
            "Taunt": (1.2, sounds.bone_signatures(1.2, tracks(wave, 1.2, ours)), {}),
            "Dead": (1.0, sounds.bone_signatures(1.0, tracks([0.0] * 5, 1.0, ours)), {}),
        }
        sources = sounds.clip_sources(clips, animations)
        self.assertEqual(sources["AttackMelee"].name, "hattack1")
        self.assertEqual(sources["Taunt"].name, "taunt")
        self.assertNotIn("Dead", sources)   # a static pose matches by name only

    def test_sound_slots_replace_the_legacy_descriptor_sounds(self) -> None:
        descriptor = ["9155", "MM9 Nobleman C", "184", "38", "140", "0", "0x00e7e7e7", "2900", "2901", "2902", "2903"]
        tables.apply_sound_slots([descriptor], {155: {7: "50569", 8: "50565", 9: "50573", 10: "0"}}, [155])
        self.assertEqual(descriptor[7:11], ["50569", "50565", "50573", "0"])
        with self.assertRaises(ValueError):
            tables.apply_sound_slots([descriptor], {}, [155])

    def test_installed_tables_bind_the_count_to_mm9s_nobleman(self) -> None:
        """Kluso (the Count, row 155) plays MM9's Nobleman files, not MM6-MM8's 112noblemana set."""
        slots_path = Path(__file__).resolve().parent / "mm9_monster_sound_slots.tsv"
        actor_sounds = ROOT / "assets_dev/worlds/mm9/models/actor_sounds.yml"
        sound_table = ROOT / "assets_dev/worlds/mm9/data_tables/sounds.txt"
        if not (slots_path.exists() and actor_sounds.exists() and sound_table.exists()):
            self.skipTest("generated MM9 sound tables not present")
        with slots_path.open(newline="", encoding="utf-8") as handle:
            slots = {int(r["mm9_source_number"]): r for r in csv.DictReader(handle, delimiter="\t")}
        self.assertEqual(slots[155]["attack_sound"], "animsounds/nobleman/hattack1")
        self.assertEqual(slots[155]["death_sound"], "animsounds/nobleman/die1")
        self.assertEqual(slots[155]["wince_sound"], "animsounds/nobleman/wince1")
        ids = {}
        for line in sound_table.read_text(encoding="utf-8").splitlines():
            if line and not line.startswith("/"):
                name, sound_id = line.split("\t")[:2]
                ids[name] = int(sound_id)
        self.assertTrue(all(sounds.SOUND_ID_BEGIN <= value <= sounds.SOUND_ID_END for value in ids.values()))
        self.assertEqual(int(slots[155]["attack_sound_id"]), ids["animsounds/nobleman/hattack1"])
        entries = {e["descriptor"]: e for e in yaml.safe_load(actor_sounds.read_text(encoding="utf-8"))["actors"]}
        attack = entries["MM9 Nobleman C"]["clips"]["AttackMelee"]
        self.assertIn({"at": 0.333, "sound": "animsounds/nobleman/hattack1", "voice": True}, attack)
        self.assertIn({"at": 0.366, "sound": "animsounds/nobleman/fx_hattack1"}, attack)
        self.assertEqual(entries["MM9 Nobleman C"]["footsteps"][0], "animsounds/footsteps/dirt1")


if __name__ == "__main__":
    unittest.main()
