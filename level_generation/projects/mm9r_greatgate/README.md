# Great Gate (MM9 `GREATGATE.dat`): not converted

Outcome of the overnight dungeon run, 2026-10-31: **not a dungeon, not converted.** `GREATGATE.dat` is a small
open-air cutscene set (a standalone copy of the Great Gate scene that MM9 actually plays inside Arslegard City). No
world, script, RUDE row or game binary sends the party to it, it has no exits, and it is not an enclosed map, so it
does not fit the BLV dungeon route of `../mm9r_common/DUNGEON_PLAYBOOK.md`. Nothing was installed in the review root.

## What the DAT contains

- **Geometry** (`PhysicsBSP`, 1 084 polys, extents 2 304 × 2 048 × 4 800 MM9 units, about 5.9k × 5.2k × 12.3k
  OpenYAMM units): a winding paved path (`sturmsidewalk`, 763 polys) to a short bridge, a gatehouse with two towers,
  a wide stair (`stone_bricks_t`, `Trimgarg`, `woodgrain01`) up to the great gate wall, and pools of `underwater_tile`
  either side. It sits inside a 6-face `SkyMarker` box, with `SkyBox0` (SnowMtns faces) and a `TOD_Sky0` star field:
  an exterior stage open to the sky, not a room. Layout sketch (top and side, red dots are objects):
  `work/greatgate_layout.png`.
- **Lighting:** no Light objects. One `StaticSunLight` (white, BrightScale 1), `AmbientLight 50 50 50`,
  `PlayerLightOn 1`; one lightmap frame on all 1 090 polys.
- **Door0:** a 16 × 4 × 4 unit wooden shutter at (24, 386, 1270), the peephole in the gate that Hanndl opens
  (`draweropenwood.wav`). The inventory's "1 door".
- **Hanndl** (`models\Hanndl.abc`, `Hanndl.scr`) behind the peephole: the inventory's "1 NPC". Not a talking NPC
  here; his script only plays cinema animations and voice lines (`Sc3_hanndl07/08`, `Sc4_hanndl09`–`15`,
  `sc5_Hanndl16/17`).
- **Cameras:** `Losecam1`–`Losecam4` (`LoseCam1.scr`, `LoseCam2.scr`) and `CameraMarker0`–`2`: scripted camera dollies
  with letterbox and fades.
- **The two script objects** (inventory's "2"): `Loseman` (`LOSEMAN.scr`) and `Fateman` (`FATEMAN.scr`).
- `StartPoint0` on the bridge end, no `ExitTrigger`, no monsters, chests, props or items
  (`devdocs/mm9/MM9_PICKABLE_ITEM_CLASSIFICATION.md`, Great Gate).

## How MM9 uses it

The scripts all say "handles losegame cutscene" (Timmy, 12/20). Both managers wait for a `Lose` trigger
(`Addtrigger Lose, OnLose`); no `.scr` sends it, so the engine does on arrival after the party is killed.
`cshell.dll` holds `worlds\ArslegardCity` (the death destination) and `object.lto` holds `movies\LoseGame.bik`;
nothing anywhere names `GreatGate`, and `tools/mm9_import_discovery/promote_mm9_map_images.py` already skips it.

- `LOSEMAN.scr`: fade out, camera flies along the path (`Losecam1` → `CameraMarker0`), then over the bridge
  (`Losecam2` → `CameraMarker2`), cut to `Losecam3` at the gate; the peephole opens, Hanndl turns the party away
  (Hanndl07/08, `voices\cinema\Losegame`), the peephole closes, fade back to play.
- `FATEMAN.scr` (once, gives key 98): the same flight from the other side (`Losecam4`), then Hanndl and the party
  argue in six exchanges (Hanndl09–15, party lines picked by `getPCVoice` from 16 voice sets): "You again!",
  "dead soldiers", "Destiny?", "If I am to let you in ... Writ of Fate ... Wyrdes", "Dark Passageway ... transport
  you to the entrance". Then `GiveExp 46000`, `quest.wav`, and `trigger ExitTrigger2`, which moves the party to the
  Dark Passageway. **`ExitTrigger2` does not exist in `GREATGATE.dat`**; it exists in Arslegard City at
  (7256, 798.6, -5760). Key 98 is also what `CAPSTONE.scr` and `PLACECAPSTONE.scr` test (Writ of Fate chain).
- Arslegard City (`ARSLEGARDCITY.dat`) carries the full, final version of this scene at about (5632, -6500): the same
  `Hanndl`, `Door0`, `Losecam1`–`5`, `CameraMarker0`–`3`, `Loseman`, `Fateman`, `Fateman0`, plus `WritMan.scr`
  (presenting the Writ: keys 100/9515, Hanndl16/17, `GiveExp 170000`, Hanndl removed, `RotatingDoor0/1` unlocked and
  opened) and the talking Hanndl NPC (`Hanndl1`, `NPC334.scr`). Journal chapter III ("When they reached the Great
  Gate, Hanndl the Gatekeeper refused to let them in without ... a Writ of Fate") and RUDE NPC997 rows 254/256 ("show
  it to Hanndl at the Great Gate in Arslegard") describe that Arslegard scene.

So `GREATGATE.dat` is a development stage for the lose-game / Writ of Fate cutscene (it lacks WritMan and the exit
its own script fires), superseded by the Arslegard City copy. The shipped game never loads it.

## Scripted objects

| Object | Script | Native event | Reason |
| --- | --- | --- | --- |
| Loseman | `LOSEMAN.scr` | unmatched | cinema only; belongs to Arslegard City's death flow |
| Fateman | `FATEMAN.scr` | unmatched | cinema; its exit target `ExitTrigger2` is in Arslegard City |
| Hanndl | `HANNDL.scr` | unmatched | animation/voice player driven by the two managers |
| Losecam1–4 | `LOSECAM1.scr`, `LOSECAM2.scr` | unmatched | camera dollies; OpenYAMM has no cinema camera system |

## What a native version would need

None is recommended as a separate map: the scene's home is Arslegard City, an exterior map outside the BLV route.
Whoever converts Arslegard City should carry this scene there, as the Hall of the Gods carried its end-game cinema
(outcome as events, no camera system):

1. **Outcome first:** on party death, the Arslegard City arrival (the `Lose` hook) shows Hanndl refusing entry as a
   message or dialogue (Hanndl07/08 text), with the death/resurrection rules OpenYAMM already uses. With the Writ
   chain's key 98 not yet set, the Fateman outcome: the Hanndl09–15 lines as dialogue, 46 000 experience, key 98,
   then a move to the Dark Passageway start (the `ExitTrigger2` row in the transitions table). With keys 100 set and
   9515 not set, the WritMan outcome: 170 000 experience, Hanndl gone, the gate doors (`RotatingDoor0/1`) unlocked
   and opened.
2. **Full cinema (optional, engine work):** a camera-path player for `Camera`/`CameraMarker` objects (`MoveToPos`
   at a speed, `Target`, letterbox, `ScreenFadeIn/Out`), Hanndl's cinema clips on his 3D model, the peephole mover,
   and the party voice lines by PC voice set (`getPCVoice`). That is shared engine work and was not started.
3. If a standalone set were ever wanted (for example as a backdrop for that cinema), it would be an outdoor-style
   stage: sky box (SnowMtns), sun-lit lightmaps (`AmbientLight 50`, one white sun), the path, bridge, gatehouse and
   gate wall, about 1 100 polys. It would go through the exterior route, not `DUNGEON_PLAYBOOK.md`.

## Not checked

- No game run, no reference capture of the old ODM import (`assets_dev/worlds/mm9/maps/greatgate.*`, untouched).
- Which engine call fires `Lose` in MM9 (not found as a string in `mm9.exe`, `cshell.dll` or `object.lto`); the
  death destination `worlds\ArslegardCity` was found in `cshell.dll`.
- Whether Arslegard City's current import already plays any part of this scene.
