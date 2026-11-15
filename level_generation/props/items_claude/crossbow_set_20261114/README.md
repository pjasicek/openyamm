# Crossbow set for the solo run's first-person arms (2026-11-14)

A crossbow held with both hands like a crossbow, with its own clips: carried at the right hip, raised to the cheek,
loosed with a short sharp recoil, and spanned again before the next shot. Engine side and rules:
devdocs/solo_action/WEAPONS.md "Crossbow set (2026-11-14)". Before this, the crossbow template hung rigidly on the
left fist and played the bow's clips (drawing the bow read as winding the crossbow).

The arms are Oblivion's (reference/oblivion_poc/README.md): private, never committed. Only this README and `scripts/`
are tracked; `ingame/` is git-ignored by the level_generation rules. The crossbow template is our art, built in
[view_model_weapons_20261114](../view_model_weapons_20261114/README.md).

## Which hand holds it

The right hand: the crossbow hangs on the right hand's `Weapon` node, the wrist of the stock (its laced grip) through
the fist, the hand cradling it from below and behind (the elbow down). While spanning the cord and while the left hand
casts, only the right hand holds it, so it cannot hang on the left hand's `Torch` node as before. The template is
placed there rigidly by the weapons project's `kinds.py` `mount` (grip point, a roll of -115 degrees about the stock,
no tilt; `weapon_from_build`), which `export_mesh.py` applies to all four tier skins and which the clip bake reads, so
the template and the clips cannot disagree. The left fist closes on the short vertical foregrip under the fore-end,
exactly where the crossbow was built in the Torch frame: in every two-handed pose the left hand's Torch frame is the
crossbow's build frame. The engine measures that relation once from `crossbowidle` (`m_crossbowGrip`) to carry our
ground crossbows (held.yml's Crossbow mount grips them in the Torch frame) on the Weapon node too.

## Baked clips

`scripts/bake_crossbow_clips.py <in.glb> <in.textkeys.json> <out.glb> <out.textkeys.json>` (numpy only, about 2 s)
appends 17 clips to an arms GLB that already holds the dual-wield clips; every existing clip, mesh, skin and texture is
copied byte for byte. It refuses input that already holds crossbow clips. `scripts/rebake_arms.sh [race ...]` bakes
every race from the pristine copies (`reference/oblivion_poc/glb/pristine_predual/`): the dual clips and the crossbow
set into scratch files, then (since the same day) the pole set ([pole_set_20261114](../pole_set_20261114/README.md))
into the arms in place (`reference/oblivion_poc/glb/arms_hd_<race>.glb`), and installs the human arms as the engine's
(`tools/install_model.py --view-model --name arms.glb`: the source into `assets_source/engine/view_model/`, the cooked
copy and the text keys into `assets_dev/engine/view_model/`). Run it again after changing any of the three bakes.

How a clip is made: per frame, the crossbow's place relative to the eye (Camera01) comes from keyframed poses (the
stock's wrist position, yaw, pitch, roll, eased per segment), and both arms are solved onto it.

- **Arms:** a two-bone solve (upper arm, forearm as a hinge about its Z, the elbow toward a pole), the hand turned onto
  its target, the forearm twist bone taking the hand's twist about the forearm (as Oblivion's clips do), fingers as in
  a gripping hold (right: `onehandidle`; left: the bow's riser hold, `bowattack` at 1.37 s).
- **Body:** spine, neck, Camera01 and clavicles from a bow clip (`bowidle`, the walks from the bow's walks, the casts
  from Oblivion's one-handed casts). The chest (Spine2) turns 18-25 degrees left shoulder forward, as a shooter stands;
  the eye does not follow it (the engine's eye follows only Camera01's position). Without it the left hand could not
  reach the foregrip.
- **Walks:** the idle pose carried by the bow walk's motion of the left hand relative to the eye (its Torch node), so
  the crossbow bobs as the bow does.

| Clip | Duration | Keys | What it shows |
|---|---|---|---|
| `crossbowidle` | 3.0 s | | At the right hip, the bolt forward and slightly down, both hands on it; three breaths of sway |
| `crossbowforward`, `-backward`, `-left`, `-right` | 1.0, 1.0, 0.87, 0.87 s | the bow's | The idle carried by the bow walk |
| `crossbowfastforward`, `-fastbackward`, `-fastleft`, `-fastright` | 0.87, 0.87, 0.8, 0.8 s | the bow's | The same, running |
| `crossbowequip` | 0.8 s | Attach 0.1 | Up from below the screen into the idle |
| `crossbowunequip` | 0.67 s | Detach 0.5 | Down out of view |
| `crossbowattack` | 1.55 s | Release 0.4, a:R 1.433 | Raised to the cheek (0.25 s), loosed, a 0.06 s kick (nose up 7 degrees, back into the shoulder) and settling; then the span: nose down and across, the left hand from the fore-end onto the cord at the prod, drawn back to the nut, back to the fore-end, up into the idle by 1.433 s |
| `crossbowblockidle` | 1.3 s | | Raised across the face, the stock level |
| `crossbowblockhit` | 0.3 s | Blend: 0 | A jolt toward the eye |
| `crossbowcastself`, `crossbowcasttarget` | 1.3, 0.9 s | Oblivion's (Hit) | The left arm casts as in `onehandcast*`, the right holds the crossbow low on the right |

**Cadence:** the engine fits a shot to the member's recovery by the clip's span (its chain key when it has one) and
starts the next queued shot there: for `crossbowattack` the a:R key at 1.433 s, the bow's Release in `bowattack`, so a
crossbow keeps exactly the bow's cadence at any recovery (one shot per recovery, at most 3.5 times Oblivion's pace:
0.41 s). The bolt leaves at Release, 0.4 s into the clip (0.11-0.4 s after the press).

## Gates

The bake prints, per clip, how far each wrist stays from its target where the arm cannot reach (units, and when).
Final bake (every race: they share one skeleton): 0.0 for the right hand everywhere; the left at most 0.61 (1.2 s into
`crossbowattack`, the hand back on the fore-end with the crossbow still tipped), 0.54 in the runs, 0.1-0.3 in the
idle, walks, equip and unequip, 0.0 in the block and the casts.

`scripts/preview.py <arms.glb> <crossbow.glb> <out.png> <clip>@<seconds>[@side|@close] ...`: a software raster of the
skinned arms and the crossbow from the engine's eye (60 degree field, 16:9, crosshair), or from the right side to check
the hands on the stock. Quick enough to tune poses between in-game runs.

## In-game checks

`scripts/run_ingame.sh <outdoor|indoor> [tag] ["1 2 3 4"]`: MAW solo run, 1600x900; `viewmodel equip 0 0 63` empties
the new knight's hands and puts the Hunting Crossbow in the bow slot (the real kit path: an empty main hand draws the
bow slot, and its held.yml kind picks the crossbow set). Per tier (`viewmodel tier`): idle, then held poses of
`crossbowattack`: raise 0.15, aim 0.38, the recoil frame 0.46 (`swing`), mid-span 0.95 (`reload`); then our ground
model (`viewmodel weapons ours`). `ARMS=<arms.glb>` holds arms from disk (`[debug] view_model_path`, the weapons
beside them) for tuning before installing. `LIVE=1` presses Attack four times with `viewmodel trace on`.

Live play (`LIVE=1`, MAW solo cleric, ranged recovery 0.27 s): `swing crossbowattack rate 3.5 recovery 0.266667 hit
at +0.114286`, each blow at clip 0.40-0.41 (the Release key), four presses, four shots, the bolt leaving toward the
crosshair while the crossbow is tipped for the span (`ingame/live2/`, slowed to a quarter).

Final captures: `ingame/final/{outdoor,indoor}/` (engine arms, all four tiers and our ground model); converted for the
skins viewer as `w_crossbow_{outdoor,indoor}_{t1..t4,ours}_{idle,swing,swing2}.jpg` (idle, the recoil frame at
0.46 s, mid-span at 0.95 s; 1280x720, quality 82).

Verdict at full size: the crossbow reads as a crossbow carried in two hands at idle (the left fist under the fore-end,
the right cradling the wrist below the frame), the aim brings the prod across the view with the bolt under the
crosshair, the recoil kicks the nose up, and the span shows the left hand drawing back along the stock. Weak points: the
right fingers sink a little into the thick wrist of the stock; the span happens low and partly under the right
forearm, because the eye cannot look down at a crossbow tipped toward the floor; the cord and the bolt are static (a
bolt stays nocked after the shot); our ground crossbows (`viewmodel weapons ours`) follow the hands but keep their
wide prods and short stocks.
