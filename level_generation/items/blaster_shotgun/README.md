# Blaster Shotgun (item 2201)

An engine-authored test weapon modelled on the MM6 Blaster Rifle (item 1667, `raygun2`): seven bolts fanned across
Ice Blast's 60° arc, each rolling half the rifle's damage, with a longer recovery.

| Field | Value |
|---|---|
| Item | `items.txt` row 2201, pic `blastsg`, Weapon / Blaster, 3d4+6 per bolt (9–18; rifle 5d5+12 is 17–37) |
| Behaviour | `content_flags` = `ScatterBlaster` (constants in `game/gameplay/GameMechanics.cpp`): 7 bolts, π/3 arc, +20 recovery ticks (Blaster base 30) |
| Projectile | the stock blaster bolt (object 555) with per-bolt damage and hit rolls |
| Sound | `shoot blaster scatter01` (sound 44587, `SoundId::ShootBlasterScatter`) |
| Inventory icon | `assets_dev/engine/icons_x2/blastsg.png`, 124x372 (2x6 cells), muzzle up like `raygun2` |
| Ground sprite | object 417 → sprite 23990 in `engine/rendering/sprite_frame_data_engine_items.yml` → `engine/decorations_x2/blastsg_p547.png` (272x72) |

The sprite group lives in `sprite_frame_data_engine_items.yml`, not the common table: every outdoor lighting bake
depends on `sprite_frame_data_common.yml`, and appending to it would make them all stale.

## Art

`refs/style_reference.png` (the restored MM6 rifle, pistol and MM8 ground rifle on a magenta matte) and
`refs/prompt_master.txt` went to two Codex `image_gen` workers (`raw/worker_*.txt`). Variant B (`raw/master_b.png`,
seven splayed emitter tubes) was chosen over A (five tubes). It was keyed from the matte with despill and a one-pixel
alpha erosion (`review/master_cutout.png`), then resized in premultiplied alpha: rotated 90° counter-clockwise for the
icon, and squashed to 80 % height for the ground sprite. `review/compare.png` shows both beside the MM6 rifle.
There is no native source, so the art is not part of the `decorations_x2/manifest.json` restoration record.

## Sound

`make_sound.py <output.wav>` rebuilds the WAV deterministically from `shoot blaster01.wav`. It layers seven
pitch-spread, staggered copies (the volley), a 130→42 Hz thump with a filtered noise crack, a falling whine, and a
two-click recharge clack at 0.56 and 0.66 s for the longer recovery. The output is 16-bit mono PCM, 44.1 kHz, 0.74 s.

## Testing

`tests/InventoryEquipRegressionTests.cpp` checks the profile against the rifle and the shared fan helper
(`GameMechanics::projectileFanYawOffsetRadians`, also used by Sparks, Poison Spray, Ice Blast and Shrapmetal).
In game: `item give 2201` from the console, on a member with the Blaster skill.
