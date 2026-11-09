#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from import_mm9_world_audio import import_audio, selected_audio_imports


class Mm9WorldAudioImportTests(unittest.TestCase):
    def test_selects_every_sound_and_npc_voices_but_not_pc_voices_or_engine_root_sounds(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sounds = root / "SOUNDS"
            voices = root / "VOICES"
            engine_audio = root / "engine_audio"
            output = root / "output"
            fixtures = {
                sounds / "AMBIENT" / "Bird.wav": b"ambient",
                sounds / "DOOR" / "Open.wav": b"door",
                sounds / "EVENTS" / "QUEST.wav": b"quest",
                sounds / "PICKUPITEMS" / "Gold.wav": b"pickup",
                sounds / "WEAPONS" / "Bow.wav": b"weapon",
                sounds / "DEFAULT.wav": b"default",
                sounds / "ANIMSOUNDS" / "TROGLODYTE" / "Attack.wav": b"monster",
                sounds / "DEATHSOUNDS" / "Death.wav": b"monster-death",
                sounds / "MAGIC" / "Cast.wav": b"magic",
                sounds / "PLAYER" / "Step.wav": b"player",
                sounds / "SPELLS" / "Fire.wav": b"spell",
                sounds / "SPELLS" / "leggibLoop.wav": b"ambient-spell",
                sounds / "MAGIC" / "WizardEyeLoop.wav": b"ambient-magic",
                sounds / "ANIMSOUNDS" / "Zombie" / "Fidget1.wav": b"ambient-fidget",
                voices / "NPC" / "NPC_249.wav": b"npc",
                voices / "CINEMA" / "THEARGUMENT" / "01.WAV": b"cinema",
                voices / "PC" / "Hero.wav": b"pc",
                engine_audio / "DEFAULT.wav": b"engine-default",
            }
            for path, content in fixtures.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)

            imports = selected_audio_imports(sounds, voices, engine_audio)
            relative_paths = {entry.destination_relative.as_posix() for entry in imports}
            self.assertEqual(relative_paths, {
                "ambient/bird.wav",
                "animsounds/troglodyte/attack.wav",
                "animsounds/zombie/fidget1.wav",
                "deathsounds/death.wav",
                "door/open.wav",
                "magic/cast.wav",
                "magic/wizardeyeloop.wav",
                "pickupitems/gold.wav",
                "player/step.wav",
                "spells/fire.wav",
                "spells/leggibloop.wav",
                "voices/cinema/theargument/01.wav",
                "voices/npc/npc_249.wav",
                "weapons/bow.wav",
            })

            copied, unchanged = import_audio(imports, output, check=False)
            self.assertEqual(copied, 14)
            self.assertEqual(unchanged, 0)
            self.assertEqual((output / "voices/npc/npc_249.wav").read_bytes(), b"npc")
            self.assertEqual((output / "spells/fire.wav").read_bytes(), b"spell")
            self.assertFalse((output / "voices/pc/hero.wav").exists())


if __name__ == "__main__":
    unittest.main()
