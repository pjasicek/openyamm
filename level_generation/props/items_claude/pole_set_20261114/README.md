# Pole set for the solo run's first-person arms (2026-11-14)

Spears, tridents, halberds and poleaxes held with both hands with their own clips: carried low at the right hip with
the head up and right of the crosshair, jabbed along the view, swept across it and chopped down through it. Engine side
and rules: devdocs/solo_action/WEAPONS.md "Pole set (2026-11-14)". Before this, poles played the two-handed (claymore)
clips, which hold a pole upright: at idle only the shaft was on screen and the head above the frame, and in the swings
the head was small or off screen, so the tier skins' heads (where each tier's ornament is) were never seen.

The arms are Oblivion's (reference/oblivion_poc/README.md): private, never committed. Only this README and `scripts/`
are tracked; `ingame/` is git-ignored by the level_generation rules. The pole templates (`w_spear`, `w_trident`,
`w_halberd`) are our art, built in [view_model_weapons_20261114](../view_model_weapons_20261114/README.md) in the right
hand's Weapon node (the palm at the origin, the head along +Y, the edge's width along X, the flat along Z); nothing
about them changes here.

## Hold

The right fist holds the pole on its Weapon node (the template hangs there), behind and low at the right hip, off the
bottom of the screen at idle. The left fist closes on the shaft 22 units further up (its Torch frame, the bow hold's
riser frame, on the shaft with the thumb toward the head), visible at the bottom right. The shaft points forward, up
and a little in, so the head sits up and right of the crosshair at about 0.8-1.1 m, turned (roll 125°) so its flat
half faces the eye and the halberd's axe blade stands up and to the right. The chest is turned 22° left shoulder
forward, as a spearman stands; without it the left hand cannot reach that far up the shaft.

Held long instead of shortened: the head can be in view only if the shaft crosses the view. With the pole along the
view (the first try: the head 12° off the view ray) the halberd blade was seen edge on and the spear head a sliver;
held more upright and in (about 25° off the view ray) the head reads at a third of the screen's height.

## Baked clips

`scripts/bake_pole_clips.py <in.glb> <in.textkeys.json> <out.glb> <out.textkeys.json>` (numpy only, about 15 s with
its gates) appends 24 clips to an arms GLB that already holds the dual-wield and crossbow clips; every existing clip,
mesh, skin and texture is copied byte for byte. It refuses input that already holds pole clips.
`../crossbow_set_20261114/scripts/rebake_arms.sh [race ...]` bakes every race from the pristine copies
(`reference/oblivion_poc/glb/pristine_predual/`): the dual clips and the crossbow set into scratch files, then the pole
set into the arms in place (`reference/oblivion_poc/glb/arms_hd_<race>.glb`), and installs the human arms as the engine's
(`tools/install_model.py --view-model --name arms.glb`: the source into `assets_source/engine/view_model/`, the cooked
copy and the text keys into `assets_dev/engine/view_model/`). Run it again after changing any of the three bakes; about 1.5 minutes
a race.

How a clip is made, as the crossbow set's: per frame, the pole's place relative to the eye (Camera01) comes from
keyframed poses (the right palm's position; the shaft's yaw, pitch and roll; how far up the shaft the left fist is;
the chest's turn), eased per segment, and both arms are solved onto it with the crossbow bake's `Rig` (a two-bone
solve, the hand turned onto its target, the forearm twist bone taking the hand's twist, gripping fingers: right from
`onehandidle`, left from the bow's riser hold). The left fist's turn about the shaft is kept apart from the pole's
roll (`grip`), so the shaft turns in the left hand when a sweep or chop turns the head's edge forward. The body comes
from `twohandidle` (the casts: Oblivion's one-handed casts, whose left arm casts); the walks carry the idle by
`twohand<walk>`'s motion of the Weapon node relative to the eye, at 60 % (a long pole wags at the sword's full sway).
The attacks are baked at 60 frames a second, the rest at 30: the engine interpolates each bone on its own, which in a
fast swing opens the two-handed loop between frames (the left fist up to 1.8 units off the shaft at 30).

Rolls: 125 is the carry (the flat toward the eye); 0 turns the halberd's axe blade (-X) down, so the chops lead with it;
270 and 90 lead the sweeps to the left and to the right with the edge.

| Clip | Duration | Keys | What it shows |
|---|---|---|---|
| `poleidle` | 3.0 s | | Low at the right hip, the head up and right of the crosshair; three breaths of sway |
| `poleforward`, `-backward`, `-left`, `-right` | 1.0, 1.0, 0.87, 0.87 s | the two-handed walks' | The idle carried by the walk |
| `polefastforward`, `-fastbackward`, `-fastleft`, `-fastright` | 0.87, 0.87, 0.8, 0.8 s | the runs' | The same, running |
| `poleequip` | 0.8 s | Attach 0.1 | Swung up from below the view (head down) into the idle, the left fist closing on the shaft |
| `poleunequip` | 0.67 s | Detach 0.5 | Back down |
| `poleattackright` | 0.867 s | Hit 0.333, a:L 0.433 | The jab: drawn back a little, driven along the view until the point is on the crosshair at the Hit, the shaft sliding through the left fist |
| `poleattackleft` | 0.833 s | Hit 0.2, a:R 0.367 | A second, higher jab |
| `poleattackright_chop` | 0.9 s | Hit 0.333, a:L 0.467 | The sweep: the head wound out to the right, swept through the crosshair right to left (edge leading), carried through to the left |
| `poleattackleft_chop` | 0.933 s | Hit 0.233, a:R 0.4 | The chop: raised up and to the right, brought down through the crosshair (the axe blade leading) |
| `poleattackpower` | 1.6 s | Hit 0.633 | The lunge: drawn far back (the head close and big), driven out with the right shoulder until the point is on the crosshair |
| `poleattackforwardpower` | 1.567 s | Hit 0.633 | The same lunge, a little further and lower (Charge plays it) |
| `poleattackbackpower` | 1.5 s | Hit 0.6 | A big overhead chop |
| `poleattackleftpower` | 1.433 s | Hit 0.6 | A big sweep right to left (Cleave and Whirlwind's first) |
| `poleattackrightpower` | 1.7 s | Hit 0.9 | A big sweep left to right (Whirlwind's second) |
| `poleblockidle` | 1.3 s | | The shaft raised across the face, the head off to the left |
| `poleblockhit` | 0.3 s | Blend: 0 | A jolt toward the eye |
| `polecastself`, `polecasttarget` | 1.3, 0.9 s | Oblivion's (Hit) | The left arm casts as in `onehandcast*`, the right holds the pole lower on the right |

**Timing:** every attack carries the Hit and chain keys (a:L, a:R) of the two-handed clip of the same name, so the
engine fits it to the member's recovery by the same span (the chain key, or the Hit plus 0.3 s for the power attacks)
and lands the blow at the Hit exactly as it did with the claymore clips: the same cadence, and the Hit is the contact
frame (the point on the crosshair in a jab or lunge, the head crossing the crosshair in a sweep or chop). The combo
(`comboAction`: right, left, right_chop, left_chop, then a power attack by the movement) therefore plays jab, jab,
sweep, chop, lunge (standing).

## Gates

The bake prints, per clip, how far each wrist stays from its target where the arm cannot reach, and measures the
written clips four times a frame: the left fist's distance from the shaft's axis (its Torch frame's origin; the right
fist cannot leave the pole, which hangs on it), the closest approach of the shaft and of both forearms to the eye, and
for the idle where the heads of the three templates (head start and tip) fall on screen.

Final bake (every race: they share one skeleton): the right wrist 0.0 everywhere. The left fist sits 0.79 off the axis
at rest (inside the shaft's 1.25 radius: the fist closes round it), at most 1.42 in the sweep at speed and 0.8-1.06
in every other attack; in the equip and unequip 1.9 while both hands are below the screen (the left fist closes on the
shaft as it rises). Wrist misses: 1.45 and 1.27 in the jabs and 1.29-1.33 in the lunges at the Hit (both arms long; the
fist stays within 0.92 of the axis there), 3.2 in the equip and unequip below the screen, 0.0 elsewhere. Eye clearance
(the shaft from butt to tip and both forearms) at least 13.9 units, in the sweeps; nothing reaches the near plane. The
idle's heads on screen (head start and tip of all three templates, through the breathing): x 0.18..0.43, y
-0.38..0.46 in normalised device coordinates. The casts take the left hand off the shaft by design.

`../crossbow_set_20261114/scripts/preview.py <arms.glb> <w_spear|w_trident|w_halberd.glb> <out.png> <clip>@<s>[@side]`
draws any Weapon-node template on the arms (it was written for the crossbow, which hangs there too): quick enough to
tune poses between in-game runs.

## In-game checks

`scripts/run_ingame.sh <outdoor|indoor> [tag] ["1 2 3 4"] ["spear trident halberd"]`: MAW solo run, 1600x900, MM6 New
Sorpigal (oute3) and Corlagon's dungeon (6d05). `viewmodel equip <id> 0` puts a real item in the knight's hand (the
real kit path: the held.yml kind picks the pole set, held_tiers.yml the template): Steel Spear (42), Titanic Trident
(1643), Light Poleaxe (1630: the halberd template). Per tier (`viewmodel tier`): idle, then held poses at each attack's
Hit: the jab (`swing`, `poleattackright` 0.333), the sweep (`poleattackright_chop` 0.333), the chop
(`poleattackleft_chop` 0.233) and the lunge (`poleattackpower` 0.633). `ARMS=<arms.glb>` holds arms from disk.
`LIVE=1` presses Attack five times (one round of the combo) with `viewmodel trace on`.

Live play (`ingame/live`, and ten presses half a second apart through `action: attack`, Light Poleaxe, MAW solo
cleric, melee recovery 0.47 s): `swing poleattackright rate 1 ... hit at +0.333333`, then `poleattackleft`,
`poleattackright_chop`, `poleattackleft_chop`, `poleattackpower rate 2 ... hit at +0.316667`, and again: one full
round of the combo, each blow reported within a frame of its Hit (clip 0.340, 0.205, 0.349, 0.244, 0.658 at rate 2;
the trace's `blow (clip ...)`).

Final captures: `ingame/v2/<kind>_<outdoor|indoor>/t<1..4>_<idle|swing|sweep|chop|lunge>.png` (the human arms;
every race shares the clips). Converted for the skins viewer as `w_{spear,trident,halberd}_{outdoor,indoor}_t{1..4}_
{idle,swing}.jpg` (idle and the jab at its Hit as `swing`; staged in the weapons project's `ingame/pole_v1/` for its
`to_viewer.py`).

Verdict at full size: the idle now shows each head the whole time, up and right of the crosshair and clear of the
minimap, big enough to read the tier: the halberd's axe blade and beak with the gilded langets (tier 3) or the cyan
runes (tier 4), the trident's three prongs and set stone, the spear's leaf point and lugs; the shaft's wrap and
filigree run down to the left fist at the bottom right. The jabs and lunges read as thrusts (the point driven onto the
crosshair, the head small at the Hit because it is a metre away along the view), the sweep as a sweep (the head
crossing the crosshair edge first, the halberd's blade leading), the chop as a downward blow. Weak points: the spear's
narrow head is the smallest of the three at idle (about 60 pixels tall at 900); the chop shows the halberd's blade edge
on at its Hit (the eye looks along the shaft from behind it); the right hand is never on screen at idle (it holds the
butt end at the hip, below the frame); in 6d05 tiers 1-3 go dark as every template does there.
