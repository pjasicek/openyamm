# Melee hit feedback

Design for how a party member's melee hit reads on screen and in sound, for a first-person party of up to five in
real time or turn-based combat. Everything below is implemented; "Proposed next" lists what is left.

## Starting point

The MMerge **Sword Swing Mod** (v1.4, MM6/7/8/Merge, MMExtension Lua) was the prompt. On every melee hit it summons
one of four white crescent sprites 40 units in front of the party, rotated towards the monster, at a height between
the party's eye and the monster. It shows hits only and has one look for every weapon. The visible slash is the
point: the player sees the blow land. We keep that idea, but draw the slash on the monster at the contact point, in
HD, with a shape per weapon class and a direction per party member. We use none of its code or art.

## What makes a hit read

The strongest study of impact feel (Lin et al. 2022, "Impact feedback features", arXiv:2208.06155) ranks **hitstop**,
**sound coherence** and **camera control** highest. Practitioner guidance adds a contact effect at the point of
impact and a material sound. First-person party games put the effect on the enemy, not in front of the camera: a
slash, pierce or crush mark over the target, plus damage numbers.

## Layers

| Layer | What | Setting (default) |
| --- | --- | --- |
| Contact effect | Sword/axe: an arc swept through the contact point. Spear/dagger: a straight streak ending in a puncture flash. Mace/staff/club/fists: a radial burst and a shock ring. Light, normal and heavy variants by blow strength | `gameplay.melee_hit_effects` (on) |
| Attacker attribution | Each party slot swings from its own side of the portrait row | part of the contact effect |
| Weapon element | A fire, air, water, body, light or dark weapon adds a coloured halo and element particles to the blow | part of the contact effect |
| Miss | A faint blow passing beside the target (the swing sound already plays) | part of the contact effect |
| Material contact | Blood for flesh and leather (a spurt of drawn-out drops arcing down, round drops and a fine mist), sparks for armour and metal, chips and dust for bone, stone, earth and wood, shards for glass, drops for liquid, ichor for chitin, goo for slime, motes for ethereal | `gameplay.melee_hit_effects`; blood and gore follow `gameplay.melee_hit_blood_effects` |
| Material impact sound | Sound of what was struck (flesh, leather, chain, plate, bone, stone, metal, wood, glass, liquid, ethereal), glancing/normal/crushing | `gameplay.melee_hit_feedback` (on) |
| Target hitstop | Struck actor's animation clock holds for 0 to 90 ms; combat timing untouched | `gameplay.melee_hit_feedback` (on) |
| Target flash | 70 to 120 ms mix towards warm white over the struck sprite or model, peak 12 to 25% | `gameplay.melee_hit_flash` (off) |
| Camera kick | A 1.5 degree turn of the view along a critical or killing blow, back within 0.2 s | `gameplay.melee_camera_kick` (off) |

All five settings are in the Video settings menu (Colour & effects) and the INI `[gameplay]` section.

## Blow strength

Crushing on a kill, critical damage (`CharacterAttackResult::criticalDamage`) or damage of at least 30% of the
target's maximum HP; glancing below 6%; normal otherwise. It picks the impact sound, the hitstop, the flash and the
effect variant (`_light`, normal, `_heavy`).

## Contact effects

`openyamm:fx/melee/{slash,thrust,crush}{_light,,_heavy,_miss}`, the element accents
`openyamm:fx/melee/{class}_element_{fire,air,water,body,light,dark}` and the material contacts
`openyamm:fx/melee/contact/*` in `engine/effects/authored/melee_library.yml`, generated with their textures by
`tools/fx/generate_melee_effects.py` (original procedural art plus the CC0 particle sprites; edit the generator and
rerun). Its PNG frames are sources in `assets_source`; the game loads one cooked atlas per sprite (BC7 on desktop,
ASTC on Android, `tools/cook_effect_textures.py`, `ASSET_COOKING_PLAN.md` §11).

- **Placement.** At the contact point (`resolveMeleeContact`: the crosshair hit on the target, else the world's
  contact point, else the body surface facing the party), pulled 24 units towards the party so the body does not cut
  it. The effect's plane faces the attack source.
- **Direction.** Local +X is the blow's direction on screen and +Y the outer side of the arc. The leftmost portrait
  cuts from the left towards the lower right, the rightmost from the right (mirrored), the middle nearly straight down,
  with a few degrees of random tilt; a member in the exact middle takes a random side. Thrusts are flatter.
  `game/gameplay/MeleeContactEffects.{h,cpp}` (`buildMeleeContactEffect`).
- **Size.** Authored for a 160-unit target and scaled by the target's height (0.6 to 2.2), times 1.15 for
  two-handed weapons. Heavy variants are 25% larger and warmer.
- **Layers.** Each class is an alpha-blended white body (readable on bright outdoor scenes) over an additive cool
  glow: a 6-frame sweep (45 fps) then a fading final frame for the arc, a 4-frame streak for the thrust, a 5-frame
  spike burst for the crush, plus a short camera-facing contact flare and, for heavy blows and crushes, a shock ring.
  Effects last 0.2 to 0.35 s.
- **Weapon.** The main-hand item's skill group (`meleeWeaponClassForSkill`); no weapon or a broken one is fists.
- **Element.** Every element in the attacker's melee elemental damage bonuses, strongest first and at most three
  (`ItemEnchantRuntime::characterAttackElementalDamageBonuses`, `meleeWeaponElementsFor`), so a dual wielder with a
  fire sword and a poison sword shows both. Each accent is spawned with the same transform: the blow's shape in the
  element's colour behind the white body, plus element particles (a fire burst with flames and embers, electric arcs,
  frost glints, poison drops, light motes, dark smoke).
- **Miss.** A melee attack on a target in range that misses draws `{class}_miss`: a faint arc or streak shifted to
  pass beside the contact point, with no flare, accent or particles.

## Victim material

Each monster names what it is made of in the `HitMaterial` column of `engine/data_tables/monster_descriptors.txt`
(MM9 rows in `worlds/mm9/data_tables/monster_descriptors.txt` take their legacy stand-in's material). The name is a
row of `engine/data_tables/melee_hit_materials.txt`, which gives its impact sounds, its contact effect and whether
that effect is blood or gore. A monster naming an unknown material fails the table load. This replaces both the
earlier picture-family table and the original `bloodSplatOnDeath` flag for hit reactions, so dragons, rats and nagas
now bleed when struck; death splats still follow the original flag. Contact particles are spawned at the contact
point with their local +Z along the outward normal, sized by the target's height (0.7 to 1.8), and world-space
emitters may set `gravity` so chips and drops fall. Every contact effect comes in three strengths
(`{id}_light`, `{id}`, `{id}_heavy`: about half, normal and 1.8 times the particles, slower or faster and smaller or
larger), chosen like the blow's own variant (`meleeContactEffectVariant`). Our own blood
(`openyamm:fx/melee/contact/blood`) replaced the MM9 melee blood for flesh and leather; `mm9:melee_blood` stays in the
MM9 library.

## Sounds, hitstop and flash

On a successful melee hit (`GameplayActionController::executePartyAttack`), after damage is applied:

| Strength | Hitstop | Flash (when on) |
| --- | --- | --- |
| Glancing | none | 0.07 s, peak 0.12 |
| Normal | 0.05 s | 0.09 s, peak 0.18 |
| Crushing | 0.09 s | 0.12 s, peak 0.25 |

Only the struck actor freezes. The world never pauses, so five members attacking cannot stack a global freeze, and
only the animation clock stops: `actionSeconds`, recovery and attack impact timing keep running, so hitstop does not
change combat balance. The flash fades quadratically from its peak and is mixed in display space on both sprites and
models. With the flash off no flash is triggered: creatures stay in the instanced skinned batch and the shaders skip
the mix.

### Data

- `engine/data_tables/melee_hit_materials.txt`: material name, glancing/normal/crushing sound paths (after MM9's
  `DATA/MATERIALS.txt`), contact effect and blood flag. `Bone` and `Chitin` borrow the hollow wood set, `Slime` the
  liquid set; `Ethereal` has no sound yet.
- `engine/data_tables/monster_descriptors.txt` column `HitMaterial`: one material per monster.
- `engine/audio/melee_hits/`: the 36 MM9 sounds, see its `SOURCES.md`.

## Code

| Piece | Where |
| --- | --- |
| Strength, effects, sound, hitstop/flash/kick trigger | `game/gameplay/GameplayActionController.cpp` (`resolveMeleeContact`, `resolveMeleeHitStrength`, `queueMeleeContactParticles`, `placeMeleeBlow`, `queueMeleeBlowEffects`, `kickCameraAlongMeleeBlow`, `presentMeleeHitFeedback`) |
| Effect choice, element, direction, size | `game/gameplay/MeleeContactEffects.{h,cpp}` |
| Effect spawn | `GameplayFxService::queueWorldEffect` and `queueSurfaceEffect`, consumed by `consumePendingWorldFxRequests` |
| Camera kick | `GameplayActorHitFeedback::triggerCameraKick`; added to the view by `OutdoorGameView::effectiveCamera*` and `IndoorRenderer::view*Radians` (render, culling, crosshair picking; not movement) |
| Per-actor flash/hitstop timers (shared, transient, never saved) | `game/gameplay/GameplayActorHitFeedback.{h,cpp}`; each world runtime owns one (`actorHitFeedback()`), cleared on map load, aged in `GameSession` while the world runs |
| Material lookup | `MonsterTable::loadMeleeHitMaterialsFromRows` / `findMeleeHitMaterial` |
| Hitstop | `ActorRuntimeFacts::hitstopActive` stops `actorAnimationTickDelta` (shared AI, both worlds, including dying); the turn-based paused animation loops honour it too |
| Sprite flash | `LitBillboardVertex::hitFlash` (`a_texcoord2`), mixed in `billboard_lit.sh` |
| Model flash | `GameplayRuntimeActorState::hitFlash` to `ModelInstanceSystem::setHitFlash` (`WorldFxSystem::syncActorModels`); `u_modelEdge.y` in `fs_model.sc` |

## Known limits

- On 3D creatures the crosshair contact point lies on the picking box, not the mesh; for targets not under the
  crosshair the outdoor fallback uses the 2D sprite frame. Nearest skin-joint bounds
  (`ModelInstanceSystem::deformationBounds`) would place it on the body.
- Ethereal targets (ghosts, wisps, fire and air elementals, genies) play no impact sound.
- Materials were first assigned by picture family with a one-off migration; individual monsters can now be corrected
  in the column. Blood is always red; insects and slimes use their own ichor and goo instead.
- Held attachments (a creature's weapon) do not flash.

## Proposed next

- Attacker portrait rim pulse.
- A soft impact sound for ethereal targets.
- Contact points on the 3D mesh rather than the picking box.
