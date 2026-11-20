# All projectiles: design proposal, asset sources and first implementation

Status: implemented (2026-10-11; third round 2026-10-15). Every flying projectile, including Sparks and arrows, has an
enhanced flight effect, and every bound projectile has an authored impact. Since the third round (section 10) the
instant spells that kept the classic burst or drew nothing (Implosion, Inferno, Immolation, Mass Distortion, Spirit
Lash, Prismatic Light, Souldrinker, Lifedrain, Armageddon) have impacts too, and Deadly Swarm no longer flies as its
native sprite. Shared monster missiles have per-monster variants
(dragons, gogs, fire elementals, bone dragons, mages). Section 9 records the second round; the designs still want
review in game. Since 2026-10-16 there is no classic style and no projectile or impact draws its native sprite: solid
projectiles are 3D models (`engine/models/projectiles.yml`, `level_generation/props/projectiles_claude/`), Sparks'
effect draws its whole crackling ball, a projectile falling into water plays `water_splash`, and the regression case
`projectile_visuals_draw_no_native_sprites` (suite `projectiles`) keeps it so; references to the classic style below
are history. Since 2026-10-23 a world can add its own missiles, bound to effects by object name
(section 12, Hesper's palette).

Fire has its own, more detailed proposal: [PROJECTILE_VFX_FIRE_PROPOSAL.md](plans/PROJECTILE_VFX_FIRE_PROPOSAL.md). The
background (layered projectiles, ribbons, the first test) is in
[PROJECTILE_VFX_INVESTIGATION.md](plans/PROJECTILE_VFX_INVESTIGATION.md).

## 1. Approach

Every school uses the same layers as fire, recoloured and re-weighted:

- **Core:** a small, very bright glow on the collision point, always the brightest thing.
- **Head:** the school's shape: a flame, an electric blob, a glint, a soft star, a rock clump, a water orb.
- **Trail:** either sprites shed by distance travelled (flame, mist, wisps, ripples, dust) or a ribbon (electric
  arcs, water, light, blades). Shed sprites suit things with volume; ribbons suit energy and speed.
- **Body tone:** alpha-blended smoke, mist or dust where the school has a dark or dirty side, so it does not wash out
  to a flat bright colour. This was the lesson of the fire test.
- **Sparks or glints:** a few small fast accents.
- **Native sprite:** where the original game draws a sprite for the projectile (ice shard, rock, blades, fist,
  meteor, star, toxic cloud), it stays visible under the effect, so the spell keeps its identity.

**Size and brightness rise with danger**, as in the fire ladder: monster missiles are smaller and rougher than the
party's spells; strong spells (Lightning Bolt, Sunray, Incinerate) are the largest and brightest.

## 2. Schools

| School | Palette | Head | Trail | Accent |
|---|---|---|---|---|
| Fire | white-yellow → orange → red → dark smoke | fireball flipbook | flame tongue over smoke | embers |
| Air | white → pale blue → deep blue | white core, velocity streak, electric blob | jittering electric ribbons over a soft glow ribbon | fast sparks |
| Water | white-cyan → cyan → deep blue; poison and acid green | water orb, ice glint | flowing ribbon, mist | falling droplets |
| Earth | amber glow, tan and brown dust | rock or debris clump | dust trail | falling pebbles |
| Body | green-teal life, blood red for Harm | pulsing glow | soft ribbon, wisps | — |
| Mind | amber and violet | pulsing soft star | expanding psychic ripples, wisps | — |
| Spirit | silver-blue, ghostly | glint | faint ribbon, rising wisps | — |
| Light | white → gold | glint or starburst | white-cored golden ribbon | sparkles |
| Dark | black-violet with a violet rim; poison green-black | dark glow | alpha-blended dark ribbon and smoke | — |
| Technology | red-hot | long velocity streak | thin solid ribbon | — |

## 3. Projectiles and what they look like now

All of these are implemented as first passes. The effect ids are `openyamm:fx/projectile/<effect>`.

| Projectile (recipe) | Effect | Design |
|---|---|---|
| Fire Bolt | `fire_bolt` | the comet: round flame head, flame tongue, faint smoke |
| Monster fire missile | `monster_fire_bolt` | spat flame: smaller, smokier, dirtier |
| Fireball | `fireball` | bigger churning double head, thick lingering smoke |
| Dragon Breath, Flame Blast | `flame_gout` | breathed flame that widens as it flies |
| Incinerate | `incinerate` | white-hot core, white-centred flame lance, little smoke |
| Meteor Shower | `meteor` | native rock in a large flame envelope, very heavy smoke |
| Fire Spike | `fire_spike` | small crackling star with a short flame trail |
| Darkfire Bolt | `dark_fire_bolt` | magenta-violet flame over black-violet smoke |
| Monster air missile | `air_bolt` | the approved design: core, glow ribbon, crackling arc |
| Lightning Bolt | `lightning_bolt` | the air bolt grown into a storm: flickering head, two wide arcs; replaces the flat yellow beam |
| Starburst | `starburst` | native falling star with a golden glint, sparkling ribbon and glitter |
| Monster water missile | `monster_water_bolt` | water orb, flowing ribbon, falling droplets, mist |
| Ice Bolt | `ice_bolt` | native ice shard in a cold halo, frost mist, ice glints |
| Ice Blast shards | `ice_shard` | small stretched frost streaks |
| Poison Spray | `poison_spray` | green dripping globs, low green mist |
| Acid Burst | `acid_burst` | bubbling yellow-green glob, acid drips, rising vapour |
| Monster earth missile | `monster_earth_bolt` | hurled rock and soil clump, dust, falling pebbles |
| Rock Blast | `rock_blast` | native rock trailing heavy dust and pebbles |
| Death Blossom | `death_blossom` | dark seed with a sickly glow and dust |
| Blades | `blades` | native blades, silver streak, thin sharp ribbon |
| Monster body missile | `monster_body_bolt` | pulsing green-teal energy with wisps |
| Harm | `harm` | native sprite, pulsing blood-red halo, dark red wisps |
| Flying Fist | `flying_fist` | native fist driving a red-orange streak with shock rings |
| Monster mind missile | `monster_mind_bolt` | amber soft star trailing lilac ripples |
| Mind Blast, Psychic Shock | `mind_blast` | violet star pulsing hard, bright ripples and wisps |
| Monster spirit missile | `monster_spirit_bolt` | silver-blue glint, faint ribbon, rising wisps |
| Monster light missile | `monster_light_bolt` | white-gold glint, thin golden ribbon, sparkles |
| Light Bolt | `light_bolt` | radiant starburst, white-cored golden ribbon |
| Sunray | `sunray` | blinding golden lance; replaces the flat beam |
| Destroy Undead | `destroy_undead` | holy soft star with drifting sparkles |
| Monster dark missile | `monster_dark_bolt` | black-violet smoke body and dark ribbon, dim violet core |
| Toxic Cloud | `toxic_cloud` | native cloud rolling out green-black smoke |
| Sharpmetal | `sharpmetal` | native shards with metallic glints and dark streaks |
| Blaster, monster "energy" missile | `blaster` | red-hot streak and thin solid ribbon |

**Who actually fires them.** In the merged monster table, ordinary monster missiles exist for fire, air, water, earth,
light, dark, energy and arrows. No monster uses the body, mind or spirit missiles; those effects exist for
completeness. The energy missile is the laser: 24 monsters use it, including MM8's Emerald, Sapphire and Ruby dragons,
the Chaos Hydra and the Archmage, so they all fire the red blaster bolt until per-monster variants exist.

**Monster variants.** Shared missiles are rebound per monster (section 9): dragons breathe fire, frost, lightning,
energy or grave smoke instead of the ordinary missile, gogs spit lava, fire elementals and genies throw living
flame, and archmages, warlocks and power liches fire an arcane bolt instead of the robots' blaster.

**Not covered:**

- **Cannonballs** are skipped by the projectile effects code.
- **Stun** keeps its debuff particles; the other debuffs also keep their procedural auras (section 10).

## 4. Asset sources

OpenYAMM is GPL-3.0 in a public repository. That decides what we can use:

- **CC0 and CC-BY assets** can be committed and shipped (CC-BY needs a credit line).
- **Our own renders** (Blender, or generated procedurally like the trail textures) can be committed.
- **Unity Asset Store, itch.io, Gumroad and ArtStation packs** cannot go into the public repository or a public asset
  download. Their licences allow distribution only inside a finished product, and loose textures that players can
  extract fail that test (the Unity EULA FAQ says so explicitly). They could only live in a private package.
- **Fab (Unreal Marketplace) content cannot be used at all.** Its licence (section 6a) forbids combining Standard
  License content with GPL-covered code and names the GPL as the example.

So buying a pack is not useful for the shipped game. A paid pack would be visual reference at most.

### Recommended free sources

1. **Kenney Particle Pack** (CC0, already used). I imported fourteen more shapes for this pass: glints, a starburst, a
   soft four-point star, a twirl, an electric blob, debris, wispy smoke, a streak, a flame lick, a wobbly ring and a
   slash. Good neutral white masks; low detail.
2. **Unity Labs VFX image sequences** (CC0, already used for FireBall01): 28 Houdini-rendered flipbooks, including
   explosions, flames, wispy smoke and clouds. The best source for fire and impact flipbooks, matching our fireball.
   https://unity.com/blog/engine-platform/free-vfx-image-sequences-flipbooks
3. **Raffaele Picca's particle and VFX textures** (CC0): glows, lights, flares and sparks at up to 1024 px, in black
   and white and alpha versions, made to be coloured. Better cores and glints than Kenney.
   https://github.com/RPicster/Godot-particle-and-vfx-textures
4. **Screaming Brain Studios noise packs** (CC0): hundreds of tileable noise textures, including streak noise. These
   feed the ribbon shader directly (lightning, mind, spirit, dark and water trails).
   https://screamingbrainstudios.itch.io/
5. **JangaFX free VDB simulations** (CC0): volume simulations of explosions, fire plumes and clouds. Rendered in
   Blender, they give our own flipbooks at any resolution and palette, for impacts and dust.
   https://jangafx.com/software/embergen/download/free-vdb-animations
6. **Viktor Hahn's spell animation spritesheets** (CC-BY 4.0): ice, skull smoke, holy wings and fire. Worth a look
   for ice and dark impacts; needs a credit.
   https://opengameart.org/content/spell-animation-spritesheets

Paid packs that would otherwise fit the look, for reference only: Gabriel Aguiar's Unique Projectiles, Hovl Studio's
projectile packs, Vefects Flipbook VFX (good lightning and poison flipbooks) and Kripto289's Realistic Effects Pack 4.

**Recommendation:** stay CC0. Imported so far (section 9): Kenney masks, five Unity Labs flipbooks (two
explosions, a flame column, wispy smoke and a cloud) and seven Picca flares, ray bursts and a swirl. Still worth
doing: a few Screaming Brain streak noises for the ribbons (itch.io needs a manual download), and JangaFX volumes
rendered in Blender for earth and dust impacts.

## 5. Engine work

- **Emit by distance** (`emission_distance` on sprite systems): continuous trails at any speed.
- **Mind Blast recipe:** Mind Blast and Psychic Shock had shared the Darkfire Bolt recipe; they now have their own
  (`mind_blast`), with the same classic look, so each can get its own flight effect.
- **Flame Blast** (spell 123) now uses the Dragon Breath recipe, so it flies and explodes like Dragon Breath.
- **Bindings** (`projectiles.yml`, `game/fx/ProjectileEffectBindings`): per recipe `flight`, `settled`, `impact`,
  `impact_follows_target`, `sprite: native|hidden` and `light: {rgb, radius}`, and `variants` that override those
  keys for listed monsters (by monster picture name). Unknown keys, recipes or effects fail the load; a unit test
  checks every variant monster exists.
- **Impacts:** a bound impact replaces the recipe's impact particles and native impact sprite; the recipe's impact
  light stays. The debug `effect impact-rebind` still wins over the file. Impacts carry their source monster
  (presentation only, not saved).
- **Settled state:** a projectile lying on the ground switches to its `settled` effect (the armed Fire Spike).
- **Sparks and arrows** go through flight effects; arrows and fire arrows have their own recipes, which change
  nothing in the classic style.
- **Particle roll and spin** (`random_roll`, `spin_speed` on sprite systems), used by smoke, flame and impact
  sheds so repeated puffs look less alike.
- **Debug firing:** `projectile spell <spell-id> <x y z> <tx ty tz> [skill] [mastery]` casts a spell from a point
  (event-sourced, so it hits whatever is in its path), and `projectile actor <index|last>
  <attack1|attack2|spell1|spell2> <tx ty tz>` makes an actor launch its attack now, indoors and outdoors.

- **Rendering cost:** animated effect sprites are packed into one atlas texture per sprite at load, additive sprites
  draw after the depth-sorted alpha sprites grouped by texture, and the indoor and outdoor renderers share one
  texture cache. Draw calls now follow the number of distinct textures on screen rather than the number of sprites:
  in a busy test (100–200 effect sprites) about 13 draw calls instead of 63. Bound projectile textures preload with
  the map in the enhanced style (about 25 MB uncompressed, once), so a first cast no longer stalls on image decoding.
  Particles refer to interned sprite ids instead of copying the string.

- **Chest traps** (2026-10-19): a discharged trap is the impact of its trap object (811–814), which is also its
  source, so it classifies as the binding-only recipes `fire_trap`, `elec_trap`, `cold_trap` and `poison_trap`. They
  bind the large fire, lightning, ice and toxic cloud impacts. The traps' native ball sprites (`sp101b`–`sp106b`,
  shared with the monster missiles) and the cannonball's `spell70c` are no longer drawn and were deleted.

Still open: cannonballs; compressed effect textures
(BC/ASTC would cut the 25 MB to about 5 MB).

## 6. How it is built

- **Generator:** `tools/fx/generate_projectile_effects.py` writes
  `assets_dev/engine/effects/authored/projectile_library.yml` (122 effects: 50 flight, settled and return flights,
  48 impacts, 24 auras) from
  per-school specs built on shared layer helpers (core, head, flame tongue, smoke, mist, ribbon, sparks, pulse;
  flash and burst for impacts). Tune the specs and rerun; the generated file is not edited by hand.
- **Bindings:** `assets_dev/engine/effects/projectiles.yml` binds 48 recipes and 9 monster variant groups;
  `assets_dev/engine/effects/spell_auras.yml` binds the buff, heal and debuff auras (section 11).
- **Textures:** `tools/fx/import_showcase_assets.py` imports the pinned archives (`--kenney`, `--picca`,
  `--explosion00`, `--explosion02`, `--flame02`, `--wispysmoke01`, `--cloud02`; any subset), with provenance and
  licences in `assets_dev/engine/effects/authored/`.
- **Setting:** none since 2026-10-16. `video.projectile_style` (classic) and `features.monster_projectile_visuals`
  (sprites) were removed; these effects are the only projectile look.

## 7. Next steps

1. Review the second round in game (section 9) and tune per school; the impacts are first passes.
2. Review the third round in game (section 10).
3. Screaming Brain streak noises for richer ribbons; JangaFX dust and debris flipbooks for earth impacts.

## 8. First-pass review in game (2026-10-11)

Captured in New Sorpigal with caster groups against friendly archers; sheet in
`output/projectile_vfx/all_first_pass.png` (local).

- **Good:** monster air bolts and the long crackling arcs; ice glints and frost around water elementals; fire
  missiles and the fire bolt tongue up close.
- **Fixed after the review:**
  - Poison Spray's mist filled the screen when a spray hit the party. The mist is now smaller, thinner and
    shorter-lived; Acid Burst's vapour likewise.
  - Fireballs thrown at the party blinded it (MM6 Hive, 2026-10-17): the trail's smoke dropped in front of the eyes
    covered the view as one dark sheet, and the impact's flame and smoke centred on the camera turned it white or
    dark. Two general rules now apply to every effect: sprites and particles fade out as they come to fill the view
    (`game/fx/EffectViewFade.h`: full strength up to 90 % of the view's half height, gone at twice, and within
    16 units of the camera), and an impact on the party plays 160 units in front of its eyes along the view, 40
    lower and at 0.6 scale (`PartyHit*` in `WorldFxSystem.cpp`); its loose particles and light stay where it struck.
  - Meteors smeared into yellow-green streaks over grass: additive orange over a green background turns yellow.
    The halo is smaller and the smoke body darker and denser. Large fire effects in general need a darker
    alpha-blended body under the additive flame to keep their hue over bright ground.
- **Not reviewed yet:** the body and mind group (Harm, Mind Blast, Sharpmetal, Blades, Dragon Breath), Light Bolt
  and Sunray up close, and Starburst. The captures are distant and depend on monsters choosing to cast; a debug
  command to fire a chosen projectile from a chosen point would make this review much faster.
- **Unrelated:** captures taken after another session rebuilt the game with in-progress water changes show the sea
  in solid magenta; that is not from the projectile effects.

## 9. Second round: impacts, variants and the rest (2026-10-11)

- **Impacts** for every bound projectile, built from flashes (glow, flares, rays, rings) and bursts (embers,
  droplets, glints, wisps, debris), with Unity Labs flipbooks where the school has volume:

  | Impact | Used by |
  |---|---|
  | `fire_small` | Fire Bolt, monster fire missiles, living flame |
  | `fireball` | Fireball, Dragon Breath and Flame Blast, dragon fire |
  | `meteor`, `incinerate` (on the target), `fire_spike`, `dark_fire`, `fire_arrow`, `lava_splash` | their spells and missiles |
  | `air_small`, `lightning`, `starburst` | air missiles and Sparks, Lightning Bolt and storm breath, Starburst |
  | `energy_burst`, `arcane_burst`, `blaster` | energy breath, arcane bolt, Blaster and robots |
  | `water_small`, `ice`, `ice_shard`, `poison`, `acid` | water missiles, Ice Bolt and frost breath, Ice Blast, Poison Spray, Acid Burst |
  | `earth_small`, `rock`, `death_blossom`, `blades` | earth missiles, Rock Blast, Death Blossom, Blades and Sharpmetal |
  | `body`, `harm` (on the target), `flying_fist`, `mind`, `mind_blast`, `spirit` | their missiles and spells |
  | `light_small`, `light_bolt`, `sunray`, `destroy_undead` (on the target) | light missiles and spells |
  | `dark_small`, `necrotic`, `toxic_cloud` | dark missiles, bone dragons, Toxic Cloud |

- **Monster variants** (flight, impact and light): `dragon_fire` for red dragons, drakes and the fire hydra;
  `lava_glob` for gogs and the fire beast; `living_flame` for fire elementals, efreets and genies; `frost_breath`
  for water dragons and wyrms; the Lightning Bolt flight for green dragons, lightning lizards and titans;
  `energy_breath` for crystal, gold and mega dragons, energy drakes and the chaos hydra; `arcane_bolt` for the
  Archmage, Warlock and Power Lich; `necrotic_breath` for bone dragons.
- **Smaller projectiles:** a faint streak behind arrows, a burning fire arrow, a crackling arc on each spark, and an
  armed Fire Spike (`fire_spike_mine`) that pulses and flickers while it waits on the ground.
- **Lights** for projectiles whose recipe had none: Dragon Breath, Darkfire Bolt, Toxic Cloud, Blaster and the
  variants.
- **Heads:** Picca flares replace the Kenney glints on ice, spirit and light missiles and the Sunray head.
- **Review tooling:** `projectile spell <id> party ahead 1000 10 4` fires a spell from just in front of the party at
  the ground ahead; `actor spawn <id> 1 x y z friendly` then `projectile actor last attack1 ahead 1100` makes a
  monster fire its missile. `--set debug.time_scale=0.25` (one-shot, never saved) runs the game in slow motion so
  menu-input tour captures catch fast projectiles.
- **In-game check** (sheet `output/projectile_vfx/second_round.png`, local): Fireball's flash, explosion and smoke,
  dragon fire, frost and storm breath, living flame, Sparks, Starburst, Rock Blast, Death Blossom, Toxic Cloud and the
  light, mind, acid and lightning impacts all draw. Fixes after the first look: impact sprites are lifted off the
  ground (they were half buried), the explosion flipbooks gained an additive fire core and fade their smoke sooner
  (they read as dull brown), and the bone dragons' grave smoke is lighter.
- **Still to review closely:** the arrows (too small to judge at capture distance), the lava glob, the energy breath
  and arcane bolt, and the water, ice and poison impacts, which the capture spot shows only small.
- **Review fixes (lasers and doubled heads):** the Kenney streak texture is vertical, so velocity-aligned streaks lay
  across the flight; it is now imported rotated. Velocity-aligned sprites follow their on-screen motion with
  perspective (they had used the direction flattened onto the screen, which turned streaks sideways for shots flying
  away from the camera). Ribbon heads follow the effect every frame, not only on the 60 Hz tick, so fast trails stay
  attached. The native sprite is hidden where the effect draws the whole head (Blaster and its dragon and mage
  variants, Dragon Breath, Darkfire Bolt, Mind Blast, Incinerate); Death Blossom lost its duplicate seed.
- **Flame Blast fix:** its projectile (object 12010, sprite `spell100`) was caught by Inferno's sprite token
  `spell10` before the Dragon Breath check, so it flew as an unbound, invisible Inferno with Inferno's small impact.
  Sprite tokens now match whole sprite names (a letter suffix is allowed), and a unit test checks that every spell's
  projectile object classifies to the same recipe as its spell id.

## 10. Third round: the spells that kept old sprites (2026-10-15)

An audit of spell visuals outside the projectile bindings found one spell still flying as its original sprite
(Deadly Swarm, `spell37` in flight and `spell37c` on impact), four that drew nothing on the struck creature (their
impact objects have no sprite: Spirit Lash, Prismatic Light, Souldrinker, Lifedrain), two with no world visual at all
(Mass Distortion; Armageddon had only a screen tint and camera shake) and three instant spells left on the classic
procedural burst (Implosion, Inferno, Immolation).

- **Recipes:** `DeadlySwarm`, `MassDistortion`, `SpiritLash`, `PrismaticLight`, `SoulDrinker`, `Lifedrain`,
  `ShrinkingRay` and `Armageddon` classify by spell id, object name or sprite. Like the arrows they are binding-only
  (`projectileRecipeIsBindingOnly`): no classic impact burst or impact light, so the classic style is unchanged.
- **Instant spells on creatures** (Implosion, Inferno, Mass Distortion, Spirit Lash, Prismatic Light, Souldrinker,
  Lifedrain and each Immolation tick) now pass the struck actor with their impact visual, so `impact_follows_target`
  works for them. Mass Distortion now spawns that visual (it had none).
- **`return_flight`** (new binding key): an effect that flies from each impact back to the casting party, bowing
  upwards and ending a little in front of its eyes. Souldrinker's pale souls and Lifedrain's blood use it. Party
  casts only.
- **Visual-only bolts:** a debuff applied at once whose recipe binds a `flight` (Shrinking Ray) now sends that flight
  from the party to the target at 6000 units per second; the debuff aura and the bound impact play when it arrives.
  The debuff itself still applies at the cast, as before. The original game fired Shrinking Ray as a real projectile
  (OpenEnroth `CastSpellInfo.cpp`), so making it one is a possible gameplay follow-up. Blind may have flown too
  (its object has a flying speed); it is unconfirmed and keeps its aura.
- **Armageddon:** while the ground shakes, a meteor strike (`openyamm:fx/impact/armageddon`: a burning meteor falls
  for half a second, then explodes) lands every 0.07 s at a random point 500–3000 units around the party; half a
  second before the detonation one strike falls on every creature within 6000 units (at most 40), so they land as
  the damage resolves. The strikes derive from the cast's saved state; no save data changed.
- **Effects:** flights `deadly_swarm` (a local-space cloud of insect specks with wing glints and stragglers; the
  native sprite is hidden), `mass_distortion` (monsters' cast), `shrinking_ray`, `soul_drain`, `life_drain`; impacts
  `deadly_swarm`, `mass_distortion`, `spirit_lash`, `prismatic_light`, `souldrinker`, `lifedrain`, `shrinking_ray`,
  `implosion`, `inferno`, `immolation`, `armageddon`. The generator gained local-space sheds (`local=True`), inward
  bursts (negative velocity) and `moving()` motion paths.
- **Review tooling:** `projectile cast <spell-id> [actor-index|nearest] [skill] [mastery]` makes the first party
  member cast any party spell at a creature as a wand would (fixed power, no mana or recovery).
- **Still classic:** Reanimate (its objects are missing). Inferno cannot be cast outdoors, so its impact was only
  checked by the effect tests.

## 11. Buff, heal and debuff auras (2026-10-15)

The procedural aura particles (soft alpha blobs, green for every buff, violet for most debuffs) and the party's
sparkles at its own position (inside the camera) are replaced in the enhanced style by named aura effects
(`openyamm:fx/aura/*`), bound in `assets_dev/engine/effects/spell_auras.yml` (`SpellAuraEffectBindings`): a default
per kind, and spells by id.

| Kind | Where it plays | Effects |
|---|---|---|
| `creature_debuff` | on the creature when a party debuff lands (follows it, sized to its height) | `stun` (halo and stars over the head), `slow` (sinking blue haze, closing ring), `paralyze` (golden lock, crackle), `turn_undead`, `charm` (rose stars), `berserk` (red pulses), `enslave` (violet rings at the head), `fear`, `blind` (black smoke at the head), `dark_grasp` (tendrils from the feet), `dispel` (shattering ring), default `debuff` |
| `creature_buff` | on a creature buffing or healing itself | `haste`, `shield` (dome ripple), `stoneskin`, `hammerhands`, `pain_reflection`, `creature_heal`, default `blessing` (golden column) |
| `party_buff` | 150 units in front of the party's eyes and 75 below, so it rises into the lower view | `party_ward` (resistances and protections), `party_utility` (light, sight, flight), `party_weapon` (Fire Aura, Vampiric Weapon), default `party_buff` (golden) |
| `heal` | the same place, for heals and cures | `heal` (green-gold glow, ring, soft stars and wisps) |

Dispel Magic on creatures now has an aura (it had no visual; the classic style still shows none). A debuff bolt's
impact stands in for its aura (Shrinking Ray). The portrait animations (`spell_fx.txt`) are unchanged.

## 12. World missiles and object bindings (2026-10-23)

A world can give its monsters missiles of its own, with their own objects, shield tiers and effects, without touching
MM's tokens, objects or bindings. Hesper is the first (design: `design/kreegan_world/PROJECTILES.md`; staged by
`level_generation/projects/hesper_stage/stage.py` from its `projectiles.yml`). A world without these files loads,
plays and renders exactly as before.

- **Missile tokens:** `worlds/<world>/monster_projectiles.yml` (schema `openyamm.monsterProjectiles.v1`), read by
  `GameDataLoader::loadMonsterProjectileTable` after `monster_projectiles.txt`
  (`MonsterProjectileTable::loadWorldYaml`):

  ```yaml
  schema: openyamm.monsterProjectiles.v1
  missiles:
    HesBolt: {object: 21000, impact_object: 556, tier: classic_blaster}   # tier optional
  ```

  A token must be new (MM's `Ener`, `Fire`... cannot be redefined), its object must lie in the world's
  `idRanges.objects`, `tier` is a shield tier (`physical`, `classic_blaster`, `kreegan_energy`, `spell`). A monster row
  naming a world token is ranged like one naming an engine token (`MonsterTable::acceptWorldMissileTokens`: the
  engine's token list in `isSupportedMonsterMissileToken` stays MM's).
- **Objects:** the world's `object_descriptors` table contribution (as MM9's), e.g. a copy of the laser object 555
  with its own name and speed.
- **Shield tier:** a token's `tier` rides on the projectile (`ResolvedProjectileDefinition::shieldTier`, indoor and
  outdoor, into `ProjectileState::shieldTier`); without one the tier follows the attack's damage type as before
  (`GameplayProjectileService::projectileShieldTier`). Not saved, like the party's tiers.
- **Effects by object:** `engine/effects/projectiles.yml` takes a top-level `objects` map, object name (object_list
  `Name`) to a binding with `flight`, `impact` (both required), `sprite`, `light`, `impact_follows_target` and
  `impact_light {rgb, radius}`. An object binding wins over the recipe and its monster variants, whatever the
  recipe (`ProjectileEffectBindings::find(recipe, picture, objectName)`; every `WorldFxSystem` lookup of a flying
  projectile, an impact or an actor's charge colour passes the object's name). `impact_light` replaces the recipe's
  impact light colour and radius; the recipe's duration stays. MM's file has no `objects`, so every MM lookup is as
  before. The Hesper stage appends its `objects` to its copy of the file and adds its effect library to its copy of
  `engine/effects/library.yml` (`imports`); a packaged world would want a world-level binding file (not done).
- **Not done:** the party's guns still fire the blaster object 555 (a per-item missile is designed in
  PROJECTILES.md); a missile's own fire and impact sounds (named in PROJECTILES.md; a shot plays its monster's
  attack sound).
- **Checks:** `./build/tests/openyamm_unit_tests --test-case='*world missile*,*MM*s monster missiles*,*by object
  name*,*staged Hesper missiles*'` (`tests/WorldMissileTests.cpp`; the last runs only against a built Hesper stage).
