# Fire projectiles: design proposal

Status: proposal agreed (2026-10-11); step 1 done (see section 7). First-pass flights for the other fire
projectiles (Fireball, Flame Blast and Dragon Breath, Incinerate, Meteor Shower, Fire Spike, Darkfire Bolt) are in
[PROJECTILE_VFX_ALL_PROPOSAL.md](../PROJECTILE_VFX_ALL_PROPOSAL.md), and so are the impacts, the dragon, lava glob and
living flame variants, fire arrows and the armed Fire Spike (its section 9). The original background is the fire
bolt test designs in
[the investigation](PROJECTILE_VFX_INVESTIGATION.md) (section 7) and the comparison of four fire bolt designs in
`output/projectile_vfx/fire_variants.png` (local, git-ignored).

**Goal:** one coherent fire family for the enhanced projectile style. It covers monsters' ordinary ranged fire attack
and every fire spell that flies. Each one reads as fire at a glance, and its size and intensity tell the player how
dangerous it is.

**Starting point:** the comet design (B in the comparison) is the base look. It is a round flame head that sheds a
dense tongue of flame, which shrinks and reddens over a faint dark smoke. It was the only one of the four designs
that read as real fire.

## 1. What flies

| Projectile | Recipe | Used by | Speed | Drawn now |
|---|---|---|---|---|
| Monster fire missile ("Fire") | `monster_fire_bolt` | 38 monsters: dragons, drakes, fire hydra, gogs, fire elementals, efreet, genie, liches, devils, clerics of the Sun, druids, gazers, unicorn | 4000 | test fire bolt (A) |
| Fire Bolt (spell 2) | `fire_bolt` | party; 17 monster casters | 4000 | test fire bolt (A) |
| Fireball (spell 6) | `fireball` | party; 19 monster casters | 4000 | classic bead trail |
| Flame Blast (spell 123, MM8 dragon breath) | none | dragon party member | 4000 | native sprite only |
| Dragon Breath (spell 97, MM7) | `dragon_breath` | party; 2 monster casters | 4000 | native sprite only |
| Incinerate (spell 11) | `incinerate` | party; 5 monster casters | 4000 | native sprite |
| Meteor Shower (spell 9) | `meteor_shower` | party; 3 monster casters | 1000 | native sprite, falling |
| Fire Spike (spell 7) | `fire_spike` | party | 1000, bounces, waits on the ground | native sprite |
| Darkfire Bolt (spell 103, MM8 dark elf) | `dark_fire_bolt` | party | 4000 | no trail |
| Fire arrows ("FireAr", "ArrowF") | none | 15 archer types (Fire Archer, centaurs, Regnan crossbowmen) | 4000 | native arrow sprite |

**Dragon Breath uses the Flame Blast design.** In MM7 Dragon Breath (spell 97) is Dark magic, described as "a cloud
of toxic vapors". The user chose to draw it as fire anyway, the same as Flame Blast: a gout of flame that explodes
like Fireball. Dragons' own fire breath is the ordinary monster fire missile above; section 4 gives dragons their own
version of it.

**Not projectiles:** Immolation (an aura around the party) and Inferno (hits everything in sight) never fly. They
need area and target effects, which I'd treat as separate work after the projectiles.

## 2. Shared design language

**Layers.** Every fire projectile is built from the same parts, in different amounts:

- **Core:** a white-yellow glow on the collision point. It's always the brightest thing, so the eye finds the
  projectile.
- **Head:** the animated fireball flipbook, round (not stretched), additive.
- **Flame tongue:** flame sprites shed behind the head, shrinking and reddening. This replaces the ribbon for fire.
- **Smoke:** alpha-blended smoke puffs under the flames. This is what keeps red and brown in the picture instead of
  everything adding up to flat yellow, the main fault of the current design.
- **Embers:** a few fast sparks that fly off and fall or rise.
- **Light:** the existing projectile light, tinted to match.
- **Impact:** a flash, a burst, embers and smoke, scaled to the projectile.

**Colour.** One gradient for the whole family: white-yellow core, orange body, red tail, then dark smoke. Variants
shift it, without breaking the order: hotter for magic, cooler and dirtier for monsters, inverted for Darkfire.

**The ladder.** Size, trail length and brightness rise with the danger, so that a player can tell a monster's spit
from a Fireball across the field. All values are relative to Fire Bolt = 1.

| Projectile | Head | Tongue | Smoke | Brightness | Character |
|---|---|---|---|---|---|
| Fire arrow | 0.3 | 0.3 | thin line | low | an arrow on fire |
| Monster fire missile | 0.8 | 0.8 | more | medium | rough spat flame |
| Fire Bolt | 1 | 1 | light | high | clean, fast magic flame |
| Fireball | 1.6 | 1.2 | heavy, lingering | high | a big churning ball |
| Flame Blast / dragon breath | 1.4 | 1.6, widening | heavy | high | a gout of flame |
| Incinerate | 1.3 | 1.5 | little | very high, white | a lance of white fire |
| Meteor | 2 | 2, upward | very heavy | high | a burning rock falling |

## 3. Spells

### Fire Bolt

- **Look:** the comet design as captured. A round head, a dense flame tongue about 500 units long, faint smoke and
  a few embers.
- **Fix first:** at the far end of the tail the flame puffs separate into blobs. Emitting by distance instead of by
  time fixes it at every speed (section 5).
- **Impact:** a small flash and burst of flame with embers. A bigger, fuller version of the current burst.

### Fireball

- **Look:** clearly bigger and heavier than Fire Bolt. Two fireball flipbooks at different sizes and frame offsets
  make the head churn. The flame tongue is shorter in proportion, and a thick dark smoke trail hangs in the air for
  about half a second after it passes. The tail is reddened, with more embers.
- **Impact:** the main event. A bright flash, then a fast expanding sphere of flame (the existing sphere burst,
  upgraded), a ground ring, embers flung outward and a smoke cloud that rises and lingers. The light flares for the
  blast.

### Flame Blast and Dragon Breath

- **Look:** a gout of flame rather than a ball. A thick stream of flame puffs that widen as they fly and fall
  behind, so it reads as breathed fire. A short bright head, a long turbulent body and heavy smoke.
- **Impact:** like Fireball, since it explodes the same way, with more flame and less flash.
- Dragon Breath (MM7, spell 97) uses the same flight and impact.

### Incinerate

- **Look:** the strongest single-target spell, so the hottest look. A white core and white-yellow head, a narrow,
  intense tongue with a white centre (a hot core ribbon inside it works here), and flame wisps peeling off. Almost
  no smoke: it burns clean. The light is bright and white-orange.
- **Impact:** the target is engulfed. A short column of fire rises from the target and burns for about half a second.

### Meteor Shower

- **Look:** keep the native meteor sprite as the rock, and wrap it in fire. A large flame envelope trails upward
  behind the rock as it falls, with a very heavy smoke trail and sparks streaming off.
- **Impact:** a heavy ground burst. Flame, dust thrown up, burning debris arcing out, and a smoke cloud. The
  existing radial burst becomes the base.

### Fire Spike

- **Look in flight:** slow and bouncing. A small spiky white-yellow star with crackling sparks and a short trail.
- **Look on the ground:** an armed mine. A pulsing glow, small flickering flames and sparks rising slowly. A player
  should be able to see where it lies.
- **Impact:** a sharp radial burst of flame spikes.
- Needs effects to continue after the projectile settles (section 5).

### Darkfire Bolt (MM8 dark elf)

- **Look:** the fire bolt shape with inverted colour. An alpha-blended black-violet core and body, with an orange
  and magenta burning rim and dark smoke. It is fire that eats light.
- **Impact:** a dark burst with an orange rim.

## 4. Monsters' ordinary fire attack

38 monster types use the same missile, from a Druid to a Great Wyrm. One shared look would make a dragon's breath
the same as a gogling's spit. Proposal: one default and a few family variants, chosen by monster.

| Variant | Monsters | Look |
|---|---|---|
| **Default: spat flame** | liches, devils, clerics of the Sun, druids, monks, warlocks, gazers, terrible eye, unicorn | the Fire Bolt design, smaller and rougher: more smoke, a dirtier orange, a less bright core |
| **Dragon breath** | Dragon, Dragon Flightleader, Great Wyrm, Red Dragon, Flame Drake, Fire Hydra, Fire Lizard | the Flame Blast design, at the dragon's scale: a big gout of flame |
| **Lava glob** | Gogling, Gog, Magog, Smoke/Ember/Fire Gog, Fire Beast | a dark crusted core with glowing cracks, molten drips falling under gravity, black smoke |
| **Living flame** | Fire Elemental, Fire Spirit, Warden of Fire, Guardian of Flame, Efreet, Genie | pure flame with no smoke and no rock, flickering and bright, with many embers |

Monsters casting real spells (Fire Bolt, Fireball and so on) use the spell designs from section 3, so a
monster's Fireball looks like the party's.

## 5. Engine work needed

Most of this is authoring in `library.yml` and `projectiles.yml`. The engine additions are small:

1. **Emit by distance.** An emitter option that sheds particles every N world units along the path, rather than
   every N seconds, so tails stay continuous at any speed. This is the fix for the blobbing.
2. **Per-monster flights.** `projectiles.yml` can bind a flight effect for a list of monster ids. Projectiles
   already carry `sourceMonsterId`. Without this, all 38 monsters share one look.
3. **Impact effects.** `projectiles.yml` binds an `impact:` effect in place of the recipe's burst, so that impacts
   can be authored like flights.
4. **Keep the sprite.** A flight option to keep the native billboard (meteor rock, fire spike, arrow) under the
   effect, rather than hiding it.
5. **On-ground state.** A flight option for an effect while the projectile lies settled, for Fire Spike.
6. **Particle spin (optional).** A random start rotation and spin for particles, so that flame puffs repeat less.
7. **Gravity (optional).** Already possible as downward wind; a real gravity term would make lava drips and debris
   arc properly.

None of this changes gameplay. Projectile speed, collision and damage stay as they are; `video.projectile_style=classic`
keeps the original look throughout.

## 6. Order of work

1. **Fire Bolt and monster missile:** emit by distance, the comet as Fire Bolt, the spat-flame default for
   monsters. Remove the three unused test designs.
2. **Fireball:** flight and the impact binding, with its full explosion.
3. **Per-monster variants:** dragon breath, lava glob and living flame, plus Flame Blast and the Dragon Breath spell.
4. **Incinerate, Meteor Shower, Fire Spike, Darkfire Bolt and fire arrows.**
5. **Later:** Immolation and Inferno as area effects.

Each step ends with captures of the new designs next to classic, from close and far, in the same New Sorpigal setup
as the fire bolt test. The dragon variants need a dragon map.

## 7. Step 1 (done)

- **Emit by distance:** sprite systems take `emission_distance` (world units). Emissions land on their own points
  along the path travelled in each step, and particles placed earlier on the path start older, so a tail is
  continuous and evenly graded at any speed. A jump of more than 64 spacings in one step restarts the trail. Local
  particle space is rejected for distance emitters.
- **Fire Bolt:** `openyamm:fx/projectile/fire_bolt` is the comet design, with flame and smoke emitted by distance.
- **Monster fire missile:** `openyamm:fx/projectile/monster_fire_bolt`, the spat-flame default for all 38 monsters
  until per-monster variants exist.
- The three test designs are removed. The browser preview skips distance emitters, like ribbons.
- Captures: `output/projectile_vfx/fire_step1.png` (local), with Ember Gogs (monster missile and Fire Bolt) and a
  Regnan Archmage against friendly archers in New Sorpigal.
- Checks: the normal build, and the full unit suite (1601 cases).
