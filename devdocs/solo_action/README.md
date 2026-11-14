# Solo action mode: research and prototype

A possible mode (a ruleset option, not decided) in which the player controls one character in first person: a held
weapon and shield on screen, swings that land when the blade does, an action bar of spells, buffs and special skills,
and a character made as strong as possible. Started 2026-11-13.

## Direction (user, 2026-11-13)

Experimental and parallel to the normal game. "Solo" is chosen at new game. It makes a party of one and turns on the
first-person presentation (arms, weapons, the solo HUD and action bar). Under MAW it also turns on the talents; under
Standard there are none. The mechanics stay those of the ruleset for a party of one: the same attacks, to-hit, damage
and recovery. The presentation only moves the moment a blow (or a spell) lands to its animation's Hit key inside the
recovery, which counts from the press, so the rate of attacks is unchanged. Rules for keeping it parallel:

- **Presentation, not rules.** The view model and the solo HUD read game state and never change it. The only
  gameplay hook is the deferred blow (`ViewModelLink`), plus the talents (MAW, solo only).
- **Casts work like swings:** on the press, the SP and the recovery are spent as today, a cast clip fitted to the
  recovery plays, and the spell leaves the hand at the clip's release key. Not built yet.
- **The one real difference** is the delay inside the recovery (about 0.1–0.4 s). The blow takes the target in reach
  at the blow, so a monster that steps away in that time is missed. Locking the target at the press is the
  alternative.
- **Turn-based combat** keeps the immediate blow, as now.
- **Built (2026-11-13):** the solo run is chosen at new game ("Solo run" on the party roster, or `--ruleset maw:solo`),
  saved, and gates the arms, the solo HUD and the action bar; see [HUD.md](HUD.md) "What is built". The talents read
  `GameplayScreenRuntime::soloRun()` and fill `ActionBarSlotKind::Talent` slots.
- **The party stays one (user, 2026-11-14).** `Party::setSoloRun` (set by the session from the options, not saved)
  makes the party full at one member: a companion's join is refused and stays where it is, and the Adventurer's Inn
  has no Hire. MM9 hirelings can still be hired for their services and passives but take no combat actions: they are
  outside the attack rotation and the turn queue (`Party::actingCombatantCount`). Monsters still pick them as targets.
- **The bow at any range (user, 2026-11-14).** With the bow in the arms (swapped in, or an archer's), Attack shoots
  even at melee range (WEAPONS.md, "Bow swap"). With the melee weapon in the arms it never shoots: out of reach the
  blow swings at the air, where a party member would fire the bow (`PartyAttackConfig::preferMelee`; talent shots
  excepted).
- **The Oblivion art ships (user, 2026-11-14).** The converted Oblivion arms, clips and weapons in
  `assets_dev/engine/view_model/` are committed and packaged with the solo run from release 2.4, by the user's decision
  after the licence risk was raised (Bethesda still sells Oblivion). Our own arms, rig, clips and held weapons remain
  the long-term replacement.

## References

No single game has all of it. Skyrim is the closest whole (one character, sword and shield with an active block and
bash, spells from either hand, favourites on keys 1–8, a perk tree per skill, Shouts and once-a-day powers, ragdolls)
but has no visible hotbar and floaty melee. Dark Messiah of Might and Magic is the reference for the feel of blows
(kick, physics, block), Vermintide 2 for crowds and gore, Avowed for a modern minimal HUD (its six ability keys and a
pausing radial menu were its most criticised part). The first-person arms follow Oblivion: one set of arms for every
weapon type, the shield on the left forearm, spells from the open hand, gauntlets and race on the arms.

## Prototype: Oblivion arms (shipped from 2.4 by the user's decision)

The arms, skeleton and animations come from the original Oblivion (GOTY), converted to GLB locally under the
git-ignored `reference/oblivion_poc/` (see its README for the converter). That raw conversion stays local; the
installed GLBs are sources in `assets_source/engine/view_model/` (install with `tools/install_model.py <glb>
--view-model`), cooked into `assets_dev/engine/view_model/` like every model (ASSET_COOKING_PLAN.md §16), whose
`*.textkeys.json` stay there beside them; they ship (see above). They are a stand-in for our
own arms; the engine side does not depend on them beyond the clip and node names below.

- A solo run draws the engine's arms, `assets_dev/engine/view_model/arms.glb` (since 2026-11-14 the HD human arms,
  `arms_hd_human.glb`: hands, forearms, 147 first-person clips), loaded through the packages like any asset.
  `[debug] view_model_path` names another arms GLB on disk instead (another race, `arms_full.glb`). Weapons
  and the shield are separate GLBs beside it (`w_*.glb`, `s_steelshield.glb`) in the space of the node they hang on
  (`Weapon`, `Bip01 L ForearmTwist`); `<arms>.textkeys.json` holds Oblivion's text keys.
- `game/render/FirstPersonViewModel` draws the arms in their own view (`FirstPersonViewModelView`, after the world,
  AO and bloom, before grading and the HUD) with their own 60° projection and depth, so they never clip into walls.
  The eye is the clips' animated `Camera01` node. They are lit as a creature at the eye would be
  (`OutdoorGameView::eyeModelLighting`, `IndoorRenderer::eyeModelLighting`: sun, sky and bounce from the baked probes
  outdoors, the room's ambient and daylight indoors, the nearest lights as a list), turned into the arms' space with
  the camera. Two changes for the held weapon (`sceneViewModelLighting`, 2026-11-14): where the scene has no sun
  (indoors) the arms get a soft key from above, left and in front of the eye, in the room's colour and as strong as
  its ambient (`HeldKeyStrength`), since metal takes almost none of the ambient and a blade read black in a dungeon;
  and the sky reflection loses its tint (its strength kept), which laid a blue cast over a blade filling a third of
  the screen. The converter gives Oblivion's specular as PBR: the normal map's alpha is the specular mask
  (`openyamm_specular_mask`), skin stays dielectric, masked metal turns half metallic and smoother; skin is drawn
  two-sided, since the single-sided hand shell shows its palm's inside through the thumb's web in a fist.
- The kit follows the active member's main hand: sword, axe, mace (one- or two-handed by `ItemRules::wield`), dagger,
  staff, and spears, tridents, halberds and poleaxes (their own `pole` set since 2026-11-14, by the item's held.yml
  kind: WEAPONS.md "Pole set"), fists without a weapon; a shield in the off hand is drawn and
  blocks. An archer (nothing in the main hand, a bow in the bow slot) draws the bow. Clip names are `<set><action>` with sets `onehand`, `twohand`, `staff`, `bow`, `handtohand`; `dual`, `crossbow` and `pole` are baked into the arms (WEAPONS.md).
- Oblivion's text keys drive the timing: `Hit` is the blow, `a:L`/`a:R` where a further attack chains into the other
  side (attacks combine right, left, right as in Oblivion), `Blend: N` the crossfade, `Attach` when an equip clip's
  weapon reaches the hand.
- Debug console: `viewmodel pose <clip> <seconds>` holds a frame, `viewmodel kit <set> <weapon.glb|none> <0|1>`
  overrides the kit, `viewmodel clips` lists clips with their Hit times. Input tours gained `middle_down`/`middle_up`.

Run it: `./tools/run_game.sh --isolated arms --world mm6 --map oute3.odm --ruleset maw:solo --visible --seconds 0`.
Middle mouse blocks.

**A dragon draws its own forelegs** (built 2026-11-14, [DRAGON.md](DRAGON.md) "Built in the engine"): a member for
whom `ClassRules::isDragon` holds (MAW: the portrait's race) shows `assets_dev/engine/view_model/dragon_forelegs.glb`
(our own art, the `claws` set: rakes right and left, a bite on the fifth blow, the Scales guard on block, the breath at
range released at its clip's Hit from the mouth) as a second view model; everyone else keeps the arms. To see it, add
`--set debug.console=true` to the run above and type `testparty apply early solo_dragon` in the console.

### Verification of the converted animations

Checked against the data rather than by eye: Euler keys match the clips' stored first poses (orientation and order),
the compressed B-spline channels (2,641 rotation channels, the bulk of the motion) have no hemisphere flips and the
looping idles close (median error 0.005), the hand and forearm weights are the skin partitions' exactly (no
truncation; seam duplicates share weights), and the bind pose equals the first-person skeleton. Blender and the game
draw the same poses. What looked wrong came from presentation, now fixed: Gamebryo's clockwise triangles (flipped for
glTF), a 180° turn in the engine's glTF placement, missing normal maps (the knuckle creases read as cracks), a
downward camera pitch Oblivion does not use, and too short a crossfade into swings (Oblivion's attacks start from a
raised arm). The remaining roughness (a crease tearing at the knuckles in the hardest bends, blocky elbows) is the 2006
hand mesh itself.

## Gameplay hooks (prototype)

- **Swing then hit, fitted to the recovery.** While the view model shows a melee kit, the attack key starts a swing
  and the attack waits for the clip's `Hit` key; the ordinary attack then runs against whatever the crosshair or the
  usual fallback finds in reach at that moment (`GameplayScreenRuntime::ViewModelLink`). MM's recovery counts from the
  press: the swing is played fast enough (1–3.5× Oblivion's speed) to reach its chain point (`a:L`/`a:R`, or 0.3 s
  after `Hit` for a clip without one) as the recovery ends, and the recovery applied at the blow is the member's minus
  the time the swing took (`PartyAttackConfig::recoverySpentSeconds`). The recovery is the ruleset's own (MAW's weapon
  delay through `CombatRules::characterAttackRecoveryTicks`, else the engine's). A swing starts only when the active
  member is ready; a held key starts the next one as the recovery ends. The whoosh plays when the swing starts
  (`GameplayActionController::playMeleeSwingSound`), not at the blow. A two-second safety in game time (the view
  model's clock, so slow motion keeps the blow at `Hit`) releases a blow the view model never reports. Measured live
  (`viewmodel trace on`, MAW solo knight): level 1, recovery 1.30 s: blow at +0.33 s, 0.96 s left, next swing 1.3–1.4 s
  after the last; level 200, recovery 0.47 s: rate 1.07, blow at +0.31 s. At `debug.time_scale 0.3` the blows still
  land at `Hit`. Air swings in MAW take the engine's recovery, not MAW's (`buildUntargetedMeleeAttack`, older code).
- **Combo.** Repeated attacks play right, left, right chop, left chop, then a power attack by the movement direction
  (standing `attackpower`, moving forward, back or sideways the matching `attack*power`), and start over from the
  right. The combo also continues across a recovery longer than the swing, unless the arms rested for a second
  (`FirstPersonViewModel::nextSwing`). The staff uses the two-handed clips with the staff
  re-gripped near its butt (`w_staff_grip.glb`; held at its middle, as Oblivion builds it, the shaft ran back through
  the camera); Oblivion's `staff*` clips cast spells. The blade tip for the blow's direction is the weapon's +Y end
  (Oblivion's weapons point along +Y from the grip). Bare fists take the blow's direction from the fist that
  travelled further since the swing began. [WEAPONS.md](WEAPONS.md) proposes per-weapon paths instead (power attacks
  kept for special skills); the review below shows both.
- **Review set.** Every kit's clips with frame strips and blade paths, plus a live combo video per kit, in the private
  viewer `reference/oblivion_poc/review/` (built by its `tools/gen_tours.py` and `tools/build_review.py`).
  `viewmodel path <clip> <file.json> [samples]` dumps a clip's blade tip, hilt and left-hand screen path with the
  current kit; `viewmodel trace on` prints each swing's clip, rate and blow, and the active member's recovery.
- **Blow direction.** At the blow the view model projects the blade tip's motion on screen; the melee hit effect
  (`MeleeContactEffectInput::blowDirection`) takes that direction instead of the attacker's portrait side.
- **Shield block.** Holding the block with a shield raises it (`Party::shieldRaisedMember`, transient): a physical
  monster blow or missile loses 40 % (Normal), 55 % (Expert), 70 % (Master) or 85 % (Grandmaster), and the block-hit
  clip plays (`GameplayCombatController::shieldBlockedDamage`, tests/ShieldBlockTests.cpp). Raised, the arm does not
  swing. Not yet: facing (a blow from behind is blocked too), stamina, a shield bash.
- **Cast then release, fitted to the recovery.** A quick or action-bar spell (GameplayInputController) and an Attack
  whose battle orders hold an enabled spell (GameplayInteractionController) wait like a swing (`ViewModelLink`:
  `waitIsCast`, `quickCastWaiting`): the arms play the kit's cast clip fitted to the spell's recovery at the caster's
  mastery (`GameplaySpellActionController::prepareViewModelCast`), and at the clip's `Hit` the cast is made exactly as
  the press would have made it (the same path, so SP, target, failure messages and rules are unchanged); the recovery
  it sets is shortened by the clip's time, so it counts from the press. The Attack's orders still decide at the
  release (a spell order that no longer holds falls through to the weapon, as at the press). Casts gameplay makes
  itself (upkeep, scrolls) show the clip at once. Same two-second game-time safety as swings; turn-based combat casts
  at once.
- **Bow shot.** With the bow kit the attack key plays `bowattack` and the attack waits for its `Release` key (1.43 s):
  the right hand takes an arrow over the shoulder (`Attach`, 0.27 s), nocks and draws it, and looses it; the ordinary
  attack then runs (a shot at any range in a solo run, as with the bow swapped in; see WEAPONS.md, "Bow swap"). As a
  swing, the press waits while the member recovers, the clip is fitted to the member's bow recovery (not the melee
  one) and that recovery counts from the press; the bow's sound plays as the arrow leaves, with no swing whoosh at the
  press. The safety timeout counts game time, so slow motion keeps the release.

## Weapon trail and casting effects (prototype)

**What it is called.** The streak a blade leaves in the air is a *weapon trail* (also *swing trail*, *sword trail*,
*slash trail*; the comics' "sword lines"). It is not the hit effect: that is the contact effect at the struck point
(devdocs/MELEE_HIT_FEEDBACK_DESIGN.md), already in.

**What others do.** Vanilla Skyrim draws none; mods add them, the Precision mod with configurable lifetime and
smoothness ([Nexus](https://www.nexusmods.com/skyrimspecialedition/mods/72347/)) and others only for enchanted
weapons. Vermintide 2 draws them in first person with a setting: Normal, off for non-criticals, Off
([patch notes](https://devtrackers.gg/vermintide2/p/4f8c6f9c-free-dlc-karak-azgaraz-out-now-on-ps4-and-xbox-one)).
(Not checked against sources: Mordhau, Chivalry 2, Dark Messiah, the Souls games, Monster Hunter and Kingdom Come;
the searches found nothing first-hand on their trails.) The common ground of the checked ones: short, only on fast
motion, faint or none for plain steel, coloured for enchanted weapons, and a setting.

**Our look** (FirstPersonViewModelFx). A ribbon swept between the blade's lower fifth and just past its tip, over the
last 0.11 s, built from the hilt and tip sampled each frame and smoothed (Catmull-Rom, four pieces per frame gap).
Additive; brightest just inside the tip, faint towards the hand, a soft outer edge and faint lengthwise streaks; fading
with age. It appears only while the tip moves fast (from 140 to full at 420 of the arms' units per second), so rest,
walk and block draw nothing, and it fades through the blow. Plain steel is a faint cool white (50 %); a weapon with an
element (the strongest of its enchantment and the rules' elements, `meleeWeaponElementsFor`, chosen at the swing's
start) takes that element's colour at 70 %. Swings and the melee talents (Cleave, Whirlwind, Charge) trail; casts,
the bow and bare fists do not. Setting `[gameplay] weapon_trails` (on). `viewmodel pose <clip> <s>` draws the trail
the clip would have left at that moment, for review.

**Casting glow.** During a cast clip motes gather on the casting palm (a swirl pulled in, about 55 a second, more as
the cast builds) around a pulsing core, and at the clip's `Hit` the spell leaves in a flash and a burst of sparks
forward; then the glow is gone. Coloured by the spell's school (FirstPersonViewModel::schoolColor): Fire red-orange,
Air pale blue-white, Water cyan, Earth amber-green, Spirit gold, Mind violet, Body green, Light white-gold, Dark deep
violet (additive light cannot darken), others a neutral arcane lilac. The palm is between the wrist and the four
knuckle joints; the glow is drawn over the hand (light in the palm shows through the fingers), the trail behind
the arms. `viewmodel fx <school|off>` with a held cast pose shows the glow for review.

**Casting in Oblivion and here.** Measured on the clips' hand travel: `casttarget` casts with the left hand (the right
barely moves), `castself` and `casttouch` with both hands, the `onehandcast*` clips with the left hand while the
weapon hand stays still at the side, and the `*alt` clips with the right hand. There are no two-handed, staff or bow
cast clips: Oblivion casts with the left hand and lets a two-handed weapon hang in the right. Here: every kit with a
weapon in the right hand (one-handed with or without a shield, two-handed, staff) uses `onehandcasttarget`/
`onehandcastself`, the weapon hand still at the side (the bare-handed clips lift the right hand too, which swung a
staff's shaft across the view in the live check); fists use `casttarget`/`castself`; the bow, held in the left hand,
uses `casttargetalt`/`castselfalt` from the right hand. A two-handed weapon is mostly below the view during a cast.
Heals, buffs, cures and utility spells take the self clip, missiles and spells on monsters the target clip
(`PartySpellSystem::describeSpell`). Spells still leave from the party's usual point, not the hand; the flash at the
palm covers the moment.

**Checks (2026-11-14).** Live in a Standard solo run (`viewmodel trace on`): a fire spell on key 3 played
`onehandcasttarget`, left the hand at +0.38 s (its `Hit`), killed the goblin, and set 1.07 s of the 1.5 s recovery,
so the member was ready 1.5 s after the press; Torch Light, Haste, Fire Resistance and Immolation (self clip) and
Fireball and Fire Spike (target clip) the same. Fire Aura asks for an item, so it is cast at once and its window
opens (spells that open a window are not deferred). No heal was on either test character's bar; heals take the same
self path. Captures, private (Oblivion arms), in `reference/oblivion_poc/preview/fx/`: `trail_sheet.jpg` (sword,
claymore, mace, dagger), `cast_schools_sheet.jpg` (the nine schools), `cast_kits_sheet.jpg` (fists, sword and shield,
claymore, staff, bow), `live_sheet.jpg`. They are rebuilt by `reference/oblivion_poc/tools/fx_tours/run_fx_tours.sh`
(three tours). With the monitor asleep, game runs work on a headless GNOME Shell with a virtual monitor: start
`dbus-run-session -- gnome-shell --headless --wayland --no-x11 --virtual-monitor 1600x900 --wayland-display
oyheadless &`, then run with `HEADLESS=1` (the script sets `WAYLAND_DISPLAY=oyheadless SDL_VIDEODRIVER=wayland`; the
window must be `--visible`, a minimized one gets no frame callbacks and the run times out).

**Not done.** Spells still leave from the party's usual point, not the hand. A two-handed weapon is mostly out of view
during a cast (as in Oblivion). The glow sits in the palm and shows through the fingers by design. The trail is
untested at 3.5× swing rates in play (held poses only), and the Attack key's battle-order cast is exercised only by
code reading (the test characters had no spell orders).

## Proposed, not built

- **Hitting several monsters.** One-handed weapons hit one target, as today. Two-handed swords and axes cleave: the
  swing also strikes up to two other monsters inside its arc (±50° of the crosshair, within melee reach), each with its
  own to-hit roll and half damage. Talents widen it (Cleave: +1 target at full damage; Whirlwind: all around). This
  keeps MM's single-target balance for most builds and gives the heavy weapons their role.
- **HUD, action bar and special skills:** the study in
  [level_generation/ui/solo_action_hud_20261113](../../level_generation/ui/solo_action_hud_20261113/README.md)
  (variants A–D and the recommended R: small unit frame top-left, ten-slot bar on 1–0 in the basebar panel, a special
  skills screen with schools tied to MM skills and masteries, one point every ten levels plus one per promotion).
- **Bows (built for archers):** as Oblivion does it, from its data. The bow's root hangs on the left hand's `Torch`
  node (checked: from `Attach` to full draw the arrow's nock stays within 4–7 units of the right fingertips and the
  drawn string meets them within 1.5). The string is a morph (`Bow:0`'s `BowMorph`, keyed in the clip: slack until
  1.03 s, full at `Hold` 1.37 s, a damped twang after `Release`), the arrow hangs on the bow's `ArrowBone` (keyed in
  the clip) and shows between `Attach` and `Release`. `w_bow.glb` is its own instance with clips of the arms' names
  (`rest` for the others), placed on `Torch` each frame. Open: a member with both a melee weapon and a bow shows the
  melee kit, and MM's automatic shots at far targets show no draw (switching kits would cost Oblivion's 0.8 s equip on
  top of the 1.4 s draw); Oblivion's hold at full draw while the key is held is not used.
- **The HUD's implementation plan** (unit frame, buff rows, action bar, crosshair brackets, special-skills page, keys,
  save data, stages): [HUD.md](HUD.md).
- **The Dragon** (two claws, the breath, its special skills and art route): [DRAGON.md](DRAGON.md).
- **Balance and talent trees** (the solo power gap measured on MAW at Nightmare and Beyond Madness, the proposed Lone
  Hero rule, the trees per MM skill and the point economy; scenarios and the model in `tests/scenarios/solo_balance/`):
  [BALANCE_AND_TALENTS.md](BALANCE_AND_TALENTS.md).
- **Talents as built** (MAW solo run: the table, points, passives in MAW's rules, the actives from the action bar, the
  Talents page behind the Skills / Talents switch, respec at training halls, the `talent` console command):
  [TALENTS.md](TALENTS.md).
- **Held weapons** (every weapon kind's hand rule, animation set and attack path; spears, polearms, staves and dual
  wielding; our item models as held weapons and their grip table): [WEAPONS.md](WEAPONS.md). Built since: the dual,
  crossbow and pole sets (WEAPONS.md); our ground
  models are held in a solo run (`engine/world_items/held.yml`, "Held weapons in the game") and the melee/bow swap
  (`swap_weapon`, mouse 4; with the bow drawn Attack shoots even at melee range, "Bow swap").
- **Own arms** to replace Oblivion's: one rig with the same node names (`Camera01`, `Weapon`, `Bip01 L ForearmTwist`)
  and clip names, material sets by armour and race; Oblivion's clips remain the timing reference.

## Arm textures, race skins and our own arms (2026-11-14)

Full record: [level_generation/solo_action_arms_20261113/README.md](../../level_generation/solo_action_arms_20261113/README.md).

- **The blur, measured:** Oblivion's forearms use 24 % of a 512 x 256 texture (equivalent 253 px, a quarter of the
  hands' density); the hands share one mirrored 512 x 256 set.
- **Route A (private, Oblivion mesh):** new even UVs for hands and forearms in one 4K atlas (PartUV + sparrow, about
  82 % used, spread 1.14), written into the animated GLB without touching skeleton, weights or clips; a Meshy 4K paint
  on those UVs (10 credits); a procedural pore normal detail. Hands about 5x, forearms about 15x the original
  density. Meshy's paint is soft; the fine detail is the normal map's.
- **Race skins:** `reference/oblivion_poc/glb/arms_hd_<race>.glb` for human, elf, dwarf, vampire, dark elf, goblin,
  undead (colour ramps of the human paint, read off the MM8 portraits) and troll, minotaur, zombie (their own paints,
  ramped). A texture cannot give claws, the minotaur's thick hands or the undead's bones.
- **Route B (shippable path, our meshes):** our humanoid rigs use biped names, so `graft_arms.py` re-poses any of our
  models' forearms and hands onto the first-person skeleton and the Oblivion clips drive them unchanged. Per-race
  shapes come free (the lich's bones, the minotaur's fists). Our arms need smoothing (one subdivision level), the upper
  arm kept and a thicker girth to read at first-person distance; then the same new UVs, 4K paint and detail.
- **In the game** (solo run, the mockup scene; `reference/oblivion_poc/preview/arms_hd/races_ingame_sheet.jpg`):
  route A is a clear gain and every race reads; route B's grafted fists do not close (finger lengths and rolls differ),
  so it proves the rig contract but is not the shippable arm.
- **Recommendation:** route A for the prototype now; for shipping, a dedicated first-person arm pair of our own built
  in the first-person bind pose (HD masters, Meshy, playbook hand gate), then this UV, 4K paint and detail pass.
- **Engine hook (not built):** pick `<stem>_<race>.glb` beside `[debug] view_model_path` by the active member's race.

## Open decisions

The study's list (portrait placement, HP/SP echo, second bar row, buff panels, point rate, magic talents, a signature
skill, special skills in party mode) and: whether solo mode is a new-game option on Standard and MAW or its own
ruleset; cleave as proposed; block facing and stamina; whether bows are in scope.
