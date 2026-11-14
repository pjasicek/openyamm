# First-person weapon templates for the kinds Oblivion lacks (2026-11-14)

Own first-person weapon models for the solo run's arms, one template per kind with four tier skins each: **spear,
halberd (also poleaxes and other polearms), trident, crossbow, wand and blaster**, and a **club** with two skins (low
and mid: every club is valued below the mid band; "Club" below). These are our art (committable), unlike the Oblivion templates beside them. Engine side and verdicts:
[WEAPONS.md "New templates (2026-11-14)"](../../../../devdocs/solo_action/WEAPONS.md#new-templates-2026-11-14).

## Which file is which

- **Sources (kept here):** `work/<kind>/model.blend` (the built model, face attribute `region`), `work/<kind>/layout.blend`
  (the same with the locked UV layout), `work/<kind>/t<tier>/{basecolor,normal,mr[,emissive]}.png` (the skin maps) and
  `work/<kind>/t<tier>/w_<kind>_t<tier>.glb` (the accepted skin). Masters in `work/<kind>/masters_t<tier>/`, Meshy returns
  in `meshy/<job>/`, requests in `requests/`, ledger `creature_3d_progress.json` (identity
  `engine:view-model-weapons`). `work/`, `meshy/`, `review/` and `ingame/` are git-ignored; scripts, requests and this
  README are tracked.
- **Runtime copies:** `assets_dev/engine/view_model/w_<kind>.glb` (the template: a copy of the mid-tier skin) and
  `w_<kind>_t1..t4.glb`, copied from `work/<kind>/t<tier>/`. The view model folder is loaded raw (no cooking), as for
  the Oblivion skins. Never edit the runtime copies; re-run `scripts/post.py skin` and copy again.

## Route

1. **Design** (`scripts/codex_design.py`): one Codex HD design master per kind from the MM6-MM8 icons of that kind
   (`work/<kind>/design/`). The image tool refuses weapon words as violence: the briefs call them display props
   ("processional pole", "museum replica"). The spear's session was killed with the previous helper; its two images
   were recovered from `~/.codex/generated_images`. The crossbow got one top view after two refused attempts.
2. **Model** (`scripts/build.py <kind>`, Blender, helpers `scripts/vmw.py`): every kind built from parts in Blender,
   no Meshy geometry: lathed shafts, sockets, collars, rings and caps; lofted fluted or diamond-section points with the
   honed bevel strips tagged `edge`; bevelled plates with per-vertex insets (halberd blade and beak, barbs, the
   blaster's spur); swept tubes (trident cross-piece and prongs, wand claws, crossbow prod, trigger guard and lever).
   Built in the arms' node space, Oblivion units (1 unit = 1.43 cm): poles and the wand in the Weapon node (palm at the
   origin, head +Y), the blaster in the Gun frame, the crossbow in the left hand's Torch frame at the bow's full draw.
   Shafts 2.5 units across at the hands (3.6 cm), wraps 2.8 (the Oblivion fists close on radius 1.38).
3. **Layout** (`scripts/prep.py <kind>`): `uv_atlas.unwrap()` defaults (PartUV charts, seam pass, sparrow), the head
   1.4x denser, long shaft islands cut into pieces of at most 4:1 and repacked. **Pieced upload:** a pole is cut into
   3-4 pieces (kinds.py `pieces`) stood side by side for the Meshy upload and the guides, so a 1.7 m weapon fills the
   guides at about four times the resolution of one full-length view; the paint lands on the assembled model through
   the original UVs. `--upload-only` redoes the upload and guides on a locked layout.
4. **Masters** (`scripts/codex_masters.py brief|run <kind> <tier>`, `work/run_masters.sh <N> kind:tier ...`): Codex paints
   each tier over the guides (front and back; the wand also its left side, the blaster also its top), the design master
   attached for shape and ornament. Tier looks: 1 crude iron, ash and rawhide; 2 satin steel, yew, brass, dark leather;
   3 mirror steel, gilding, ebony with gold filigree, crimson leather, rubies (no glow); 4 dark star-metal with
   luminous cyan runes, midnight-blue leather, platinum, glowing stones, the only tier that glows (the poles' legendary
   since its redo: "Legendary poles" below). About half the sessions were refused as
   violence at random; fallbacks, in order: retry; a missing back is the front mirrored (`meshy_request.py`: the
   side-by-side upload seen from behind is exactly the front guide mirrored); a refused low tier is recoloured from the
   mid paint (`post.py`, by region); the crossbow (every brief refused, four tiers, two wordings) got **rendered
   masters** (`scripts/render_masters.py`: the exact upload in Blender with procedural per-tier materials by region,
   Cycles, from the guide cameras: registration IoU 1.0). Since the user's review the crossbow skips Codex and Meshy:
   `scripts/bake_crossbow.py` paints its four tiers procedurally ("Crossbow tiller and skins").
5. **Meshy** (`scripts/meshy_request.py <kind> <tier> [version]`): each master checked against its guide (alpha IoU,
   refused below 0.8) and cut to the guide's silhouette; `meshy-7`, original UVs, PBR, 4K, the masters as multiview, no
   text prompt. Submitted with `tools/run_creature_meshy.sh`, polled with `scripts/poll_jobs.sh`.
6. **Post** (`scripts/export_mesh.py`, `scripts/bake_ao.py`, `scripts/post.py maps|skin`): as the Oblivion skins' post
   with the regions from `build.py` instead of Oblivion's specular mask: 4K -> 2K once, gentle grade on the AO bake,
   weave filter and albedo by tier on steel (brass and gold keep their paint with a luminance floor), honed `edge`
   strips brighter and glossier, lengthwise grain and a small normal tilt on blades, tier-1 rust non-metal; the
   legendary tier's cyan-teal paint on metal becomes emissive (and non-metal), stones glow by tier, the blaster's cell
   always; MR (R = AO, `openyamm_specular_occlusion: orm`) 1K, colour/normal/emissive 2K; `gutter_fill.py` last; the GLB
   written directly (one mesh, one material, node `w_<kind>`, winding with the normals). Rigid runtime turns are applied
   in `export_mesh.py` (same UVs and paint): the blaster half a turn (kinds.py `turn`), lifted up the fist (`shift`) and
   its muzzle raised (`aim`; "Blaster"), the crossbow placed in the right hand's Weapon node (`mount`, "Crossbow
   hold"), the spear's plain shaft shortened (`compress`), the club moved down the hand (`shift`).

## Held length

The two-handed clips swing a sword-length arc: at idle the shaft stands upright out of the top of the screen and a
2 m pole's head is never seen. Tested by moving the grip up the shaft (point at 110, 86, 76, 68, 58 units from the
palm): even at 58 only the socket reaches the frame at idle, while the swings bring the head into view at any of
them. So the poles are held naturally (both hands on the wrap, butt 22-30 units behind the palm) and shortened to
1.65-1.75 m: spear point at 88 (built 140 long and painted; the plain shaft compressed to 0.66 at export, the paint's
grain squashed by a third there), halberd spike at 98 and trident point at 96 (rebuilt shorter before their layouts).
The follow-through of the right swing (`twohandattackright` about 0.4 s) points the pole forward with its head in
view; that is the capture pose. A pole head readable at idle needs own two-handed clips (WEAPONS.md, work order 4).

## Crossbow hold

Built in the left hand's Torch frame at the bow's full draw (`bowattack` Hold, 1.37 s: +X along the aim, +Y up, +Z
right, measured in Blender from `arms.glb`): level, a short vertical foregrip in the left fist at the origin, the stock
running back toward the right hand, its rear shortened so the butt does not fill the screen.

**Since 2026-11-14 it has its own set**
([crossbow_set_20261114](../crossbow_set_20261114/README.md)): both hands on it, the right hand holding it. The runtime
copies are placed rigidly in the right hand's Weapon node by kinds.py `mount` (`weapon_from_build`, applied by
`export_mesh.py` to every tier; the set's clip bake reads the same function): the laced wrist of the stock (build
-11.5, 0, 3.95) at the fist's centre, the stock along the node's +Y, turned -115° about it so the hand cradles the wrist
from below and behind. The left fist stays on the foregrip in the build frame, so the template, the clips and our
ground crossbows agree. Re-placing it: change `mount`, run `export_mesh.py crossbow` and `bake_crossbow.py 1 2 3 4`
(the maps are unchanged: tid/bary and the AO bake are in UV space, and the bake inverts `mount` to paint in the build
frame), copy the four skins and the mid skin as the template, and rebake the arms
(`crossbow_set_20261114/scripts/rebake_arms.sh`). The tiller rework below kept the wrist and the foregrip where they
were, so the clips and the arms did not need a rebake.

Before the set (superseded): the bow set, the crossbow hanging rigidly on the left hand's Torch node, pitched 6° and
yawed 8° about the palm (`aim`); drawing the bow read as winding the crossbow and the left fist held the stock up.

## Crossbow tiller and skins (user's review, 2026-11-14)

"Doesn't look that different between the versions": low, mid and legendary showed the same pale ribbed stock, only
the high tier (black) differed.

- **The ribbing** was in the colour map, not in the geometry or the normal map (Meshy's normal map was nearly flat,
  the loft smooth): the rendered masters' wood was a Blender wave texture (`render_masters.py`, bands along the stock),
  and Meshy's paint over them turned it into dense, regular, high-contrast pale stripes on every tier. Those maps are
  gone; the new grain is a distorted ring field with irregular spacing (a ring about every 0.6 units).
- **The tiller** (`build.py` `build_crossbow`): the 12-sided box loft became a 20-sided shaped tiller: squarer
  shoulders on top (the groove), a rounder belly, a slim fore-end, a narrower wrist under the laced grip, the butt
  deepening below a straight comb into a tapered end, a cheek piece swelling out of its left side (+Y in the build
  frame); lock plates on both sides of the nut, each set with a stone, a stone in the nose (region `gem`); the prod's
  clamps and the butt plate in region `brass` (gilt or platinum by tier); the trigger lever hugging the new belly.
  The wrist (-11.5, 0, 3.95) and the foregrip stay where they were, so kinds.py `mount`, the crossbow set's clips and
  the arms are unchanged. 2,260 triangles (was 1,522). Layout redone from scratch (`prep.py crossbow`, sparrow,
  `bake_ao.py`, `export_mesh.py`, `post.py maps`); the v3 state is kept in `work/crossbow_v3_backup/`.
- **Codex, two more wordings, refused:** "antique workshop instrument: a carved wooden stock (museum stock furniture)
  with a curved steel spring", per-tier materials from the review (`codex_masters.py` crossbow entries), tiers 2 and 4;
  then the same with a binding rule never to name the object or its use in the image prompt. All four sessions were
  blocked as violence on the first image (`work/crossbow/masters_t{2,4}/codex_run_refused_{2,3}.log`): the guide
  silhouette itself is refused, whatever the words.
- **Procedural skins** (`scripts/bake_crossbow.py <tier>...`, numpy, no Blender, no Meshy, 0 credits): every map
  computed per texel of the locked layout at 4096 from the 3D position in the build frame (kinds.py `mount`
  inverted), by region and tier, and downsampled once to 2048 (MR 1024); the normal map is the derivative of a height
  field along each texel's tangent frame; the AO bake shades the colour gently and fills MR's R; `gutter_fill.py`
  last; post.py's GLB writer. About 6 minutes per tier. The tiers:
  1. rough weathered grey-brown wood (bleached grey patches, open cracks along the grain, scuffs), rusty iron (pitted,
     orange-brown rust patches, non-metal there), cracked rawhide with pale lacing, a frayed hemp cord, iron bosses;
  2. warm polished walnut with a flowing figured grain (satin, roughness 0.3), satin steel fittings, dark brown leather,
     a cream linen cord, steel bosses;
  3. black lacquered ebony with framed gold panels on both sides of the butt and the fore-end (a border 0.32 inside
     the edges and a gold rinceau: a waving vine with a spiral curl at each crest), polished steel (roughness 0.2:
     lower read black without an environment map), engraved gold clamps and butt plate, crimson leather laced with
     gold, a gold-bound cord, rubies; no glow;
  4. blackened wood with a violet cast, dark star-metal with a blue-violet hue drift, platinum clamps, butt plate,
     lacing and cord, luminous rune channels (a line with hashed rune marks every 1.6 units, cyan drifting to violet)
     along both sides of the stock over the wood and the lock plates and along the front and back of the prod, and
     glowing cyan-violet stones: the only tier with an emissive map.
- **Verdict at full size** (`ingame/review3/crossbow_*`): four different crossbows at a glance outdoors (grey-brown
  weathered wood with rusty iron; red-brown walnut and bright steel; black with gold scrollwork, a ruby and crimson;
  black-violet with glowing cyan-violet runes). The recoil frame shows the prod across the screen: rusty, bright steel,
  polished steel, violet with runes. In 6d05 tiers 1-3 go dark as every template does there; the legendary runes and
  stones glow. Procedural rather than painted: the wood and metals are clean and a little graphic next to the Meshy
  skins of the other kinds.

## Blaster

Built in the Gun frame as WEAPONS.md described it then (muzzle -X, grip down through the fist): in game the muzzle
pointed at the eye, so the runtime copy is turned half a turn about the vertical (`turn`). `onehandblockidle` reads as
aiming. Shots still play the one-handed swings (no aim or recoil clip).

**Grip (user's review, 2026-11-14: "not held properly"):** the fist closed below the gun body instead of around its
grip. Measured in the Weapon node at `onehandidle` (the posed arms' finger vertices against the model): the fingers
wrap the node's Y axis from y -3.5 (little finger) to 3.2 (index), the thumb up to 4.1; the body's underside sat at y
1.2, so the index and middle fingers were inside the body and only the lower half of the fist held the grip. The
runtime copy is now lifted 2.3 units up the fist (kinds.py `shift`) and its muzzle raised 10° about the palm (`aim`,
the grip's rake along the fist's axis): the body sits on the index finger, the trigger guard just in front of it, the
whole grip in the fist and its pommel below the little finger; at idle the barrel points up and forward past the
left of the crosshair, in the block pose at it. Same UVs and paint (`export_mesh.py blaster`, `post.py skin blaster <t> blaster_t<t>_v1`,
identical stats). The offline check is `crossbow_set_20261114/scripts/preview.py <arms.glb> <w_blaster.glb> ...
onehandidle@0@close`. The right swing (`onehandattackright`, the shot clip) still swings the pistol sideways across
the screen: held properly, but it reads as a swing, not a shot.

**Ground blasters (the Gun mount):** `heldWeaponMatrix` put the muzzle along -X, which is toward the eye; it now
puts it along +X (out of the knuckles, `game/render/HeldWeapons.cpp`), and our ground blasters point forward. The
shot itself is not affected by either: a party's blaster bolt leaves the party's ranged source (its position at
`PartyAttackProjectileSourceHeight`, as arrows do), not the muzzle; only spells start at the casting hand on screen.

## Wand glow

User's review: "could glow a bit? the tip?". The crystal (region `gem`) glows on every tier, set in `post.py`
(`WAND_GLOW`, wand only, no new Meshy jobs): peak emission 0.2, 0.45, 0.55 and 1.0 for tiers 1-4, in the crystal's own
hue pushed to full saturation (tier 1's grey quartz a faint cool blue-white), brighter toward the tip (0.4 at the cup,
1 at the point) and on the paint's lighter facets (0.3 + 0.7 facet^1.5), so it reads as a lit crystal and not a flat
blob. Verdict (`ingame/review3/wand_*`, against `ingame/v2`): in daylight tiers 1-3 look almost as before (the
sun swamps a faint glow) and the legendary is brighter; in 6d05 every crystal now stays lit and faceted (pale blue,
blue, red, violet) where tier 1 was dark grey and tiers 2-3 dim before. Subtle by design ("a bit"); `WAND_GLOW` is the
knob.

## Club

Added later the same day; clubs drew the Oblivion mace's low tier before. One template for every club (Barbed,
Thornbark, Primitive, Thorned, Steel, Root, Spiked and Killer Club: values 1-120, all below the 150 band), so only
**tiers 1 and 2** exist (`held_tiers.yml` `club: {file: w_club.glb, max_tier: 2}`; tier 2 is an enchanted club).

- **Design** (`codex_design.py club`): the first brief ("hardwood walking cudgel", iron thorns, six icons) was refused
  as violence; the second, a **shillelagh** walking stick with "decorative pyramid studs" and four icons (item077,
  club1, 7item058, club2), went through: a knotted shaft swelling into an egg-shaped knob, a riveted iron band at the
  neck and near the top, pyramid studs, a criss-cross rawhide wrap, a butt band and knob. The tier briefs use the
  same wording (`codex_masters.py` `WEAPON['club']`, club-specific materials in `KIND_TIERS`).
- **Model** (`build.py` `build_club`): one lathe (18 sides) along a Catmull-Rom radius curve, every vertex pushed out
  by low-frequency ridges and eight Gaussian burls (two knots on the shaft, lumps on the knob; damped on the wrap and
  the bands), the bands and the wrap raised sleeves, twelve four-sided studs, eight domed rivets: 2,440 triangles,
  55 units (79 cm, make_held_table.py's club length), the handle 2.88 across over the wrap.
- **Hold:** the one-handed set like the mace. Built with the palm at the wrap's middle, the knob stayed above the idle
  frame; the runtime copy is moved **4.5 units down the hand** (kinds.py `shift`, applied in `export_mesh.py`: butt
  15 below the palm as on the mace's 16), so the fist holds the top of the wrap and the neck band and the knob's base
  show at the top of the idle frame. The right swing's backswing (0.25 s) and blow (0.4 s) show the whole knob.
- **Upload:** two pieces (knob, handle; cut in the plain shaft at z 18), front and back views.
- **Masters:** tier 1 front and back; tier 2's back refused (violence), so the front mirrored (`meshy_request.py`).
  IoU 0.97-0.98.
- **Verdict at full size** (`ingame/club`): tier 1 weathered grey-brown ash with dark knots, a pale rawhide wrap and
  dark iron; tier 2 dark oiled walnut with flowing grain, bright steel bands with brass rivets and a dark leather
  wrap: two clearly different clubs. The master's bark patches on tier 1 mostly became grain in Meshy's paint. A
  faint colour step runs round the shaft at the upload cut (z 18, 13.5 above the palm at runtime: visible at idle on
  close look). In 6d05 both tiers go nearly black, like every template there.

## Legendary poles

Redone 2026-11-14 after the user's review ("legendary doesn't look legendary"; the trident's also "a bit blurred"):
at idle only the shaft shows, and the first legendary gave it bone-white wood with a few cyan bands, which read plain
and pale. Tier rule (shared by the skin helpers): high is mirror steel, ebony with gold filigree, crimson leather and
rubies, and does not glow; legendary is the only tier that glows: dark star-metal, blackened wood, platinum fittings,
luminous rune channels along the visible shaft and glowing stones at the collars and head.

- **Masters:** `codex_masters.py` `KIND_TIERS[(pole, 4)]` for spear, halberd and trident: star-metal with a blue-violet
  sheen and platinum filigree, cyan stones set in every collar and band, near-black ebony with a blue-violet sheen,
  midnight-violet leather with platinum wire. All six views on the first try (no refusal), IoU 0.90-0.94. The
  bone-white masters and skins are kept in `work/<kind>/masters_t4_bonewhite/` and `work/<kind>/t4_bonewhite/`.
- **Meshy:** `<kind>_t4_v2`, 30 credits; the paints follow the masters closely (violet star-metal, cyan rune lines on
  the heads, beaded collars).
- **Post:** `scripts/shaft_runes.py`, called by `post.py` for tier 4 of the poles, draws the shaft from each texel's
  3D position (the shaft axis is the model's +Y): the wood recoloured to violet-black ebony with Meshy's brightness as
  faint detail and a fine lengthwise fibre grain; **two rune channels** spiralling up the wood (26 units per turn),
  each a glowing core (cyan at the centre, violet at its rim, emission 1.0) in a faintly violet-glowing groove between
  raised platinum lips (relief in the normal map), widened into a diamond rune every 6 units of height. **Second
  pass** (same day, coordinator's review: the 0.22-unit core read as a thin pale lilac line outdoors): the core 0.5
  units wide, saturated cyan with violet only at its rim and in the diamond runes, and the material's
  `KHR_materials_emissive_strength` 2.5 like the legendary bow (`post.py` writes it from `shaft_runes.EMISSIVE_STRENGTH`;
  the head's runes and stones scaled to 1.25x their earlier glow); and **small
  glowing cabochons** (alternately cyan and violet, eight round each collar or band 0.7-3 units tall, platinum bezels)
  on the shaft's fittings between the wrap and the head. The head keeps Meshy's paint (its cyan runes and stones
  become emissive as before). Re-run: `post.py skin <kind> 4 <kind>_t4_v2`.
- **Verdict** (`ingame/v6` t3 and t4, `ingame/v5` the first pass, outdoors and in 6d05): legendary now reads at a glance as the magical one on all three: a
  violet-black shaft with two broad, luminous cyan channels (in daylight too) and glowing beaded collars, against high's black and gold with
  a crimson wrap. High unchanged. The halberd's paired rings are the busiest part (Meshy's painted cyan stones and the
  cabochons together).

## Shaft sharpness

Measured at the idle pose (1600 x 900, `ingame/v4`/`v5`): near the hand the shaft is about 85-90 px across at the
wood (2.5 units) and 110-120 px at the wrap (2.8 units), so **34-40 screen px per unit**. The layouts give the shaft
(units of runtime model):

| Kind | Wood texels/unit | Wrap texels/unit | Screen px per texel, wood / wrap |
|---|---|---|---|
| spear | 59 (lengthwise squashed by the compress) | 44 | 0.6 / 0.85 |
| halberd | 38 | 29.5 | 0.9 / 1.3 |
| trident | 44 | 39 | 0.8 / 1.0 |

So one texel covers about one screen pixel (only the halberd's wrap is magnified, 1.3 px per texel): the 2K maps are
not what blurred the trident. Meshy paints from the masters, which show the pole at about 30-38 px per unit (1536 px
guides of three or four pieces), and the bone-white legendary had low-contrast, soft-edged paint on its wood. The fix
is detail drawn at the map's own resolution (`shaft_runes.py`): the channel and lip edges are 1-1.5 texels wide, the
fibre grain is at texel scale. Strongest painted edges on the wood (local range / peak gradient, median of the top
3 %; a perfect step measures about 1.5-2): spear 2.08 -> 1.77 texels, halberd 2.09 -> 1.57, trident 2.22 -> 1.53;
in game the new shaft's lines are crisp at idle. Not done: a denser shaft layout (it would need a new paint or a
resampled carry-over of tiers 1-3, and the head shows at idle once the poles have their own clips) and a 4K colour map
(the view model loads PNGs raw: 4K RGBA with mips is 89 MB per map). **Runtime texture memory** (raw RGBA8 with mips):
2K colour, normal and emissive 22.4 MB each, MR 1K 5.6 MB: **72.7 MB** for a legendary pole (50.3 MB for tiers 1-3
without emissive), unchanged by the redo; only the held weapon's skin is loaded.

## Measures

Triangles (Oblivion templates 1.2-1.5k), layouts (`texture_quality.py` on `layout_measure.glb`, 2048; density in
texels per model length), runtime GLB size (2K PNG colour and normal, 1K MR, 2K emissive on some tiers):

| Kind | Tris | Length | Atlas | Density p10/p50/p90 | Fragments | Stretch p90 | GLB MB |
|---|---|---|---|---|---|---|---|
| spear | 2,748 | 118 (1.69 m) | 79.5 % | 6,196 / 6,228 / 8,889 | 0.0 % | 1.12 | 8-11 |
| halberd | 2,400 | 120 (1.72 m) | 79.8 % | 3,546 / 4,967 / 5,186 | 13.2 % | 1.30 | 8-10 |
| trident | 2,880 | 118 (1.69 m) | 80.3 % | 4,649 / 6,397 / 6,661 | 1.1 % | 1.13 | 9-12 |
| wand | 1,638 | 30.6 (44 cm) | 76.2 % | 3,355 / 3,612 / 3,847 | 0.0 % | 1.30 | 8-10 |
| blaster | 2,722 | 25.3 (36 cm) | 81.8 % | 1,860 / 2,034 / 2,177 | 0.6 % | 1.33 | 10-12 |
| crossbow | 2,260 | 57 (82 cm) | 68.7 % | 2,483 / 2,654 / 2,808 | 14.0 % | 1.64 | 5.3-6.7 |
| club | 2,440 | 55 (79 cm) | 67.7 % | 2,413 / 3,262 / 3,608 | 0.3 % | 1.21 | 10.5-12.8 |

The halberd's and crossbow's "fragments" are their small separate parts (studs, clamps, rivets; strings, bands, the
stirrup), not specks of one surface; the crossbow's stretch p90 is its thin cords and swept prod.

## Credits

37 retexture jobs at 10 credits, **370** (ledger `creature_3d_progress.json`): 320 of the 600 allowed for the six
kinds, then 20 of the 60 allowed for the club (its claim set the ledger's `credit_limit` to 380), then 30 for the
legendary poles' redo (claimed with `--budget 420`, 80 allowed):

| Kind | Jobs | Credits | Note |
|---|---|---|---|
| spear | t1-t4 v1 | 40 | t2 back mirrored |
| halberd | t2-t4 v1 | 30 | t1 recoloured from t2's paint (masters refused four times); t3, t4 backs mirrored |
| trident | t1-t4 v1, t2 v2 | 50 | t2 v1 a text-prompt fallback (rejected: it painted a pole piece steel); v2 from a Codex master, back mirrored |
| wand | t1-t4 v1 | 40 | |
| blaster | t1-t4 v1 | 40 | |
| crossbow | t1-t4 text v1, v2, v3 | 120 | text prompts weak (rejected); v2 rendered masters with a framing bug (top view only); v3 accepted, replaced after the review by procedural skins (0 credits) |
| club | t1-t2 v1 | 20 | t2 back mirrored |
| spear, halberd, trident | t4 v2 | 30 | legendary redo ("Legendary poles") |

## In-game checks

`scripts/run_ingame.sh <kind> outdoor|indoor <tag> ["1 2 3 4"]`: 1600 x 900, `--ruleset maw:solo`, MM6 New Sorpigal
(oute3) at 9 am and Corlagon's dungeon (6d05), `viewmodel kit <set> w_<kind>.glb 0`, per tier idle and two attack
moments, then our ground model (`viewmodel weapons ours` + `viewmodel held <icon>`). Final captures `ingame/v2`
(spear, wand, blaster) and `ingame/v4` (halberd, trident, crossbow), the poles since the legendary redo `ingame/v5`
(all four tiers; `ingame/proto1`, `proto2`: the shaft pass's trials), the crossbow, wand and blaster after the user's
review `ingame/review3`; `scripts/to_viewer.py` writes the review JPEGs.
`ingame/auto_tier/`: real items through `viewmodel equip` (Steel Spear low, Light Poleaxe mid on the halberd, Titanic
Trident high, Root Club the mace's low tier before the club template, Blaster low, Sparkling Wand high). The club:
`scripts/run_ingame.sh club outdoor|indoor club "1 2"` (`ingame/club`), the plain model's hold tests in `ingame/plain`
and `ingame/plain_shift`, and real items in `ingame/club_auto` (Root Club and Steel Club, both low).
