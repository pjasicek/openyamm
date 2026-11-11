# MM9 client effects (`DoClientFX`) in the rework (2026-11-06)

MM9 scripts play an effect of `CLIENTFX/SPELLS.fxf` on an object with `DoClientFX <object>, <name>[, loop, ?]`; the
names are `SPELLNAMES.inc` constants (`SPELL_BLUEFIRE` = "fireblue") or a script's own string (NPC378's `Ceffect` =
"spell-town portal"). Every FXF recipe the rework plays is an `mm9:*` world effect compiled from the FXF by
`tools/mm9_import_discovery/import_mm9_effect_assets.py` into `assets_dev/engine/effects/mm9/library.yml` (MM9's own
sprites, sounds and models; `capabilities.yml` says what each recipe needs). Effects are one-shot world effects: an
MM9 effect that follows its object or loops (`DoClientFX ..., TRUE`) plays once where the object stood.

How a port plays one:

- on a creature a map script spawns: `evt.SummonMonstersById{..., effect = "mm9:fireblue"}` (where each monster
  stands as it appears);
- on a map actor: `MM9.clientFx(actorIndex, effect[, scale[, up]])` (`mm9_common.lua`);
- carried on a map actor's socket (2026-11-10), following it: `MM9.actorFx(actorIndex, effect[, socket[, seconds[,
  scale]]])` over `evt.SpawnActorEffect` (socket: an actors.yml `animation.sockets` name or a model node such as
  `LHand1`; none: the middle of the body), ended early by `MM9.stopActorFx(actorIndex[, effect])`;
- on a marker or point: `evt.SpawnWorldEffect(effect, x, y, z[, scale])`;
- in a behaviour script: `self:effect(id, scale, heightFraction, forward)` or `self:effectAt(id, x, y, z, scale)`.

New recipes on 2026-11-06: `mm9:greenyeldots`, `mm9:bluedots`, `mm9:dragon_smoke`; on 2026-11-10 every recipe with
body-anchored emitters (`mm9:redyeldots`, `mm9:LichKingRes`, `mm9:skullcurse`). MM9 anchors these emitters to body
nodes (hands; the dragon's snout and the Lich King's nodes 8 and 9), which OpenYAMM effects do not have; the compiler
emits them at the effect's origin (`anchor_fallback: origin`, each component's node as `body_anchor` in the library) and
the caller places the origin (the shooter, the apprentice's chest, the dragon's `Socket_Mouth`, an actor's socket). A monster's own `DoFX` keys are actors.yml
animation events (`effect`/`effects` on sockets over a clip span), which follow the hand while the clip plays.

## Calls in scripts MM9 runs

58 calls in 28 scripts (users from the audit inventory: DAT objects, MONSTERS.txt, spawn strings). "new" was wired on
2026-11-06; "existing" was already carried.

| Script:line | Effect | On | When | Map | Rework |
| --- | --- | --- | --- | --- | --- |
| AK_IMPGATE.scr:208 | fireblue | the spawned Imp | each of a gate's 5 spawns | anskramkeep | new: `sendImp` summon `effect` |
| AK_GIANTIMP.scr:46 | blacksmoke | the Giant Imp | `appear` (:StartScene) | anskramkeep | new: `MM9.clientFx` as it is shown |
| ARG_YRSA.scr:35 | GreaterDemon | Yrsa | :Appear2, the windup before she shows | thronheimcity | new: council.py timer stage 1 |
| ARG_YRSA.scr:92 | GreaterDemon | Yrsa | :Vanish after her errand | thronheimcity | new: RUDE exit, before the removal |
| BC_MANAGER.scr:84, 90, 105 | mist | the spawned fighters, the monk | spawn | bootcamp | existing: `bcSpawn` -> `bcMist` |
| BC_MANAGER.scr:119, 126 | mist | the surviving fighter | the other died | bootcamp | existing: handler 612 |
| BC_TREASURECHEST.scr:64 | column of fire | the opener (monk) | the trap | bootcamp | existing |
| CHASM_GHOSTSPAWNER.scr:58 | fireblue | the spawned Apparition | each touched trigger | chasmofthedead | new: `spawnGhost` summon `effect` |
| CHESSBASE.inc:170 | fireblue | the queening square | PawnToQueen | 1000terrors | existing |
| COLLOIDALGENIE.scr:69 | blacksmoke | the Smoke marker | the lamp calls it | ruinedtemple | new: `genieFx` |
| COLLOIDALGENIE.scr:78 | mist | the Smoke marker | it appears | ruinedtemple | new |
| COLLOIDALGENIE.scr:131-132 | mist, blacksmoke | the Smoke marker | it goes | ruinedtemple | new |
| DRAGON.scr:1098 | dragon smoke | the dragon's snout | every 2.5 s from landing (DoBreathing) | dragonstadium | new: `dragon_king.lua` |
| EBORABATH.scr:163 | column of fire | Ebora | she leaves | bathhouse | existing: `ebora.lua`, cinematic |
| EBORAMINES.scr:71 | column of fire | Ebora | she leaves | thjoradmine | existing |
| ENDDEMON.scr:71 | GreaterDemon | the end demon | spawn-in | 1000terrors | existing: `evt.SpawnWorldEffect` |
| GREATERDEMON.scr:46 | GreaterDemon | a spawned Greater Demon | spawn-in (p0 1): a Lesser Demon's death | 1000terrors, bathhouse | new: kill-hook summon `effect` |
| ISLE_ISLANDEXPLOSION.scr:32-33, 50 | elemental blast, blacksmoke; mist | the explosion points | timed | isleofashes | existing |
| ISLE_SPAWNCREATURE.scr:42-43, 69 | elemental blast, column of fire; column | the Skeletoid | spawn; teleport | isleofashes | existing |
| NJAM1000.inc:44 | GreaterDemon | Njam | :Vanish | 1000terrors | fixed: `njam.lua` played town portal |
| NJAMFREEZE.scr:118 | Njam lightball for cutscene | Njam | the freeze cinematic | 1000terrors | existing |
| NJAMTAUNT.scr:68 | GreaterDemon | Njam | :OnVanish | 1000terrors | existing |
| NPC378.scr:177 | spell-town portal | Thorolf | :OnTeleport (teleports in mid-visit) | 6 cities | not carried: he stands from the map load |
| NPC378.scr:250 | spell-town portal | Thorolf | :Vanish after the message | 6 cities | new: RUDE exit, before the removal |
| RANDVERRUN.scr:81 | spell-town portal | Randver | :Vanish | sturmfordcity | new |
| SPAWNGENERIC.scr:53 | GreaterDemon | the spawn point | each spawn | 1000terrors | new: `SPAWNS` entries' `effect` |
| SPAWNNJAMCAMEO.scr:49, 84 | GreaterDemon | the marker; Njam | appear; vanish | darkpassageway | new |
| SPAWNNJAM.scr:68, 103 | GreaterDemon | the marker; Njam | appear; vanish | 1000terrors | new: `njamAppear` |
| SUMMONER.scr:68-69, 95-96 | sparklies, fireblue | the spawn locations | startup; a minion died | lichlab | new: `summoner.lua` `effectAt` |
| TELEPORTERSWITCH.scr:65 | spell reaver | the teleporter | SetDestination | wizardslab | existing |
| WIZARDEFFECT.scr:45 | sparklies | the apprentice | :PlayConjureEffect | wizardslab | existing |
| WIZARDEFFECT.scr:46 | greenyeldots | the shooter | :PlayConjureEffect | wizardslab | new: at `SHOOTER_AT` |
| WIZARDEFFECT.scr:56 | bugs | SummonLocation | :PlayShootEffect | wizardslab | existing |
| WIZARDMASTER.scr:124-127 | meteor, town portal, sparklies, column of fire | SummonLocation | :ConjureSpell | wizardslab | existing |
| WIZARDMASTER.scr:150-151 | elemental blast, paralyze | the demon | :Summon | wizardslab | existing |
| WIZARDMASTER.scr:186-187 | sparklies, fireblue | the master | :BeginBanish | wizardslab | new: after the summon |
| WIZARDMASTER.scr:204 | dark grasp | the demon | :BanishDemon | wizardslab | existing |
| WIZARDMASTER.scr:232-233 | spell reaver, elemental blast | the demon | :RemoveDemon | wizardslab | existing |
| WIZARDSUMMONER.scr:87 | bluedots | the apprentice | killed by the demon | wizardslab | new: damage hook, 110 above its feet |

Totals: 30 existing, 27 new, 1 not carried. Not reached: the engine's own Greater Demon death spawn
(`AI_Mm9DeathSpawn`) plays no effect; no map spawns a Lesser Demon with ScriptParams 1 through it today (the map
scripts' kill hooks summon the Greater Demon, with the effect).

Scripts no object runs (unreferenced.md): ILSFIREBOOK, IMPTRICKSTER, LICHEFFECTS, LICHESCORT, LICHSACRIFICE,
LICHSORCERER, LICHSORCERERNEW (transfusion, spirit, columns and the rest of the remaining calls).
