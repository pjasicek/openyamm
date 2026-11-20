# The Noble bosses — Lord Vhorrax, the Coil Keeper, the Conductor, the Hierarch (Claude E, Round 4)

[CREATURE_BUILDS](../../../design/kreegan_world/WORK_PACKAGES/CREATURE_BUILDS.md) Round 4 "Claude E": rows **10105/10106**
Lord Vhorrax (×1.4), **10108** the Coil Keeper (×1.3), **10109** the Conductor (×1.3), **10120/10145/10146** the
Hierarch (×2.2: in person, enthroned, faltering). All on the published winged Kreegan body
(`hes_overseer_codex/export/hes_kreegan_winged.glb`, copied to `source/`; the Overseer project is unchanged): no tail,
no transplanted harness.

**Status (2026-10-24): built, staged, viewer-checked and desktop-smoked (D5, D6, D11, D12, D16: 0 model load
failures). Accepted technically by the integrator (openyamm-30; `requests/P3.md`, "Integrator answer: the Noble
bosses"). Follow-up round (integrator, the same day) done: an own skin per boss through the region ramps, and the
Hierarch's throne as a permanent D12 decoration instead of 10145's attachment ("Follow-up: skins and the D12 throne" in
P3), accepted by the integrator the same day; the package is closed. User acceptance of the 3D is not recorded.
Lease released; no work pending.**

[Viewer](http://127.0.0.1:8912/level_generation/creatures/hes_noble_bosses_claude/review/viewer/) ·
[viewer sheet](review/viewer_sheet.jpg) · [skins sheet](review/skins_sheet.jpg) ·
[in game, skins](review/ingame/lineup_skins/frozen.png) ·
[D12 throne decoration, before/after phase 2](review/ingame/d12_throne_deco/before_after.jpg) ·
[attachment vs decoration](review/ingame/d12_throne_deco/attachment_deco_phase2.png) ·
[desktop smoke](review/desktop_smoke_final.json)

## Concepts

`boss_vhorrax.png` and `boss_hierarch.png` were approved. The Coil Keeper and the Conductor had none: briefs
`CODEX_BRIEF_COIL_KEEPER.md` / `CODEX_BRIEF_CONDUCTOR.md`, two candidates each by Codex (`codex exec`). The user
rejected both first pairs (kept as `*_v1_candidate_*.png`): the Coil Keeper's glow colour (neither ice-blue nor
white-gold), the Conductor drifting from the Noble carapace. Redo picks (user, 2026-10-24): **Coil Keeper candidate 2**
(deep electric violet coils and spear core), **Conductor candidate 1** (violet-white orb, throat node, arm plugs).
Recorded in the `generation_runs_*.json` approval blocks.

## Route (why this one)

The bosses keep the shared body, rig, clips and accepted grips; what makes each one is a **fitted carapace shell**:

1. **Exact-body guides** (`render_guides.py`): the winged body in its rest pose, wings removed, from the five master
   cameras (1024×1536; ortho front/back/left/right, perspective three-quarter); the cameras' projection matrices are
   kept in `references_hd/guides/cameras.json`.
2. **HD masters** (`references_hd/CODEX_BRIEF.md`, Codex): each boss's armour painted *onto the guides* (same
   framing, pose and bare parts). `register_masters.py` checks the registration (scale 1.0 for most views; the
   Conductor's and Hierarch's side/front drift ≤ 7 %).
3. **Meshy multi-image to 3D** (front/left/back/right masters, `meshy-6-lite`, mesh only, 5 credits) per boss.
4. **`fit_shell.py`**: the Meshy figure aligned onto the body (four yaws, a scale search with rigid ICP, then a damped
   per-bone correction blended by the skin weights: median 1.0–1.7 cm); every face classified by signed distance to
   the skin and the masters' colours projected through the guide cameras (gold/ivory/glow = armour, violet = skin);
   majority filter, island and hole cleanup; hands, feet, head (except the crown box) and the wing roots excluded.
   `--drop` boxes remove what is rebuilt procedurally (the Coil Keeper's coils, the Hierarch's cable tubes and
   below-knee panel).
5. **`shell_finish.py`**: decimate to 5,000 (Vhorrax 5,800), small islands dropped, faces away from the skin, ≥ 6 mm
   clearance; the body's weights transferred, arm-to-leg bridges cut, weights kept only within 2 cm of the skin and
   diffused outward through the shell, a pelvis/thighs mix between the legs, smoothed (four influences, wings zeroed);
   the skin the shell covers removed (`Body_<boss>`).
6. **Texture**: xatlas UVs (`uv_shell.py`); a **Meshy retexture** of the original figure with the four masters
   (10 credits) baked onto the shell (`transfer_tex.py`: Cycles selected-to-active; the retextured figure is mapped
   back onto the aligned one exactly, residual < 1 µm): base colour, tangent normal, roughness (metallic dropped:
   runtime contract). My own projection bake (`paint_bake.py`) was tried first and came out mottled: the painted plates
   do not sit exactly on Meshy's plates. `grade_gold.py` lifts the gold toward the concepts (raw bakes kept).
7. **Procedural signature add-ons** (`make_addons.py`, rigid, palette-textured `<Boss>_AddOn` + emissive
   `<Boss>_AddGlow`): the Coil Keeper's two glass coil capsules between the wing roots; the Conductor's three arm cables
   with glowing plugs and the throat node; the Hierarch's fused-bone crown and five spinal cables with glowing plugs
   (spine-to-pelvis weights). Meshy only produced fragments of these.
8. **Weapons** from flat Codex paintings of the concept weapons (`references_hd/weapons/`): `weapon_relief.py`
   inflates the silhouette (round hafts, thin blades) and projects the painting on both faces; `make_attachment.py`
   writes it in the **`Weapon_R` frame, an exact copy of the Overseer's accepted `CollarRod` grip**, with a 3 cm grip
   sleeve (the accepted fist is fitted to a 3.2 cm handle). No Meshy for weapons.
9. **Clips**: the seven accepted Overseer clips (`Noble_Flight/AttackMelee/AttackRanged/Cast/Hit/Death/Dead`; the
   staff/rod grip carries saber, halberd and staff; the left pistol hand relaxed, the Hierarch's right hand too), plus
   `extra_clips.py`: `Noble_WingSpread` (all four; the Hierarch's `wing_spread`, Vhorrax's scripted `fidget`) and the
   enthroned set `Noble_Seated` (4 s loop) / `Noble_SeatedCast` (release 0.45 s) / `Noble_SeatedHit`.
10. **The throne**: Codex masters (`CODEX_BRIEF_THRONE.md`), Meshy multi-image with texture (15 credits),
    `fit_throne.py` under the seated pose (`export/hes_hierarch_throne.glb`, the `Throne` joint's frame). Since the
    follow-up it is a **D12 decoration**, not an attachment: `throne_decoration.py` exports the same fitted throne in
    metres with its origin at the actor's feet (`export/hes_hierarch_throne_deco.glb`, 5.0 m, 3,000 / 1,500 / 750 /
    360 triangles, linked static LODs, orange glow). It stays when D12 hides 10145 at phase 2.

## Runtime (`TOK=<lease> scripts/build_all.sh`)

Shell chain per boss first (`fit_shell` → `shell_finish` → `uv_shell` (venv) → `shell_material` → `transfer_tex` →
`make_addons`), then `build_all.sh`: grading; `build_runtime.sh` per boss (`assemble.py` with the `Weapon_R`,
`Socket_Tip`, `Socket_Palm_L/R`, `Throne` joints → `set_skin.py` (own skins below) → `prepare_actor_glb` → `lods.py` (fitted ratios
.55/.30/.15) → `shrink_shadow_lods` → burn maps (`bake_burn_maps` + `burn_maps`, every skinned material) → emission
(shell seams by mask, add-on glow) → key times, winding) and the weapon (relief, sleeve, LODs, emission); the
Hierarch's `hierarch`/`hierarch_dark` variants (`add_variants.py`: the faltering cables dark); the throne; the viewer.
`work/venv`: pymeshlab, xatlas, numpy, scipy, Pillow.

**Skins** (integrator follow-up): each boss its own skin through the region mask and ramps only, no baked colours.
`set_skin.py --skin RRGGBB` restores the tier's region mask, ramps and specular from the published winged body (the
Blender round trip drops material extras, so before this all four showed the base plum), scales the skin ramp (mask R)
so the median skin texel lands on the colour, and gives the shell its own skin mask (its violet-painted texels) with a
ramp of the same profile. Lord Vhorrax **oxblood #5a1f1f**, the Coil Keeper **storm blue #2f4a7a**, the Conductor
**pale lilac #a898c0**; the Hierarch keeps the concept plum (no `--skin`; `hierarch_dark` unchanged). None is a Court
skin or a caste tier colour. All hexes kept: each reads against the gold. In game the storm blue looks brighter and
more saturated than the hex, and the oxblood reads as brick red.

| Export | LOD0 | LODs | + attachment |
|---|---:|---|---|
| `hes_vhorrax.glb` | 13,496 | 7,420 / 4,047 / 2,023 | `hes_vhorrax_courtesy.glb` 1,237 → **14,733** |
| `hes_coil_keeper.glb` | 13,764 | 7,566 / 4,133 / 2,075 | `hes_coil_spear.glb` 991 → **14,755** |
| `hes_conductor.glb` | 13,428 | 7,381 / 4,023 / 2,008 | `hes_conductor_baton.glb` 1,139 → **14,567** |
| `hes_hierarch.glb` | 14,247 | 7,831 / 4,269 / 2,134 | none (the throne is D12's decoration) |

All exports: key times PASS, 0 inverted closed parts, burn maps on every skinned material, PNG images only.

## Bindings (`integration/actors.yml`; staged through `hesper_stage/monsters.yml`)

| Row | Descriptor | Scale | Notes |
|---|---|---:|---|
| 10105, 10106 | Lord Vhorrax | 182 | saber on `Weapon_R`; `script_clips: fidget → Noble_WingSpread` |
| 10108 | The Coil Keeper | 169 | halberd; `script_clips: cast → Noble_Cast` |
| 10109 | The Conductor | 169 | staff, grip 0.45 m from the butt (was `sprite_only`) |
| 10120 | The Hierarch | 286 | skin `hierarch`; `script_clips: wing_spread` |
| 10145 | The Hierarch (enthroned) | 286 | seated clips (sits in D12's throne decoration); dying/dead stay seated |
| 10146 | The Hierarch (faltering) | 286 | skin `hierarch_dark` (spinal cables dark) |

Ranged bolts release at `Socket_Palm_L` (impact 0.45 s, the accepted ranged clip), casts at the weapon tip
(`Socket_Tip`; the Hierarch's right palm), melee impact 0.864583 s (the Overseer's measured staff contact). Burn death
in each boss's colour. Row heights/radii unchanged.

## Checks

- Viewer `check` (after the skins): 6 models, 48 switches, every clip, no console errors. Shots in `review/shots/`.
- Desktop smoke (`scripts/desktop_smoke.py final ...`, also fails on "decoration models failed to load"): D5, D6,
  D11, D12, D16 completed, **0 model load failures**.
  (An earlier attempt crashed on every map, including a control map without these rows: another session's engine
  rebuild; and D11 refused the actors file over the Nobles' `look` blocks, fixed by openyamm-b2.)
- `scripts/gates.py` (`review/gates_<boss>.json`, every clip at 12 Hz): shell edge stretch p99 **1.72 / 1.99 / 1.74 /
  2.56** (Vhorrax / Coil Keeper / Conductor / Hierarch), max 8–14: the shell is skinned like skin, comparable to the
  body's own accepted arm skin (p99 ≈ 1.8 in the Overseer gates). Weapon in body **0 mm** on every clip. Three fixes
  got there (`shell_finish.py`): weights near the skin only, diffused outward through the shell (spurs move with their
  base; a Hierarch maximum of 329 → 14), arm-to-leg/flank bridges that Meshy fused cut, a skirt mix between the legs;
  the Conductor's grip moved toward the butt (the 0.62 m butt went 7 cm into the hip in Flight). The add-on test
  flags the deliberately embedded roots (coil cables into the spine plates, crown spike bases, forearm sockets);
  renders show the coils clear of the back plate. The skin-poke counter is noisy at shell rims; renders of the
  extreme poses show no poke-through.
- `rebuild_all.sh --scenarios-only` (final stage, after the follow-up): **103/103 PASS**, exit 0.
- D12 throne decoration (`review/ingame/d12_throne_deco/`): before phase 2 the seated Hierarch sits in it as he did in
  the attachment (`attachment_deco_phase2.png`: attachment, decoration, after phase 2); after `actor kill 2400` (the
  conduits die, the timer runs phase 2) 10145 is hidden, 10120 stands up beside it and the throne stays. 0 inverted
  closed parts.

## Meshy (lease `hesper:noble_bosses`, cap 80)

| Job | Kind | Credits |
|---|---|---:|
| `vhorrax_geo_v1`, `coil_keeper_geo_v1`, `conductor_geo_v1`, `hierarch_geo_v1` | multi-image to 3D, mesh | 4 × 5 |
| `vhorrax_tex_v1`, `coil_keeper_tex_v1`, `conductor_tex_v1`, `hierarch_tex_v1` | retexture 2K PBR | 4 × 10 |
| `throne_v1` | multi-image to 3D, mesh + 2K texture | 15 |
| **total** (backup account) | | **75** |

No paid animation (nothing to ingest into `anim_library`).

## Open points

- **The D12 throne** is a decoration (row `hes_hierarch_throne_deco`, staged id 934, radius 0: he and 10120 occupy
  the spot), placed by `level_generation/projects/hesper_d12/build_d12.py` `add_throne()`. That function adds a marker
  node to `source/hes_d12.glb` (cloned from a shelf-rack marker, moved on later runs) and an entity to
  `source/hes_d12.geometry.yml` in the throne room's `source_nodes`. Two conventions to keep: a map entity's
  `decoration_list_id` is the table row number minus 1 (`decoration_ids.yml` holds the number; the first try used it
  as is and the engine dropped the entity), and a decoration model's yaw 0 faces +Y while an actor's faces +X (the
  throne's facing is 180 for his 270).
- Clips are the Overseer's (staff grip for saber, halberd and staff; left-hand bolt): the Coil Keeper's halberd is
  one-handed, the concept shows two hands.
- The shell is skinned like skin (no rigid plates): it stretches with the body at the joints.
- The Hierarch's crown is procedural (Meshy's was too faint); his cables hang into the throne when seated.
