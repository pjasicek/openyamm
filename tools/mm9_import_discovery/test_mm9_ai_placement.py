#!/usr/bin/env python3
from __future__ import annotations

import unittest

from generate_mm9_monster_modifiers import classify, effective_script, placement_profile
from mm9_ai_placement import SCRIPT_DIRECTORY, placement_ai, script_chain

MARKERS = {f"flymarker{index}": [100.0 * index, 0.0, 0.0] for index in range(8)}
MARKERS.update({"path0": [0.0, 0.0, 10.0], "path1": [0.0, 0.0, 20.0], "spawnloc": [1.0, 2.0, 3.0]})


def native(position):
    return [position[0] * 2.56, position[2] * 2.56, position[1] * 2.56]


def properties(**changes):
    values = {"SightDistance": 600.0, "HearingDistance": 144.0, "RunawayChance": 0.25,
              "RangeAttackType": 1065353216, "CanBeResurrected": 0, "WanderON": 0, "WanderPathName": "",
              "WanderLeash": 0.0, "WanderWaitMin": 3.0, "WanderWaitMax": 10.0, "WanderTimeMin": 3.0,
              "WanderTimeMax": 6.0, "ScriptName": "", "ScriptParams": ""}
    values.update(changes)
    return values


@unittest.skipUnless(SCRIPT_DIRECTORY.is_dir(), "needs mm9/extracted")
class PlacementTest(unittest.TestCase):
    def test_settings_in_our_units(self):
        out = placement_ai(properties(RangeAttackType=1073741824, CanBeResurrected=1, RunawayChance=0.05),
                           MARKERS, native)
        self.assertEqual(out, {"sight": 1536, "hearing": 369, "runaway_chance": 0.05, "ranged_type": 2,
                               "can_be_resurrected": True})

    def test_named_hiding_places(self):
        out = placement_ai(properties(HidingPlace0="SpawnLoc", HidingPlace1="", HidingPlace2="Missing"), MARKERS,
                           native)
        self.assertEqual(out["hiding_places"], [[3, 8, 5]])
        self.assertNotIn("hiding_places", placement_ai(properties(), MARKERS, native))

    def test_wander_path_and_aimless_leash(self):
        path = placement_ai(properties(WanderON=1, WanderPathName="Path", WanderPathRandom=1), MARKERS, native)
        self.assertEqual(path["wander"], "path")
        self.assertEqual(path["path"], [[0, 26, 0], [0, 51, 0]])
        self.assertTrue(path["path_random"])
        self.assertEqual(path["wander_wait"], [3.0, 10.0])
        aimless = placement_ai(properties(WanderON=1, WanderLeash=500.0), MARKERS, native)
        self.assertEqual((aimless["wander"], aimless["wander_leash"]), ("aimless", 1280))

    def test_wander_path_stops(self):
        # BaseWander.inc OnWanderAtMarkerNext: a marker's facing, own wait and clip; plain markers give no stop.
        marker_properties = {
            "path0": {"UseMarkerRotation": 1, "Rotation": [0.0, 30.0, 0.0, 0.0], "UseMarkerWaitTime": 1,
                      "WanderWaitMin": 0.0, "WanderWaitMax": 4.0, "AnimationName": "fidget2", "LoopAnim": 1},
            "path1": {"UseMarkerRotation": 0, "AnimationName": "hAttack2"},
        }
        out = placement_ai(properties(WanderON=1, WanderPathName="Path"), MARKERS, native,
                           marker_properties=marker_properties, facing=lambda rotation: 90.0 - rotation[1])
        self.assertEqual(out["path_stops"], [{"point": 0, "face": 60.0, "wait": [0.01, 4.0], "clip": "fidget2",
                                              "loop": True}, {"point": 1, "clip": "attack2"}])
        # Without marker data (an old caller) or without stops: none.
        self.assertNotIn("path_stops", placement_ai(properties(WanderON=1, WanderPathName="Path"), MARKERS, native))
        self.assertNotIn("path_stops", placement_ai(properties(WanderON=1, WanderPathName="Path"), MARKERS, native,
                                                    marker_properties={}, facing=lambda rotation: 0.0))

    def test_animal_wanders(self):
        # cat.scr and dog.scr force BaseWander on (BaseWanderForceStartUp), with the placement's settings (a 0 as
        # 0.01 s); wander.inc (pig, hen, rooster) always roams within p0 or 350 LT; FarmAnimal.inc (cow, goat) wanders
        # only with WanderON, at FarmAnimalInit's 10-20 s waits.
        cat = placement_ai(properties(WanderWaitMin=0.0, WanderWaitMax=0.0), MARKERS, native, row=294)
        self.assertEqual((cat["wander"], cat["wander_wait"], cat["wander_time"]), ("aimless", [0.01, 0.01], [3.0, 6.0]))
        pig = placement_ai(properties(), MARKERS, native, row=271)
        self.assertEqual((pig["wander"], pig["wander_leash"], pig["wander_wait"], pig["wander_time"]),
                         ("aimless", 896, [5.0, 5.0], [5.0, 10.0]))
        hen = placement_ai(properties(ScriptParams="200"), MARKERS, native, row=269)
        self.assertEqual(hen["wander_leash"], 512)
        self.assertNotIn("wander", placement_ai(properties(), MARKERS, native, row=267))
        cow = placement_ai(properties(WanderON=1), MARKERS, native, row=267)
        self.assertEqual((cow["wander"], cow["wander_wait"]), ("aimless", [10.0, 20.0]))

    def test_marker_clip_roles(self):
        from mm9_ai_placement import marker_clip_role
        self.assertEqual(marker_clip_role("Fidget1"), "fidget")
        self.assertEqual(marker_clip_role("fidget5"), "fidget5")
        self.assertEqual(marker_clip_role("hAttack2"), "attack2")
        self.assertEqual(marker_clip_role("hAttack1"), "attack_melee")
        self.assertEqual(marker_clip_role("Taunt"), "taunt")

    def test_script_patterns(self):
        hanging = placement_ai(properties(ScriptName="scripts\\LL_FlyingCreature.scr",
                                          ScriptParams="FlyMarker 2 4"), MARKERS, native)
        self.assertEqual(hanging["dormant"], {"until": "trigger", "pose": "hang"})
        self.assertEqual(len(hanging["path"]), 3)
        self.assertEqual(hanging["script"], "ll_flyingcreature.scr")
        self.assertEqual(hanging["script_params"], "FlyMarker 2 4")
        mummy = placement_ai(properties(ScriptName="MummyAwaken.scr", ScriptParams="1 PetrifiedMummy32"), MARKERS,
                             native)
        self.assertEqual(mummy["dormant"], {"until": "trigger", "pose": "coffin"})
        monk = placement_ai(properties(ScriptName="MonkGuardBasic.scr", ScriptParams="-1 424"), MARKERS, native)
        self.assertEqual((monk["hostility"], monk["faction"]), ("friendly_until_provoked", "monk"))
        dook = placement_ai(properties(ScriptName="DookGuardBasic.scr"), MARKERS, native)
        self.assertEqual((dook["hostility"], dook["faction"]), ("hostile_after_event", "dook"))
        summoner = placement_ai(properties(ScriptName="ISLE_Summoner.scr", ScriptParams="Skeletoid SpawnLoc"),
                                MARKERS, native)
        self.assertEqual(summoner["summon"], {"class": "Skeletoid", "points": [[3, 8, 5]]})
        self.assertTrue(placement_ai(properties(ScriptName="GreenParty.scr"), MARKERS, native)["starts_dead"])
        self.assertTrue(placement_ai(properties(ScriptName="NjamChase.scr"), MARKERS, native)["boss"])


@unittest.skipUnless(SCRIPT_DIRECTORY.is_dir(), "needs mm9/extracted")
class ArchetypeTest(unittest.TestCase):
    def archetype(self, row: int, script: str) -> tuple[str, str, str]:
        return classify(row, script.lower(), script_chain(script))

    def test_known_rows(self):
        self.assertEqual(self.archetype(183, "basemelee.scr"), ("skirmisher", "walk", "none"))       # Skeletoid
        self.assertEqual(self.archetype(157, "EvilSorcerer.scr"), ("ranged_holder", "walk", "walker"))
        # WizardSummoner.scr sets Range type 2 itself after the ritual (LinkToBaseRange): a holder, not BaseMelee's
        # skirmisher.
        self.assertEqual(self.archetype(156, "WizardSummoner.scr"), ("ranged_holder", "walk", "walker"))
        self.assertEqual(self.archetype(168, "BaseSwim.scr"), ("swimmer", "swim", "none"))           # Jellyspore
        self.assertEqual(self.archetype(86, "lobber.scr"), ("turret", "walk", "none"))
        self.assertEqual(self.archetype(1, "NPCbase.scr"), ("civilian", "walk", "none"))             # Commoner
        self.assertEqual(self.archetype(107, "policeman.scr"), ("guard", "walk", "none"))
        self.assertEqual(self.archetype(76, "flyrange.scr"), ("flier", "fly", "flier"))              # Dragonfly
        self.assertEqual(self.archetype(228, "baserange.scr"), ("skirmisher", "fly", "walker"))      # Eye
        self.assertEqual(self.archetype(84, "lobberpod.scr"), ("crawler", "walk", "none"))
        self.assertEqual(self.archetype(212, "dragon.scr"), ("turret", "walk", "none"))              # Dragon King


@unittest.skipUnless(SCRIPT_DIRECTORY.is_dir(), "needs mm9/extracted")
class PlacementScriptTest(unittest.TestCase):
    """The placement's ScriptName wins over its row's (MM9_MONSTER_AI_PLAN.md "Which ScriptName wins")."""

    def effective(self, script: str, row_script: str):
        return effective_script(script, row_script, {}, SCRIPT_DIRECTORY)

    def test_effective_script(self):
        # A fight loop of its own (KingKong.scr calls BaseInit when it breaks out).
        self.assertEqual(self.effective("kingkong.scr", "baserange.scr"), ("kingkong.scr", False))
        # GuardRude.scr reaches BaseInit by `Goto` on its alarm.
        self.assertEqual(self.effective("guardrude.scr", "guardbase.scr"), ("guardrude.scr", False))
        # Hand-overs: the row's own script (the ScriptName stat), or a named one.
        self.assertEqual(self.effective("autoresurrect.scr", "baserange.scr"), ("baserange.scr", False))
        self.assertEqual(self.effective("jumper.scr", "baserange.scr"), ("baserange.scr", False))
        self.assertEqual(self.effective("coffinmummy.scr", "baserange.scr"), ("basemelee.scr", False))
        self.assertEqual(self.effective("wizardmaster.scr", "evilsorcerer.scr"), ("evilsorcerer.scr", False))
        # BaseMelee.inc brought only as a library, with a wander loop of its own: a civilian.
        self.assertEqual(self.effective("npc8.scr", "npcbase.scr"), ("npc8.scr", True))
        # No AI at all: a dialogue script and a set-piece flier.
        self.assertIsNone(self.effective("sturmguard.scr", "policeman.scr"))
        self.assertIsNone(self.effective("ll_flyingcreature.scr", "flyingicky.scr"))

    def test_profile_overrides(self):
        # Placed Ghasts and Revenants (rows 174, 176: baserange.scr) run KingKong.scr: BaseMelee without Range.inc.
        self.assertEqual(placement_profile(174, "kingkong.scr"), {"ranged": "none"})
        self.assertEqual(placement_profile(176, "kingkong.scr"), {"ranged": "none"})
        # The row's own loop, directly or by a hand-over: nothing to override.
        self.assertEqual(placement_profile(174, "baserange.scr"), {})
        self.assertEqual(placement_profile(181, "autoresurrect.scr"), {})
        self.assertEqual(placement_profile(174, ""), {})
        # The Wizard's Lab apprentices (row 156, EvilSorcerer.scr) run WizardSummoner.scr: the row's holder.
        self.assertEqual(placement_profile(156, "wizardsummoner.scr"), {})
        # Sturmford's prison guard (row 110, policeman.scr) runs Sturmguard.scr: no AI.
        self.assertEqual(placement_profile(110, "sturmguard.scr"), {"passive": True})
        # A boss placement keeps its Lua behaviour in place of its script.
        self.assertEqual(placement_profile(261, "njamtaunt.scr", boss=True), {})
        # Monks gain Range.inc from MonkGuardBasic.scr; Embalmed Mummies (BaseCrawl) gain BaseMelee's footwork.
        self.assertEqual(placement_profile(123, "monkguardbasic.scr"), {"ranged": "walker"})
        mummy = placement_profile(145, "mummyawaken.scr")
        self.assertEqual(mummy["archetype"], "skirmisher")
        self.assertEqual(set(mummy["skirmisher"]), {"strafe_attack_chance", "evade_chance", "taunt_seconds"})
        # A Honk (baserange.scr) on Honkies.scr only wanders: a civilian without the footwork.
        self.assertEqual(placement_profile(216, "honkies.scr"),
                         {"archetype": "civilian", "ranged": "none", "skirmisher": False})

    def test_passive_script_without_wander_stands(self):
        # Thjorgard's Magreeb (row 277, WanderON) runs ScholarPromo.scr, which never starts BaseWander: it stands.
        placed = properties(ScriptName="ScholarPromo.scr", WanderON=1)
        self.assertNotIn("wander", placement_ai(placed, MARKERS, native, row=277))
        self.assertEqual(placement_ai(placed, MARKERS, native, row=277)["profile"], {"passive": True})
        # Without its row (no profile known) and on a script that starts BaseWander, WanderON still wanders.
        self.assertEqual(placement_ai(placed, MARKERS, native)["wander"], "aimless")
        shopkeeper = properties(ScriptName="Shopkeeper.scr", WanderON=1)
        self.assertEqual(placement_ai(shopkeeper, MARKERS, native, row=1)["wander"], "aimless")

    def test_placement_writes_its_profile(self):
        out = placement_ai(properties(ScriptName="KINGKONG.scr", ScriptParams="Cage0"), MARKERS, native, row=174)
        self.assertEqual(out["profile"], {"ranged": "none"})
        self.assertEqual(out["script"], "kingkong.scr")
        self.assertNotIn("profile", placement_ai(properties(ScriptName="KINGKONG.scr"), MARKERS, native))
        self.assertNotIn("profile", placement_ai(properties(), MARKERS, native, row=174))


if __name__ == "__main__":
    unittest.main()
