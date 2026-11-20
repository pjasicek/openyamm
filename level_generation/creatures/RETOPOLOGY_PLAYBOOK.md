# Retopology, repair and retexture playbook (on demand)

## Default route (user-selected 2026-10-13)

Record every reduced model in [REDUCTION_LEDGER.md](REDUCTION_LEDGER.md) (before/after, LODs, credits, status,
rollback source) when it is installed or rolled back.

Worked example: MM6 Fire Lizard, `mm6_drag_reduce_claude/` (README rounds 2-3): 13,789 -> 4,882 triangles, about
12 minutes, 20 credits, installed. Aim for a playable baseline, not perfection; the user reviews once or twice.

1. **Texture-aware reduction ladder** (`dump_mesh.py` -> `decimate_tex.py` -> `reduce_ladder.py` with
   `REA_METHOD=texture` -> `compare_ladder.py`): MeshLab quadric decimation that keeps UVs, weights by data transfer,
   error over every clip, one contact sheet, auto-pick of the lowest passing step (~40 s). Do not use Blender's
   Decimate: it slides UVs across seams (misaligned belly plates), and locking seam vertices blocks reduction.
   **Humanoids: protect the head** (`REA_PROTECT_HEAD=1`, plus `REA_PROTECT_ZMIN` covering the whole head texture
   set). A uniform cut halved the cannibal's face, and the retexture then followed the flatter forms. A kept head
   also keeps the accepted head texture (`mm6_natm_reduce_claude/scripts/copy_head_uv.py`), so only the body needs
   a Meshy job. When the head weights or head texture set also cover a hood or hair mass (MM6 Ghost: 44 % of the
   faces), protect only the face from the region mask (`REA_PROTECT_FACES`) and decimate it gently on its own
   (`REA_PROTECT_RATIO=0.6`; `mm6_gst_reduce_claude/`): keeping it whole pushed the whole cut onto the cloth.
2. **Fix small broken parts** the reduction exposes or the source already had: teeth, horns, claws, spines. Replace
   them with clean simple shapes on their original bone (`build_r35.py`: teeth as 6-sided cones, upper teeth hang from
   the top of their blob, lower rise from the bottom, root sunk into the gum). Label `part` per connected piece
   (majority vote), never per vertex: per-vertex labels painted skin beside spines/teeth ivory.
3. **Fresh UVs and a Meshy retexture per texture set** the creature has (body, head): the creature's own accepted
   requests and HD references, `enable_original_uv`; 10 credits each, back in ~2 minutes. Check UV parity.
4. **Apply** with the creature's own texture/runtime chain (`r35_texture_chain.sh`: raster, AO, compose with region
   mask and tier ramps, export, prepare, LODs, region variants, head merge, viewer tiers; ~70 s). Render open-mouth
   and spine/claw close-ups, then add the result to the viewer beside the unreduced model and run `check_viewer.mjs`.
5. **User review**, then back up the installed source and install (`tools/install_model.py`), run the actor
   regression, update the creature README.

**Horns and spikes grown out of the skin, scale size, saturation** (MM6 Dragon, `mm6_cdr1_reduce_claude/`, README
round 2, installed 2026-10-14, 20 credits):
- Horns that are part of the main surface: find them by texture (faces whose UV samples ivory), split each region
  into single spikes by a persistence watershed on geodesic height above the region border, remove the region and its
  raised skin sheath (flatten onto a robust quadratic fit of the surrounding three edge rings), close the hole with a
  fitted patch, and set closed round tubes into it with roots sunk along the surface normal (`build_horns.py`).
  Extract hole rims as directed cycles from the neighbour faces' winding (a pinched rim splits into closed cycles);
  a plain boundary walk produced open chains and a long sliver. Mirror the +x spikes to -x.
- Head scales the size of the neck's: give both Meshy jobs the whole creature (target set in about 90 % of the
  layout, the other sets small beside it) with the same full-body references; then quantile-match head and body
  luminance to one distribution so the shared ramps give one colour.
- Saturation against the restored x2: compare CIE LCh medians of the hide and belly pixels (sprite frames vs a
  render), not HSV saturation (both read about 0.9). Raise ramp chroma about luminance in linear space.

**No part to rebuild: skip the retexture** (MM6 Demon, `mm6_demon_reduce_claude/`: 16,474 -> 9,060, no credits,
installed). The reduction keeps UVs, so the installed textures, variants and region ramps stay valid: import the
installed source GLB and weld exact duplicates first (`import_source.py`; glTF splits vertices at every UV seam and
the decimation cannot cross them), run the ladder with `REA_HEIGHT_M` set to the creature's height, then
`export_cand.py` -> `swap_lod0.py` (new LOD0 primitives by material name, old LODs dropped, buffer compacted) ->
`tools/build_actor_lods.py` -> `carry_variants.py` (the LOD builder drops `KHR_materials_variants` from LOD and
shadow primitives; the demon's variant regression caught it) -> install.
Check every LOD's height against LOD0 before installing: picking bounds (and the native-height regressions) use the
coarsest LOD, and its collapse can remove a thin top feature (Dwarf helmet spike, 8 cm; Water Elemental crown).
Higher LOD ratios did not keep the spike; an inverted vertex group in the decimate modifier does, at the same counts
(`mm6_dwa1_reduce_claude/scripts/build_lods_keep_spike.py`).
Models that passed the shared gate runner (`claude_shared/gates/run_gates.sh`; Codex projects keep the config) must
pass it again before install (MM6 Lizard Archer, `mm6_lzd_reduce_claude/`, 2026-10-14): lock the soles (faces below
about 6 cm; foot yaw uses heel/toe patches of the lowest 5 mm) and any spot a gate names, and build LOD1-3 by trimming
the accepted fitted LODs with hands, fingers, flaps and soles locked (`scripts/codex_lods.py`) instead of
`build_actor_lods.py`, which broke the fitted grips. A held prop's LOD wrap needs enough of its budget to keep the grip.
Weld only duplicates with identical skin weights (`mm6_kni_reduce_claude/scripts/import_source.py`, 2026-10-14): a
plain weld merged seam duplicates that carry different bones, and the Knight's fauld got a pelvis-weighted corner
that folded through the tasset in every pose. No kept faces or weight transfer repairs that. Rollback sources of
Bloodsucker, Goblin, Cannibal, Spider, Lizard and others hold such pairs (a few to 48 per model); check a reduced
model there if a plate edge or seam folds in poses.
Per-LOD materials of the installed file (Knight: own LOD normal maps) become unused after the LOD rebuild; drop
them with `mm6_kni_reduce_claude/scripts/prune_materials.py`. Thin blades take normals by angle
(`PROP_NORMALS_ANGLE`); transferred normals pick up the far side.

**Split seams with coincident vertices** (MM8 Dragon, `mm8_m492_reduce_claude/`, 18,278 -> 10,051, no credits): a
mouth opened by splitting the lip edges keeps coincident upper (Head) and lower (Jaw) vertices; `import_source.py`
prints them as "coincident with other weights". The weld-back and weight transfer picked either vertex of a pair,
and collapses near the mouth corners built faces across the seam: a dark box between the open jaws at every step.
Use that project's `decimate_tex.py` (pairs moved 2e-5 m apart for MeshLab, `src_index` per output vertex) and
`reduce_ladder.py` (`exact_weights`: source vertices keep their source weights), keep the faces within about 1 cm of
the seam exactly (`mouth_keep.py`), and check that no face stretches in any clip at any LOD (`lod_check.py`).
The Phoenix beak (`mm8_m572_reduce_claude/`) had the same split.

**MM8 batch lessons (2026-10-18)** (Phoenix, Necromancer, Nightmare, Cyclops, Wyvern: `mm8_m{572,472,600,520,560}_reduce_claude/`):
- **Judge shading only from GLBs imported directly** (`mm8_m492_reduce_claude/scripts/glb_close.py`), never from
  `work/source.blend`. Its weld rotates the custom normals (Blender stores them relative to the default normals), so
  its renders show fake wrinkles. A normal transfer from it (`REA_NORMALS=transfer`) copied that noise onto the
  reduced mesh. The installed MM8 sources all shade smooth, so the reduced meshes keep plain smooth normals.
- **Parent before transform:** `reduce_ladder.py` must set the candidate's parent and parent inverse, then
  `matrix_basis`. Setting `matrix_world` first applies a rig's own transform twice; every step then sits the same
  ~4 cm off the source (Nightmare, Naga). Fixed in the m492 copy.
- **Thin features the averaged checks miss:** small teeth that are part of the head surface (Wyvern: reduce the head
  on its own at 80 %, `REA_PROTECT_HEAD=1 REA_PROTECT_RATIO=0.8`), painted rope trims across a UV seam (Necromancer
  cuirass centre line: keep the strip), a UV corner pushed onto a chart border that picks up another region's colour
  (Nightmare stalk fleck) and dark slivers at texture-island edges (Cyclops, `dark_slivers.py`). The per-face
  median drift stays under its threshold for all of them; look at seams and junctions in textured close-ups of every
  tier and keep the faces around each spot.
- **LODs:** lock the floor-contact vertices of Death/Dead in the LOD build (`protected_points`; Phoenix LOD3 went
  3.7 mm under the floor), keep a separate effect mesh's own LODs (Phoenix flames), rescale the LOD ratios when a
  fixed protected set (Nightmare eyes) takes a large share of a smaller LOD0, and on gated models trim the fitted LODs
  with the bounding extremes locked (Cyclops).
- **Retiming a clip on review** (Ether Knight, `mm8_m604_reduce_claude/scripts/retime_attack.py`): keep the
  engine's impact time and clip length, and rewrite only output values at the existing key times. Mixamo-derived
  clips are 30 Hz keys resampled linearly to 120 Hz, so every source key is a sudden speed change. Slowed down, each
  one shows as a visible stance jolt. Sample the slowed parts through a velocity-continuous spline (modified Akima over
  the 30 Hz keys). Keep legs on lerp, low-pass them instead, and re-lift the pelvis by the measured floor dip.
  `bone_velocity.py` finds the jolts: per-bone deg/s, and the largest change from one viewer frame to the next.
- **Weights on interpenetrating parts:** take each new vertex's weights from the source triangle containing its UV
  (Nightmare `uv_weights.py`); nearest-face transfer picked a neighbouring lump.
- **Colour after a reduction:** a separate pass can find old texture faults the reduction did not cause: the
  Phoenix's Meshy eagle head stayed brown in every tier (`unify_head.py`, local fix) and the Cyclops wrist-wrap mask
  spill. A Meshy retexture from the same references would repaint them, so fix them locally.

**Thin tubes and UV drift** (MM6 Werewolf, `mm6_wwf_reduce_claude/`, 10,821 -> 6,489, no credits): keep thin
closed tubes (a necklace chain, a pendant) exactly with `REA_KEEP_FACES`; they break into gaps at any cut. The
texture-aware collapse can still move UVs on a few large faces (dark blotches on cloth): `texture_drift.py` compares
each face's base colour with the source's at the same rest-pose points, and `drift_lock.py` keeps the source faces
around drifted ones. Run one lock round only; a second one moves the drift elsewhere and raises the error.
The check misses colour boundaries that cross faces (the chain fighter's tabard split), so still look at the back.
Thin painted lines (trims, plate bands) bend under any collapse, even at 70 %: find them from the runtime maps
(region mask channels, gold by base-colour hue) and keep those faces exactly; reduce broad trims gently on their own
(MM6 Medusa, `mm6_med_reduce_claude/`: bodice and belly kept, gold at 70 %, 14,900 -> 9,684).

**Two-sided sheets** (MM6 Harpy, `mm6_hrp_reduce_claude/`): if `import_source.py` prints fewer triangles than the
GLB's LOD0, the weld merged a face with its reversed copy (wing membranes). Record the pairs before the weld
(`find_doubles.py`), keep those faces in the ladder, and add the reversed copies back on export
(`export_cand.py` with `REA_DOUBLES`); otherwise the membrane is open from behind.

**Held weapons and shields** (MM6 Chain Fighter, `mm6_figc_reduce_claude/`): keep the fingers and hands on the
body and the handle/grip faces on the prop exactly, so the fitted grip does not change; reduce the rest of the prop
with the decoration chain (`scripts/prop_*.py`). Give hard-surface props normals by angle: transferred normals
smeared dark wedges over the shield's flat back. When parts are kept exactly (`prop_parts.py`, MM6 female Cannibal,
`mm6_natf_reduce_claude/`), keep their transferred normals and give only the decimated parts normals by angle
(`prop_build.py` does this when the input has `nkept`): angle normals on the kept round grip bar made it a flat box.
A long decorated haft (MM6 Minotaur, `mm6_min1_reduce_claude/`) is most of the prop: keep only the band the fist
holds (finger joints sampled from the clips in the prop's own space, ±10 cm). When the installed LOD1-3 are already
leaner than a rebuild (hand-repaired Codex LODs), swap only LOD0 and its shadow (`swap_lod0.py`, `REA_KEEP_LODS=1`).
Thin rims and straps go wavy at any cut; keep them and reduce the broad plate or blade.
A model whose LOD1-3 had their own texture sets: `build_actor_lods.py` rebuilds every LOD on the LOD0 material,
so drop the orphaned materials and images afterwards (`prune_materials.py`; natf 14.9 -> 8.2 MB).

**Head and hands are most of the mesh: per-region budgets** (MM6 Leather Fighter, `mm6_fgt_reduce_claude/`,
9,305 -> 6,871, no credits): when protecting head and five-finger gloves leaves the clothing to absorb the whole cut
(boots pointed, fringes jagged), give each region its own ratio (`REA_GROUPS` + `REA_GROUP_RATIOS` in
`decimate_tex.py`): face skin and eyes kept (the lips lump at 60-80 %), hair 60 % (a crease opens at the hair edge at
45 %), gloves 45 %. Keep small separate pieces (connected components of up to ~80 faces: skirt strips, buttons,
buckles, belt bands) exactly: their ends taper into points at any cut. Primitive props (the mace's ball) dent under
the collapse; decimate the part on its own and project its vertices back onto the source shape (`mace_snap_ball.py`,
by the output's per-face `group`, not by distance, which also catches spike bases and the shaft).

**Armour plates over the body: per-part weights** (MM6 Titan, `mm6_ttn_reduce_claude/`, 10,176 -> 7,666): the
nearest-face weight transfer gave reduced vertices of plates the weights of the body beneath them (43-49 mm tears at
the back in Death). `REA_WEIGHTS=component` (`dump_weights.py`, `component_weights.py`) takes each vertex's weights
from the source part it was decimated from; source vertices keep theirs exactly. Painted trims cannot be a separate
group: they are thin strips, and decimating them alone with fixed borders failed at 70 %. Leave them in the main cut,
keep the trimmed mid-size pieces (arm bands, the belt jewel just over the 80-face limit) and run one drift lock.
`probe_max.py` now prints the source vertex's rest position: a single armpit point that kept failing every step
was fixed by keeping a 4 cm patch around it (both sides).

**Already-reduced bodies** (MM6 Dwarf, `mm6_dwa1_reduce_claude/`, 11,563 -> 8,785, no credits): when an earlier
pipeline step already reduced everything but the head, the cloth is thin and absorbs any extra cut. Measure the
error per region first (`region_error.py`): per-region budgets there did worse than one shared collapse, so keep
only small pieces, hems, the buckle, fingers (finger-weighted faces) and bracers exactly, decimate the face skin
gently on its own and cut the rest uniformly. Fingers in the shared cut came back as jagged points with dark
slivers. On held props, keep thin blades and wrapped grips exactly and cut collars, caps and sockets.
Look at the raised-arm frames (Attack wind-up) up close before reducing: the user found the installed dwarf's sleeve
flaring off the arm (Codex left the sleeve 15-60 % on Spine/Pelvis, and the separate elbow skin piece rigid on
UpperArm while its covers used the twist bones). Repairing it took two rounds (`fix_arm_weights.py`):
- the sleeve's inner half lies against the torso in the rest pose and the weights run as a continuum, so a hard
  sleeve/torso split (by weight threshold, arm-axis distance or distance from the hem) dragged the lats along and tore
  the armpit; a harmonic blend (graph Laplacian) fixed at "arm only" on the outer half near the hem and at the
  original weights on the torso does not;
- move a skin piece's UpperArm weight to UpperArmTwist rather than blending its rim to the twist bone: the partial
  blend pinched a band across the triceps when the twist bone rolled;
- keep the repaired area exactly in the ladder: the decimated shirt turned the smooth blend back into coarse steps;
- give studs the weights of their host surface only (a yoke stud over the shirt split in Death).
`rim_gate.py` tracks overlapping rims against their covers over every clip; clay renders from below at the attack
frames catch the tears it cannot. Copy `reduce_ladder.py` from a project with piece-aware weights
(`REA_PIECE_WEIGHTS`, Genie), not from the Leather Fighter.

**Skirt chains and paint on covered surfaces** (MM6 PeasantF2, `mm6_fmp_reduce_claude/`, 9,902 -> 7,622, no
credits): a long dress on 16 skirt chains spreads apart in Death; a uniform cut missed the hem by 30-59 mm, so give
the skirt-weighted faces their own group (80 %). Hair under a cap is painted cap colour and the hairline skin colour;
any hair cut pushes that paint out as flecks along the rim and temples (`hair_blue.py` finds such faces). Locking the
painted faces still left a nape fleck, so keep the whole head set when the hair cut saves little (~100 triangles).

**Black shards and texturing gaps** (MM6 Flying Eye, `mm6_bh_reduce_claude/` README round 2, no credits): a creature
whose own build cut it with Blender's Decimate after texturing (`reduce_lod0.py`) already has UVs slid across seams;
reduce from its pre-cut master instead (the eye's `work/anim_v1_full.blend`). Meshy also leaves near-black gaps on
surfaces no HD view saw (horn undersides, hidden face surfaces); any cut turns them into sharp triangles. Fill the wide
blobs (morphological opening keeps thin painted stripes) from the nearest clean texel of the same part in rest-pose 3D,
in every shared map (`repair_horns.py`), and pad the dark gutters (`pad_textures.py`). Teeth painted brown or banded:
cones for separate pieces, and UVs into a painted ivory cell for teeth that are part of the main surface.

**Strongly patterned cloth and a stale source** (MM6 Cutpurse, `mm6_mfp_reduce_claude/`, 10,183 -> 7,939): a printed
cloth piece (the skirt's medallion rows) tears under the texture-aware collapse long before its geometry error or the
drift check shows it; give the piece its own gentle ratio (85 %) and look at it from front and back. Before reducing,
compare the `assets_source` GLB with the runtime copy in `assets_dev` (clip durations, atlas size, hash): the cutpurse's
runtime was a newer project export copied in by hand, and the first pass reduced the stale source.

The `r35_*` scripts copy the Fire Lizard's own scripts with new paths; for another creature, copy that creature's
scripts the same way. The full route below is for meshes that are actually broken.

**Use only when asked** to cut an existing creature's triangle count without losing features, or to fix a mesh's
topology. It is not a default step of the creature-to-3D workflow. General rules and sources:
[guidelines section 8](../GAME_ASSET_MODELLING_GUIDELINES.md#8-retopology-and-high-to-low-baking).

Worked example: MM6 Wyrm, 2026-10-13 (`mm6_drr1_retopo_claude/`, installed into `mm6_drr1_claude/` as revisions 04-05):
14,413 -> 9,212 triangles with every feature kept, Meshy retexture (20 credits), user-reviewed over five rounds.
Every step below is a script there; `scripts/rebuild_wyrm.sh` reruns the whole chain after the remesh.

## 0. Priorities (user decisions)

- **Features beat triangle count.** No visible feature may change (spines, toes, claws, horns, teeth, barbels).
  A perfect quad retopology is not required; more triangles are acceptable.
- **Re-texturing afterwards is acceptable** (Meshy retexture on the new mesh). Baking the old texture onto a new mesh
  is only a preview: it comes out soft.
- Claim the creature's lease (`tools/creature_workspace.py`), snapshot its master, and keep the previous textures and
  exports (`review/pre_retopo/`): they are the colour reference for the repairs below and the rollback.

## 1. Remesh: what works and what does not

| Tried | Result |
|---|---|
| Blender QuadriFlow | refused a verified manifold, consistently wound voxel mesh ("needs to be manifold"); dropped |
| Instant Meshes (PyNanoInstantMeshes, separate venv) | clean quads at a uniform density; at body density all thin features vanish (spines, horns, toes) |
| Uniform remesh + original protrusions layered on top | **rejected by the user**: holes and mismatched texture at every spine base, floating claws |
| Un-Subdivide away from the head on an Instant Meshes result | only partly reverses its subdivision; little gain |
| **MeshLab adaptive isotropic remesh** (`remesh_ml.py`) | **accepted**: one continuous surface, small triangles on curvature (spines, toes, claws, mouth), large on the trunk |
| Rebuilding spines as clean tapered cones (`final_geometry.py`, `REA_SPIKES=1`) | no saving (adaptive spines are already light); stumps beside the cones near the tail; off |

Adaptive remesh settings (pymeshlab `meshing_isotropic_explicit_remeshing`): `adaptive=True`, `featuredeg=35`,
`checksurfdist=True`, 12 iterations; `targetlen` and `maxsurfdist` as a percentage of the bounding box. The Wyrm
(1 m): 1.4 % / 0.15 % gave 7.8k body triangles (accepted, `a14`); 1.8 % / 0.18 % gave 6.7k (also fine); 1.0 % gave
10.4k (no gain over the source). Run it on the body piece only; separate small pieces (eyes, tongue, cheek spikes)
are kept or replaced (section 4).

### When to stop

Run a ladder of 3-4 edge lengths and stop at the coarsest step where all of these hold:
1. **Close renders match** the source at the user's review spots (head front and side with open jaw, every spine row,
   toes and claws, belly/chest junction, inner thighs), untextured (workbench with cavity) and textured.
2. **No new open edges** (section 3) beyond the source's intended openings.
3. **Deformation** (`deform_check.py`): distance from every deformed new vertex to the deformed source over every 2nd
   frame of every clip; the Wyrm passed with mean <= 0.03 mm, 99th percentile <= 0.6 mm, max 3.4 mm (death collapse).
4. Silhouettes (spines, horns, toe count) unchanged in the three-quarter, side and front views.

The adaptive remesher refines curvature itself, so finer settings stop paying off quickly: below about 1.0 % edge
length the Wyrm had more triangles than its source.

## 2. Fit, materials, weights

`final_geometry.py`: shrinkwrap (Target Normal Project) onto the source, material per face from the nearest source
face, weights by Data Transfer (Nearest Face Interpolated) from the source body, limit 8, normalise; assert every
vertex has a weight. The rig and clips are untouched; check that the source master's actions match the latest
revision before building (`compare_actions.py`).

## 3. Holes: detect every one, then close it properly

**Detect** (`loops_probe.py`): group boundary edges into connected loops and print size and centre. Run it on the
source too: intended openings (mouth/throat, the open bases of generated teeth hidden in the gums) stay; everything
else is a defect, including holes the source already had (the Wyrm's chest junction). Also check:
- **Verify after filling.** `bmesh.ops.holes_fill` silently left the Wyrm's chest and tail-base holes open while the
  script logged them as filled. Always re-run the loop probe on the saved result.
- **Bowtie loops** (a vertex shared by two loop parts) cannot be ordered into one polygon; `triangle_fill` also
  returned nothing. Close them with a fan around a centre vertex, each fan face wound against its rim face.
- **Inside-facing faces** (`chest_probe.py`): cast a ray along each face normal; if the next surface faces the same
  way, the face is inside. The engine back-face-culls single-sided creature triangles, so inverted faces render as
  holes in game even though the mesh is closed.
- Two-edge "loops" left where fans meet are zero-area slits; harmless.

**Close** (`patch_v5.py`): build the face from the ordered loop (wound against the adjacent face), triangulate, and
tag it with a face attribute (`patch`) at creation (bmesh triangulation replaces faces; held references go stale).
**Do not copy UVs from the rim**: rim vertices often belong to different texture islands, so the new face stretches
across unrelated texture (the Wyrm's dark diamond on the yellow chest). Give each closed hole its own small cell in a
free part of its texture set (planar projection; largest empty square of the UV coverage), and let the compose step
paint it with the previous model's colour at the same 3D point.

## 4. Replace broken small parts instead of repairing them

- **Teeth:** Meshy teeth are broken triangle soup. Fit a curve per original row and place simple 5-sided cones
  (upper rows rigid on Head, lower on Jaw; front fangs larger, smaller toward the back); paint them ivory.
- **Eyes:** a lumpy eye blob cannot be painted cleanly. Replace it with an ellipsoid fitted to the blob's bounding box
  (rigid on Head), mapped by flat side projection into a free square of the head texture, and paint it procedurally
  by position: iris gradient, dark rim, vertical slit pupil.

## 5. UVs for the retexture

- Separate body and head texture sets (head faces = the head material). Each set packs only its own faces: packing
  the head islands into the body layout and then moving them out left about 15 % of the body texture empty.
- Upload layout for the body retexture: body islands at 94 %, head islands in a 6 % corner, so Meshy sees the whole
  creature. The runtime body layout is the same 94 % layout.
- Smart UV Project at 80 degrees (body) / 85 (head) with concave packing reached about 38 % / 53 % coverage on the
  bumpy Wyrm; lower angles fragment it into thousands of islands.
- Check the layout before paying: draw the UV triangles with PIL (`uv_layout.py`; Blender's layout exporter needs a
  GPU and fails in background mode) and print the coverage.

## 6. Retexture (Meshy) and compose

- Requests copy the creature's original ones with the new upload (`body_texture_v2.json`, `head_texture_v2.json`):
  `meshy-7`, `enable_original_uv: true`, `enable_pbr`, 2k, the four HD masters (body) and the head close reference
  with the style prompt (head). 10 credits each; both returned in a few minutes.
- `dump_final.py`: per texture set, triangles with UVs, rest-pose positions and part ids (skin, tongue, eye, cheek,
  tooth, patch), plus AO bakes with only that set's faces (the layouts overlap).
- `compose_final.py`: the project's normal material contract (graded base, normal, specular/roughness, hide/gold
  region mask, native palette ramps), plus three repairs:
  1. **Reference repair:** sample the previous texture at the same 3D point (8 nearest old-surface samples). Gold
     where the old model was clearly green becomes green, and the reverse for solid blobs only (thin strips are
     plate lines; repairing them painted gold streaks). Meshy put gold triangles on the Wyrm's thighs.
  2. **Islands:** a small patch whose 3D surroundings (1.5 cm) are over 80 % the other colour is recoloured (gold to
     green only where the old texture was not gold, which protects spines).
  3. **Patch faces** (closed holes) take the old texture colour.
  Limits found on the Wyrm: the previous texture had some of the same wrong flecks (front legs), so it cannot vouch
  for them; patches about 1 cm wide defeat a neighbourhood vote (their own surroundings are half their colour); a
  morphological opening erases thin UV slivers (use a minimum component size instead). Position rules per creature
  (no gold on the lower lateral legs) or explicit 3D repaint zones fix what remains; if many remain, a fresh retexture
  is cheaper than more rules. Each compose run took about 8 minutes at 2K (KD-tree lookups over all texels), so
  iterate on a cropped region first.
  Fills copy nearby correct texels at the nearest clean offset (keeps the scale pattern), with diffusion as the
  fallback. Repainted parts (eyes, teeth, horns, crest, cheek spikes) follow.
- Runtime chain unchanged: finalize (materials, charred remains, export) -> prepare_actor_glb -> LODs -> burn maps
  -> region variants -> install -> actor regressions -> viewer tiers.

## 7. Review checklist (what the user found, in order)

1. Holes at junctions (chest/shoulder, tail base) and inner thigh creases; check from below and from the front.
2. Spine bases, toes and claws in close-up.
3. Mouth: teeth, tongue, the throat opening.
4. Eyes up close.
5. Wrong-colour patches on the legs from the side (both sides), and inside the belly plates.
Render these spots in Blender (`render_master.py`) before sending a viewer link; then `check_viewer.mjs`.
