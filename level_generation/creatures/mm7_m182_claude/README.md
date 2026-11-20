# MM7 Dragon (m182) — v3b, 2026-10-21

v3b answers the user review of v3 (2026-10-21, `feedback/2026-10-21/`): "1) in front look the head is looking too
high up ... 2) the head graft should be better. 3) the wings ... the part fused to the body isn't moving at all and
has the dragon texture and the part which moved is weirdly stretching on the fixed wing part". Everything else is as
v3 below (cdr1 body, wings, rig and nine clips byte-identical; same Meshy returns; 0 credits spent).

| Item | Value |
|---|---|
| Export | [`export/mm7_m182.glb`](export/mm7_m182.glb), sha256 `fbe439c2de12c74e948f553429da4473d842d2d751077ebf12d10d0c403817a2` |
| Previous | v3a `export/mm7_m182_v3a.glb` (sha `1256d457…`, + `mm7_m182_lod0_v3a.glb`, `lods_v3a.json`), v2 `export/mm7_m182_v2.glb`, v1 `export/mm7_m182_v1.glb` |
| LODs | colour and shadow 7,056 / 4,208 / 2,338 / 1,649 triangles (wing membranes whole in every LOD) |
| Meshy | **75 / 100 credits**, none spent for v3b |
| Shots | `review/shots/v3b/`: `front_vs_native.png` (native sa0 / v3a / v3b), `side_vs_native.png` (sa2), `head_graft_a/b/c.png` (user's angle and from below, v3a / v3b per tier, plus Attack jaw open), `wing_root_mid_flap.png` (user's angle, Standing frames 3/9/15, v3a / v3b) |

**1. Head orientation.** Diagnosis: the cdr1 Standing clip lifts the Head 23.5° above its rest, and the v2 head was
grafted at its own rest pitch, so in flight the eye line (red iris → upper snout tip, side view) was **2.9°** below
horizontal: from the front one looked at the underside of the jaw. The native side flight frames, read off gridded x2
crops the same way, give sa2 23.4°, wb2 20.7°, wd2 20.2°, wf2 21.8° (mean 21.5°). Fix: the head (all grafted
vertices) is turned 25° nose-down about the Jaw bone head (the jaw hinge), so the jaw still opens about its own hinge;
no bone or clip changed. Eye line now **23.0°** in Standing/Walking/Running/Fidget (v3a 2.9°), Hit 23.8°, Attack
peak 51.8° (head dip), Death 28.3° (`review/animation_gate.json` → `eye_line`, `scripts/v3/eyeline_clips.py`). Yaw is
0 (bilateral). Mouth socket re-measured: `[0, 0.1718, 0.0096]` in Jaw space (`review/actors_binding.yml`).

**2. Head graft.** Diagnosis: the v2 head carries a throat/neck stub shaped for v2's vertical neck; after scaling it
formed a 2–3 cm collar around the thinner cdr1 neck (a step at the nape and the throat), and the v3a texture blend
took the throat from mirrored neighbours, which broke the gold plates into a blocky patch. Fix
(`scripts/v3/reshape_neck.py`): the loft and the head's neck stub behind a plane 2 cm behind the jaw hinge
(perpendicular to the skull axis; jaw-owned vertices excluded) are refitted as one minimum-curvature (bi-Laplacian)
surface between the cdr1 neck (two fixed rings) and the skull: no collar, one smooth profile front/back/sides.
Frill spikes in that patch, separate cheek spikes and the first dorsal blades follow their roots; the head stays
exactly mirror-symmetric. Texture (`compose_v3.py`): the join is painted as a continuation of the cdr1 neck in neck
coordinates (arc length along the neck, angle round it from the surface normal): each texel takes the Meshy cdr1
neck paint at the same angle, whole plate periods (5 cm, the autocorrelation peak of the plates) further back, so
plates keep shape, size and spacing up to the jaw; at the cut Meshy's own continuous paint hands over within 4 cm,
and in front of the stub plane it fades into the head paint (2 cm further on the throat). The head is
luminance-matched as before. Thin near-white lines on the head (a part-code interpolation bug of v3b's first bake)
fixed by baking the patch flag in its own channel. Loft stretch p99.9 in Attack **1.47** (v3a 3.75).

**3. Wing roots.** Diagnosis: inherited from the installed cdr1, not introduced by v3: identical weights and numbers
for cdr1 and v3a (`scripts/v3/wing_root_gate.py`). Wing-material vertices 4–25 cm from the body carried only 0.16–0.75
wing weight and the shoulder skin none, so the inner membrane lagged (it hung nearly static while the wing beat) and
stretched (root edges p99 **4.04**, max 8.6 in Standing); cdr1's uniform red paint hid it, the v3a texture showed it
(membrane cells next to dark hide on a split). Fix (`graft.py` 4b): the wing share rises from 0.5 at the junction to
1 at 15 cm along the wing, and shoulder skin within 14 cm takes up to 0.5 of the wing (falling off quadratically);
wing-bone proportions and body-bone proportions kept. Root stretch p99 **1.43** (max 3.1), shoulder skin p99 1.41
(cdr1 1.04), whole-body p99.9 in Standing **1.87** (v3a 3.65). Texture: the membrane region fades into the scale
region over the last 4 cm before the junction, so pale membrane meets the dark arm/shoulder through a gradient.

**Gates (v3b).** Symmetry: head and spines 0 mm, landmark pairs 0 mm, loft max 8.2 mm (cdr1 ring). Floor as cdr1
(lowest −0.6 mm in Hit); every colour and shadow LOD through every clip ≥ −0.66 mm. Winding 0. Viewer 3 tiers × 9
clips, no console errors. Motion IoU vs MM7 frames: flight 0.44, Attack 0.40, Hit 0.35, Death 0.35 (v3a 0.44 / 0.40
/ 0.36 / 0.35). Rebuild: `scripts/v3/build_v3.sh graft` (geometry, compose, runtime, viewer), gates
`work/v3b/gates.sh`, sheets `scripts/v3/shots_v3b.py`.

**Open for review:** the plates on the join are a little softer than on the cdr1 neck (copied texels on a refitted
surface); the throat directly under the jaw keeps the head's own paint; the wing root now pulls the shoulder skin
along (by design), which reads as a broader shoulder in the upstroke.

## v3 (v3a), 2026-10-21 — superseded by v3b above; export kept as `export/mm7_m182_v3a.glb`

Green, Blue and Red Dragon: MM7 descriptors 223–225 (internal `ADragon A/B/C`), palettes 183/184/185, frame scales
5.0 / 5.1 / 5.25. Batch M, model 7 ([BATCH_M.md](../mm7_batches/BATCH_M.md)). Batch-M rule: nothing is installed; the
project stops at its export, with the binding proposal below.

v3 follows the user's direction after rejecting v2 (2026-10-21): "just take MM6 cdr1, maybe change its head - like use
the one you have here and graft it on that body and use the rig/anims from the cdr1 and retexture the body". The MM6
Cover Dragon has nearly the same pose and anatomy as the MM7 Dragon (`feedback/2026-10-20/cdr1_vs_m182_x2.png`).

| Item | Value |
|---|---|
| Export | [`export/mm7_m182.glb`](export/mm7_m182.glb), sha256 `1256d45717e48cf99c9f05cd08b931e213fc3bc7fdd0f7a73011389affdaa2a8` |
| LOD0 | `export/mm7_m182_lod0.glb` (portable, no LODs), `export/lods.json` |
| Previous | v2 `export/mm7_m182_v2.glb` (sha `304080da…`), v1 `export/mm7_m182_v1.glb` (sha `ffdad6a5…`) |
| Base | installed MM6 cdr1 `assets_source/worlds/mm6/models/mm6_cdr1.glb` (sha `bb4effe1…`, = `../mm6_cdr1_reduce_claude/export/mm6_cdr1.glb`), copied to `work/v3/cdr1_installed.glb`; the cdr1 projects and installed files are untouched |
| From cdr1 | body, wings, 36-bone skeleton, skin weights of the body and wings, all nine clips byte for byte (Standing/Walking 0.75 s, Running 0.625 s, Fidget 1.5 s, Attack = Cast 1.0 s, Hit 1.125 s, Death 2.4167 s, Dead 1 s), bind space, socket bones, burn-map contract, LOD pattern |
| From v2 | the MM7 head (head texture-set piece of `dragon_master.blend`: skull, jaw, teeth, eyes, horns, crest/frill spikes) and the MM7 tier palette method |
| New | lofted neck joint, 40-blade MM7 dorsal spine row, retexture (3 sets), region masks and ramps, iris colour per tier |
| Variants | `m182_a` Green (183), `m182_b` Blue (184), `m182_c` Red (185): one material per tier and set, sharing every image |
| LODs | colour 7,056 / 4,208 / 2,338 / 1,649 triangles (body 3,885 + head 1,807 + wings 1,364 at LOD0; body and head halve per step, the wing membranes stay whole in every LOD as in the installed cdr1); shadow LODs of the same counts tucked inside |
| Editable | `work/v3/uv_master.blend` (rig, clips, runtime UVs); rebuild `scripts/v3/build_v3.sh` |
| Viewer | [review/viewer](http://127.0.0.1:8912/level_generation/creatures/mm7_m182_claude/review/viewer/) — 3 tiers × 9 clips, no console errors (`review/viewer_check.json`); v2 in `review/viewer_v2/` |
| Meshy | **75 / 100 credits**: v1 35 (unchanged), v3 40 = retexture body 10, head 10, wings 10 (superseded), wings v3b 10 |

## v3 route (scripts in `scripts/v3/`, `build_geometry.sh` → `compose_v3.py` → `build_runtime_v3.sh`)

1. **Base** (`import_cdr1.py`): the installed cdr1 GLB imported, seam duplicates welded (UVs per corner), LOD meshes
   dropped. cdr1 is already near-symmetric (mirror-to-surface median 0.46 mm); it is kept as installed.
2. **Head scale and placement** (`graft.py`). Measured on the restored MM7 frames at the fitted scale: the native head is
   long (snout to horn base 77 x2 px ≈ 0.41 m) and narrow (skull 27 x2 px ≈ 0.15 m); the v2 head is short (length /
   width 1.4 against ~2.8). Compromise kept close to the v2 head the user asked for: uniform 4.3× about the jaw hinge,
   the muzzle (in front of the hinge, soft transition) 1.2× longer, the horns 1.25× and cheek spikes 1.2× longer about
   their roots (native horns are longer than Meshy's). The v2 jaw hinge sits exactly on the cdr1 `Jaw` bone, so the
   cdr1 jaw rotation opens the new jaw about its own hinge (Attack opens to 0.55 rad at 0.33 s; teeth, mouth floor, no
   tearing: `review/shots/attack_jaw_a.png`). No rotation: both heads point ~11–12° nose-down at rest. Result: snout
   at y −1.62 (cdr1 −1.54), head 0.42 × 0.45 × 0.44 m with crest.
3. **Neck cut** (`graft.py plane`, `cut_cdr1.py`): plane through the cdr1 neck centreline at y −1.09 (normal = its
   tangent); vertices within 12 mm snapped onto the plane, Blender bisect (UVs and weights interpolated), ring edges
   under 40 % of the mean merged: one planar 24-vertex ring. All cdr1 head pieces (horns, teeth, crest, neck spikes)
   beyond the plane removed.
4. **Graft and loft** (`graft.py`, `build_mesh.py`): the v2 head piece (its own 22-vertex back ring) split to 24
   vertices, so both seams join the loft with quads only (matched counts, no zipper; watertight). The loft is 0.17 m,
   six rings, Hermite centreline between the two ring axes, rotation-minimising frames, cross-sections blended per
   matched vertex including the head ring's out-of-plane throat V; positions blended linearly (`relax_loft.py`; the
   first smoothstep version crowded the nape and folded 6× in Attack).
5. **Weights**: cdr1 vertices keep theirs; head vertices take the v2 weights of the same-named bones (Head, Jaw,
   Neck1–3); loft weights blend the two rings; a 7-ring Laplacian band (24 passes, jaw excluded) across both seams.
6. **Spine row** (`add_spines.py`, `sym_spines.py`): the cdr1 dorsal spikes (20 small separate pieces) replaced by 40
   swept leaf blades (closed shells, 22 triangles each) along the dorsal midline from behind the frill to the tail
   tip, sized from the native side frame (neck 6–7.5 cm, tail base up to 14.5 cm, tip 5 cm), each rigid to its root's
   skin weights, then turned exactly onto the midline plane.
7. **UVs** (`uv_v3.py`, `meshy_uvs.py`): fresh smart-project UVs for the body set (cdr1 body, loft, spines) and the head
   set, the cdr1 wing layout kept; runtime layouts body [0,.92]², head and wings [0,.86]². Every upload carried the
   whole dragon (target set large, the other two small) so neighbouring sets get one scale size. Packing is not
   bit-reproducible, so the runtime UVs are restored triangle by triangle from the Meshy returns.
8. **Masters** (`references_hd_v3/`, `proxy_scene.py`). The v2 Codex masters show the MM7 wing shape (three thin
   fingers) and do not fit the cdr1 wings; a new Codex run from the native frames plus clay renders of the v3 model
   could not hold the silhouette (`references_hd_v3/codex_attempt/`, Codex's own check failed it). Used instead:
   render-guided masters of the v3 model itself in its rest pose (exact silhouettes) with proxy paint: cdr1 body paint
   and v2 head paint recoloured with the v2 MM7 tier-A ramps, procedural light grey-green 3 cm membrane cells, yellow
   spines. No native sprite or x2 frame went to Meshy. Set `b/` classifies the membranes by distance from the wing bone
   chain (`wing_classes.py`); set a's thin-shell ray test left the inner panels as dark arm.
9. **Retexture** (meshy-7, original UVs, PBR, 4K): body, head (set a), wings (set b). Meshy reproduced the proxy look
   with fine detail: dark green scales, segmented gold plates, crisp pale membrane cells, dark wing arms.
10. **Compose** (`compose_v3.py`, `bake_maps.py`): per-texel rest position/normal/part/membrane maps and AO baked in
    Cycles; 2K maps. Neck seam: the loft texels are repainted from their mirror images across the cdr1 cut plane
    (continuous with the cdr1 neck) and across the head ring (continuous with the head), cross-faded over the middle
    of the loft (gold throat plates keep the body donor to the chin); head hide and gold luminance quantile-matched to
    the body; a 6 cm band behind the ring takes the loft's mean colour; pale seam texels inside the hide and gold
    regions compressed to the 96th percentile (they became white lines under the ramps). Classes: spines = the blades
    and the head frill; ivory = horns, teeth, claws, wing spurs (Meshy's cyan specks there too); eyes painted by
    position (iris, slit pupil). Region mask R scales, G membranes (head set: iris), B ventral gold, A spines; material
    class maps; MR red = specular mask, green = roughness.
11. **Ramps**: each tier's own palette per region (index sets of the restored package; membranes only the grey-green
    side-view entries; spines the saturated accent entries; iris the eye entries 86/87: red, green, amber). Colour
    from the palette, brightness from the texel (the sea-serpent route): plain rank matching (v2) mapped Meshy's light
    scale centres onto the sprites' baked highlights and turned the hide grey. Rank windows: hide 10–85 %, membranes
    15–95 %, gold 35–98 %, spines 40–98 % (olive shadow entries made the blue tier's belly green).
12. **Runtime** (`build_runtime_v3.sh`): geometry export → `swap_lod0.py` into the installed cdr1 GLB (bind space
    asserted identical; clips, sockets, materials, variants kept) → `claude_shared/bake_burn_maps.py` (burn maps for
    the new UVs) → `apply_textures_v3.py` (maps, ramps, variants renamed `m182_a/b/c`) → `tools/build_actor_lods.py`
    → `preserve_wing_lods.py` → `shrink_shadow_lods.py` → `carry_variants.py` → winding check.

## Gates

- **Symmetry** (`review/symmetry_gate.json`): head 0 mm (943/943 vertices exactly mirrored), spines 0 mm, landmark
  pairs eye / horn tip / wing tip / fore claw / hind claw 0 mm, paired bones 0.001 mm, centre bones on x = 0; cdr1 body
  and wings as installed (mirror-to-surface median 0.23 mm, p99 5.3 mm); neck loft median 1.6 mm, max 8.3 mm (it
  starts on the cdr1 ring). Head weight mirror error 0.024 (seam smoothing from the cdr1 side).
- **Motion vs native** (`review/motion_gate.json`, sheets `review/motion_vs_native/<clip>.png`, cdr1 clips sampled at
  the MM7 native times: flight proportional, Attack impact-aligned 0.5 → 0.75 s, Hit/Death proportional): silhouette
  IoU mean (min frame) Standing / Walking / Fidget **0.44 (0.37)**, Attack **0.40 (0.28)**, Hit **0.36 (0.31)**,
  Death **0.35 (0.29)**; v2 0.62 / 0.59 / 0.63 / 0.60. Lower than v2 by construction: the cdr1 clips are not fitted to
  the MM7 frames and the cdr1 wings are broad (5 fingers) where the MM7 wings are thin (3 fingers). Clips are not
  re-timed (MM7 tables: flight 0.9375 s, attack 0.875 s with impact 0.5 s; not a clear need against the cdr1 timing).
- **Floor and stretch** (`review/animation_gate.json`, 48 Hz): lowest vertex as the installed cdr1 (Hit −0.6 mm, Death
  0, Dead 8.7 mm, flight 35 mm); the head never comes below 0.2 m. Loft edge stretch p99.9: Attack 3.75 (nape
  compression in the head dip), other clips ≤ 1.37; the cdr1 body itself 2.97 in Attack.
- **LODs** (`review/lod_motion_checks.json`): every colour and shadow LOD through every clip, lowest −0.66 mm.
- `check_winding.py export/mm7_m182.glb`: **0 inverted closed parts**.
- Viewer: 3 tiers × 9 clips, 27 switches, no console errors.

Shots (`review/shots/`): `front_a`, `q_a`/`q_b`/`q_c`, `front_b`/`front_c`, `wings_a`, `attack_a`, `hit_a`, `dead_a`,
`rear_a` (viewer); `neck_closeup_a/b/c` (Blender: side, below, above, front; engine ramp rule baked), `attack_jaw_a`
(jaw open), `tiers_vs_native.png`. v2 shots in `review/shots/v2/`, v1 in `review/shots/v1/`.

## Size and binding

Scale **462.23** (tier A): silhouette IoU fit of the Standing clip against the restored standing/flight frames, all
five views (`scripts/v3/scale_fit.py`, `work/v3/scale_fit_standing.json`: 92.45 native px per model metre × 5.0; area
method 491.7). B and C follow by frame scale. Binding proposal (not applied):
[review/actors_binding.yml](review/actors_binding.yml): the cdr1 animation block (cast `Cast`, impacts 0.382 / 0.75 s,
stride 1.0, `upper_body_root: Spine1`), the jaw socket re-measured for the longer muzzle (`[0, 0.1558, 0.0768]` in
Jaw space), no death effect (the MM7 dragon leaves a corpse, native `m182xa0`; cdr1's burn maps are embedded, so its
burn effect can be enabled by copying its `death_effect` block).

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m182_claude/export/mm7_m182.glb --world mm7
```

## Findings for artistic review

- **Head size** is a compromise: 4.3× the v2 head with a 1.2× longer muzzle reads a little longer than the cdr1 head;
  the native MM7 head is longer still (~0.41 m) and narrower. One parameter in `work/v3/graft_params.json`.
- **Neck**: the cdr1 neck is thinner than the MM7 neck; the loft widens into the head ring at the nape. The loft paint
  is rebuilt from both neighbours; up close the nape top shows faint streaks in the cross-fade, and under the jaw a
  small mottled patch where head and body paint meet. No white patch or pale stripe in any tier
  (`review/shots/neck_closeup_*.png`).
- **Wings** are the cdr1 wings (broad, five spurs), retextured pale grey-green with fine cells and dark arms; the MM7
  sprite has thinner three-finger wings, which the user chose to keep from cdr1.
- **Motion** is cdr1's (accepted for cdr1); IoU against the MM7 frames is lower than v2's fitted clips.
- **Corpse**: cdr1 Death ends lying flat belly-down; the native MM7 corpse lies on its side.
- In game not checked (batch M); the jaw socket offset should be verified with a ranged attack glow.

## v2 (2026-10-21, superseded by v3; export kept as `export/mm7_m182_v2.glb`)

Green, Blue and Red Dragon: MM7 descriptors 223–225 (internal `ADragon A/B/C`), palettes 183/184/185, frame scales
5.0 / 5.1 / 5.25. Batch M, model 7 ([BATCH_M.md](../mm7_batches/BATCH_M.md)). The MM7 Dragon is not the MM8 `m492`
body (identity check: `review/identity_check.json`), so it is a new model. Batch-M rule: nothing is installed; the
project stops at its export, with the install command and binding below.

v2 answers the user review of v1 (2026-10-20, `feedback/2026-10-20/`): "base dragon not symmetric but crooked, wings
are terrible quality, head needs better graft (pale seam under the jaw and down the neck), match the native movement
closely, also during walking/hit".

| Item | Value |
|---|---|
| Export | [`export/mm7_m182_v2.glb`](export/mm7_m182_v2.glb) (was `export/mm7_m182.glb`), 28 MB, sha256 `304080dac26fc99292b8930f3a54547e361e88d488504972aa7c1dd407f0c4f3`; LOD0 `export/mm7_m182_lod0_v2.glb`, `export/lods_v2.json` |
| Previous | `export/mm7_m182_v1.glb` (sha `ffdad6a5…`), `export/mm7_m182_lod0_v1.glb`, `export/lods_v1.json`, `work/dragon_master_v1.blend` |
| Variants | `m182_a` Green (183), `m182_b` Blue (184), `m182_c` Red (185): one material per tier sharing every image, region ramps only |
| LODs | colour 18,254 / 9,120 / 4,552 / 2,259 triangles (body 12.8k + wings 5.5k at LOD0); shadow LODs of the same counts, tucked 1.5–4 mm inside |
| Clips | Standing / Walking 0.917 s (22 frames), Running 0.75 s, Fidget 1.83 s, Attack = Cast 0.875 s (impact 0.5 s), Hit 0.875 s, Death 1.25 s, Dead 1 s |
| Rig | 43 bones: Root, Spine1–2, Neck1–3, Head, Jaw, Tail1–10, per side Wing0–3 + WingF2/WingF3 (trailing fingers), Fore/Hind Upper/Lower/Foot, `Socket_Mouth`; 4 influences; exactly mirror-symmetric |
| Editable | `dragon_master.blend` (packed); portable LOD0 `export/mm7_m182_lod0.glb`; rebuild `scripts/build_v2.sh [step]` |
| Viewer | [review/viewer_v2](http://127.0.0.1:8912/level_generation/creatures/mm7_m182_claude/review/viewer_v2/) (copy of the v2 viewer; `review/viewer_check_v2.json`) |
| Meshy | **35 / 100 credits, unchanged by v2 (0 spent)**: v1 Smart Topology 5, body 10, head 10, wings 10 |

### v2 route (scripts in run order; `scripts/build_v2.sh` replays everything after the fits)

1. **Straighten** (`sym_v2.py`, `midline_field.py`, `straighten.py`). Meshy built the three-quarter master's lean into
   the mesh: the head was turned 9.8° (yaw) and rolled 4.4°, and trunk/neck/tail cross-sections sat up to 3 cm off
   x = 0 and sheared (v1 mirrored-vertex distance: median 11.6 mm, p99 58 mm). The head's own mirror plane is fitted
   (reflection fit) and the head turned rigidly onto x = 0, the upper neck taking the turn gradually; then a midline
   field c(y, z) (midpoint of the body's x-interval on a 2 mm grid, limbs rejected, smoothed 12 mm) is subtracted.
2. **Mirror** (`mirror_half.py`). The +X half (left wing, flank, legs: the cleaner side) is kept and symmetrized onto
   −X with a 0.4 mm weld; flat in-plane slivers and stray right-foot claws that crossed the plane are dropped; a
   12 mm midline band is relaxed symmetrically. No duplicate vertices on the midline.
3. **New wings** (`shoulder_envelope.py`, `clean_shoulder.py`, `build_wing.py`, `assemble_wing.py`). The Meshy wing
   (frontal, ragged, doubled membrane, blotchy paint) is cut off at |x| = 0.075 and the shoulder rebuilt (arm stub and
   flaps removed against an inpainted flank envelope, holes filled, relaxed, re-symmetrized). The procedural wing is
   built from the broadside native planform (restored `m182sa2`, 2.2 mm per x2 pixel): arm, long leading finger with
   knuckle, two trailing fingers, ivory thumb claw and finger-tip claws, scalloped trailing edges, a 1.2 mm
   double-layer membrane with a rim (closed shell), slight billow between the fingers, the root band laid onto the
   body. Both sides share one UV layout (right = mirror of left). Analytic weights: wing bones by inverse distance,
   the body taking over within 80 mm of the root line (spreads the stroke stretch over the inner panel).
4. **Reduce, rig, UVs** (`reduce_v2.py`, `rig_v2.py`, `uv_v2.py`). Symmetric protected decimation of the body only
   (wings, crest tips and claws kept), then the v1 weight rules (head/jaw/cheek ownership, leg domains, soft roots,
   crest shells rigid) evaluated on +X and mirrored to −X (midline vertices averaged, L/R partners dropped in pairs
   at the 4-influence limit). Body and head UVs unwrap the +X half (body: neck/trunk/tail as one angle-based chart
   each, 52 % of the square; 3,744 texels/m median) and copy them to the mirrored faces.
5. **Textures** (`make_bake_source.py`, `bake_v2.py`, `uv_raster_v2.py`, `wing_texture.py`, `throat.py`,
   `neck_seam.py`, `compose_v2.py`). Body and head paint: the v1 Meshy retextures (body 4K, head 2K) baked
   selected-to-active from the straightened v1 mesh (+X side) onto the new layout; missed texels (the rebuilt shoulder)
   take the low-passed nearest colour plus scale detail from 5 cm down the flank. Wings: procedural 2K set from
   physical coordinates (so both layers and both wings match): fine reticulated cells with darker borders, branching
   darker veins from the fingers, dark scaled bones, ivory claws; no low-frequency noise and no AO on the membrane
   (the shared texels of the two layers baked AO clouds). Throat: the white patch under the jaw and the pale stripe
   down the neck (Meshy never saw the throat; the head hides it in the front master) are repainted with gold plates
   phase-locked to the last clean chest plate (period 25 mm measured from the chest), narrowing to the chin and
   continuous across the head/body seam; the head set's colour is matched to the body in a 15 mm seam band (gain
   1.04 / 1.26 / 1.46 per channel, fading over 40 mm). Region mask and tier ramps as v1 (scales, membranes, ventral
   gold, spines); the membrane ramp samples only the grey-green entries of the native membrane set in the side views
   and maps texture rank q to native rank 0.25 + 0.5 q^0.8 (the set also holds the dark edge-on shading, the yellow
   dorsal accents and baked highlights, which made v1's membranes dark green with white flecks); the spine ramp drops
   the near-white top 15 %.
6. **Clips from the native frames** (`dragon_pose.py`, `fit_native.py`, `clip_tables.py`, `animate_v2.py`). Camera
   calibrated on the standing frame (all five views): elevation 1.1°, 252.6 px/m at 288 px (= binding scale 1,263).
   Every native frame of the flight loop (sa, wa–wf), attack (aa–af), hit (na–nf) and death (na–nc, da–dc, corpse xa,
   dd) is fitted by silhouette over all five directions (death da–dd: front view only, as in game) with numpy skinning
   identical to Blender's (2e-7 m); the corpse is fitted as a side-lying body with the wings fixed flat (constrained to
   lie on its trunk). Keys sit at the native times (flight 0 / .125 / .25 / .4375 / .625 / .75 / .875 s of 0.9375 s;
   actions every 0.125 s) and are spline-interpolated (periodic for the loop); minor parameters are half-smoothed.
   The native body bob comes from the frames' vertical alignment. Bite: jaw opens to 0.44 rad at 0.5 s (native ad).
   Hit wing sweep is limited to ±0.4 rad (membrane root). Floor: constant flight lift (0.206 m: the dragon hovers
   with its feet clear, as the native frames float), tails lifted by a smoothed extra pitch, half-frame dips fixed.
   Walking = Standing (MM7 uses one group m183w for both); Running = the same strokes faster and 0.08 rad more
   forward lean; Fidget = two strokes with a look to each side.

### Gates

- **Symmetry** (`review/symmetry_gate_v2.json`, passed): mirrored-vertex distance median / p99 / max **0 / 0 / 0 mm**
  (v1: 11.6 / 58.4 / 86.2 mm); landmark pairs eye, horn tip, fore claw, hind claw, wing tip **0 mm** (v1: 10.0, 15.7,
  58.0, 17.7, 86.2 mm); paired bones mirror exactly, centre bones on x = 0, weight mirror error 0.
- **Motion vs native** (`review/motion_gate_v2.json`, sheets `review/motion_vs_native/v2/<clip>.png`): silhouette IoU
  against the restored x2 frames at the native times and directions, mean (min frame): Standing / Walking / Fidget
  **0.62 (0.57)**, Attack **0.59 (0.55)**, Hit **0.63 (0.62)**, Death **0.60 (0.47, frame da)**; v1 clips on the same
  gate: 0.40 / 0.40 / 0.40, 0.40, 0.38, 0.35. The ceiling is the body shape (the Meshy body is heavier and its
  crest/frill spines smaller than the sprite's): the best fit of the standing frame reaches 0.72 soft IoU.
- Animation (`review/animation_gate_v2.json`, 48 Hz): no vertex below z = 2 mm (Attack lowest 116 mm), loops close,
  Death end = Dead, Attack = Cast; edge stretch p99.9 flight 1.80, Attack 1.97, Hit 2.32, Death/Dead 2.67.
- Reduction (`review/reduction/step_v2_*.json`, candidate vs unreduced mesh through every clip): step 6 (18,255)
  p99 ≤ 0.88 mm, max ≤ 6 mm, passes; step 7 (16,429) fails Hit/Death (p99 1.06–1.10 mm). Step 6 kept.
- LODs and shadow LODs through every clip at 24 fps (`review/lod_motion_checks_v2.json`): lowest 0.19 mm.
- Reimport of the export (`work/export_check.json`): every clip present, floors as the master.
- `check_winding.py export/mm7_m182.glb`: **0 inverted closed parts**.
- Viewer: 3 tiers × 9 clips, 27 switches, no console errors.

Shots (`review/shots/v2/`): `front_a`, `q_a`/`q_b`/`q_c`, `front_b`/`front_c`, `neck_closeup_a` (front, side, low; Blender
render: the viewer's head focus frames the wing tips), `wings_a` (broadside), `wings_down_a`, `walk_a`, `attack_a`,
`hit_a`, `dead_a` (Blender), `rear_a`, `tiers_vs_native.png`. v1 shots are kept in `review/shots/v1/`, v1 textures in
`textures/v1/`.

### Size and binding

Scale **1,263** (tier A) from the silhouette calibration against all five native standing views (5 world units per
native pixel); v1 used 1,210 from silhouette area with its frontal wings. The area method on the v2 cycle gives 1,382
(front 1,392, side 1,373; `review/scale/measurement.json`) because the v2 wings fold more of the time; the fitted
scale is the direct measurement. B and C follow by frame scale (`scale_reference: ADragon A`).

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m182_claude/export/mm7_m182.glb --world mm7
```

Binding for `assets_dev/worlds/mm7/models/actors.yml`: [review/actors_binding_v2.yml](review/actors_binding_v2.yml)
(`cast: Attack`, mouth socket glow and release at 0.5 s, stride 0.15 / 0.12 model units per cycle).

### Findings for artistic review

- **Wing colour:** the membrane ramp follows the native broadside membrane (median sRGB ~100/110/85 × 1.3 gain);
  in the viewer a top-lit horizontal wing reads pale grey-green (`q_a`), while the side-lit wing matches
  `m182sa2`. The native frames also show yellow flecks in the membrane, which the procedural texture leaves out
  (they fall in the spine/accent palette range and would be recoloured per tier).
- **Corpse:** native `xa` is front-only (belly to the viewer, head left); the model lies on its right side with the
  top wing draped over the back, so from other directions it reads as a dragon on its side.
- **Throat plates** are procedural (gold, phase-locked to the chest plates); they read continuous at game distance,
  the close-up shows the change in plate style at the base of the neck.
- Hit and Death keep the native rearing/twisting poses; their membrane-root stretch (p99.9 2.3–2.7) is above flight.
- Motion IoU is bounded by the body shape (heavier body, smaller crest than the sprite), not by timing.
