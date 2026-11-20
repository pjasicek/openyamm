# Hesper Acid Crawlers: three tiers (Claude quadruped project)

Native acid-spitting arthropods of the Hesper world ([concept](../../../design/kreegan_world/concepts/monsters/fam_crawlers.png),
brief `design/kreegan_world/concepts/monsters/CODEX_BRIEF_ZONE1_FAMILIES.md` section 3), monsters 10090 **Acid
Crawler** / 10091 **Brood Crawler** / 10092 **Crawler Matron** (`design/kreegan_world/data/make_monster_tables.py`),
met in D0-D2. Built with the [quadruped playbook](../CLAUDE_QUADRUPED_PLAYBOOK.md) (spider section),
[HD masters](../CLAUDE_HD_MASTER_REFERENCES.md) and [creature textures](../CLAUDE_CREATURE_TEXTURES.md).
**Exported, not installed** (the Hesper stage integrates it). Meshy: **25 of 60 credits**. Not checked in game (no
engine work in this task). User artistic acceptance is not recorded.

[Review viewer](review/viewer/index.html) (serve the creatures folder over http) · [tiers](review/tiers_abc.jpg) ·
[clips in the viewer](review/clips_viewer.jpg) · [clay clip sheet](review/clips_v1.jpg) ·
[gates](review/gates_v1.json) · [HD masters](references_hd/selected_views_review.png) · [playback](review/playback/) ·
[Blender tier preview](review/tiers_v1_blender.jpg)

## Deliverables

| File | What |
|---|---|
| `export/hes_crawler.glb` | body: one skinned mesh `Crawler`, LODs **7,529** / 3,763 / 1,355 / 450 triangles + shadow LODs (tucked 3-8 mm inside), 3 variants `crawler_a/b/c` (one shared skin, region mask + ramps), clips Standing, Walking, Running, Attack, Bite, Hit, Death, Dead, Fidget; non-deforming `Socket_Mouth` (spit release); attachment nodes `Pods`, `Sacs_F`, `Sacs_M`, `Sacs_R` |
| `export/hes_crawler_pods.glb` | B's egg-pod cluster (7 pods, 700 / 350 / 126 / 42 tris) on node `Pods` (child of Abdomen) |
| `export/hes_crawler_sacs_{f,m,r}.glb` | C's six swollen acid sacs, one pair per body segment (200 / 100 / 36 / 12 tris each) on `Sacs_F` (Thorax), `Sacs_M` (Body), `Sacs_R` (Abdomen); constant emissive (0.10, 0.17, 0.02) |
| `export/hes_crawler_lod0.glb`, `work/anim_v1.blend` | LOD0 export with every attachment joined; the editable keyed master |
| `textures/` | `hcr_basecolor_graded.png` (2K), `hcr_normal_1k`, `hcr_mr_1k` (R = baked AO, G roughness), `hcr_region_mask.png` + `hcr_ramps.json`, `hcr_material_classes.png`, `hcr_glow_mask.png` (engine need below), `hcr_pods.png`, `hcr_sacs.png` |
| `integration/actors.yml` | staged bindings for `hes_acid_crawler`, `hes_acid_crawler_brood`, `hes_acid_crawler_matron` (the monster table's Picture names) |

Install later (parent), from the repository root, into the Hesper stage's model set (not `assets_dev`):
`tools/install_model.py` on the five GLBs with the Hesper world target, then the three `integration/actors.yml` entries.
Run `check_winding.py` again on the installed copies (0 inverted closed parts on all five exports here).

## Tiers (one mesh, region mask + ramps, attachments per descriptor)

| Skin | Monster | Scale | Carapace (R) | Acid (G) | Limbs (B) | Eyes (A) | Attachment |
|---|---|---|---|---|---|---|---|
| crawler_a | 10090 Acid Crawler | 100 (1.0 m) | pale bone-grey | green | pale grey-brown | dark olive | none |
| crawler_b | 10091 Brood Crawler | 125 (1.25 m) | mottled rust-brown | yellow-green | rust-brown | amber | egg pods (`Pods`) |
| crawler_c | 10092 Crawler Matron | 150 (1.5 m) | violet-black | bright lime | dark violet-grey | lime | 6 acid sacs (`Sacs_F/M/R`) |

- Size: the brief makes tier A 1.0 m long; the monster table's art scales (0.8 / 1.0 / 1.2) give B 1.25 m and C 1.5 m.
- `scripts/compose_hcr.py` classifies texels by piece (plates, shield, mandibles = carapace; rings and feet = limbs;
  the two eye pieces = eyes, repainted as glossy dark domes since Meshy painted them beige) and, on the body piece, by the
  Meshy colour (pale low-saturation = armour, hue >= 48 deg saturated = acid, the rest = limbs); feathered 1 texel,
  padded into the gutters, normalised to a partition of unity.
- `scripts/tier_ramps.py`: ramps from the **approved concept sheet** (no native sprite): per tier figure the pixels are
  classified (acid by hue; carapace = upper 55 % of each silhouette column; limbs = the rest; B's yellow pods excluded),
  sorted by luminance and sampled at the base's luminance quantiles (the spider method), times a linear gain over the
  painting (1.2; acid 1.35 with a per-tier lime tint; the matron's carapace x0.62 and limbs x0.85 because the sheet's
  violet highlights spread over the whole plate). Eyes: hand-set dark-to-highlight ramps. The graded Meshy texture sits
  at ~0.5-0.6x the concept brightness, so the ramps lift it (tier A is also recoloured, as the contract requires).
- Material classes: 4 carapace and claws, 1 soft body, 6 eyes, 7 mouth interior. Materials get `openyamm_specular 0`
  and `metallicFactor 0` (creature default).

## Model, UVs, rig

- HD masters (Codex, `references_hd/CODEX_BRIEF.md`, 1536x1024 landscape) from the concept: Claude selected the first
  three-quarter return over Codex's correction (the correction shows nine leg forms). The front/back masters still show
  only three walking legs per side in places (Codex stopped after its one correction); they served only as retexture
  views.
- Smart Topology (15k) returned 29 rigid pieces, 15,556 tris, 1.00 m long, pitched 6.3 deg head-down (the claw tips lay
  on a tilted plane): `scripts/rig_hcr.py` levels it, grounds the tips, then reduces per part to **7,529** (body 0.42
  with the face kept at full density, plates 0.55, shield 0.75, rings/feet 0.5, mandibles 0.75, eyes untouched).
- UVs: Smart UV Project shattered the decimated mesh into 821 islands at 27 % coverage (the first retexture, 10 credits,
  is kept as `meshy/retexture_v1` but unused). `scripts/uv_atlas.py` (xatlas in a venv, see the script) makes 338 charts,
  47 % of the 2K page by area, 1,018 texels/m, the head charts at 2x; `retexture_v2` painted those UVs.
- Rig (29 bones): spine `Body` (root, mid-body) -> `Thorax` -> `Head`, `Body` -> `Abdomen` -> `Tail`, borders in the
  plate gaps; `Mandible_L/R`; `Sac` (throat sac, damped spring + squeeze in the clips); per leg `Femur` (hip inside the
  flank -> the ankle ring) and `Tibia` (ring -> claw tip; ring and foot rigid on it); `Socket_Mouth`; attachment bones.
  Heat weights on the body piece, every other piece rigid on one bone. `scripts/weights_fix.py` then removes Tibia
  weight from the body's leg tubes (the knee is the ring junction), fades Femur weight out of the flank (smoothstep on
  |x| 9.5-13 cm, remainder to the spine bone over that y) and gives the sac a smooth falloff.
- Attachments (`scripts/attachments.py`): procedural UV-sphere pods/sacs placed by ray casts, own small textures, each
  set 100 % on its own non-animated child bone; `tools/split_attachment.py` cuts them out of the runtime GLB.

## Clips (`scripts/anim_hcr.py`; gaits keyed at 60 fps, the rest at 30 fps, exported on one 60 fps timeline)

| Clip | Length | What |
|---|---|---|
| Standing | 2.0 s | breathing curl, throat-sac pulse, mandibles work |
| Walking | 0.20 s | alternating tetrapod (L1 R2 L3 R4 / R1 L2 R3 L4), duty 0.55, body 3.5 cm lower, footholds planned within reach; **stride 0.48 m** (2.4 model m/s) |
| Running | 0.167 s | same, duty 0.42, lower, longer sweep; **stride 0.80 m** (4.8 model m/s) |
| Attack | 1.1 s | rear up on the back legs, front legs raised, mandibles spread, sac swells, head snaps forward and the sac squeezes: **spit at 0.60 s** from `Socket_Mouth`; settle |
| Bite | 0.8 s | melee lunge, mandibles snap shut at **0.38 s** |
| Hit | 0.57 s | jolt back and down, legs splay, sac wobbles |
| Death / Dead | 1.6 s / held | rears, rolls over onto its back (toward its right), legs fold over the belly, the body curls; B's pods crush to 35 % as it rolls; grounded from 0.3 s |
| Fidget | 2.0 s | head sweeps left/right, front legs tap, mandibles clean |

Game speeds (speed / scale, chasing x2): A 3.0 / 6.0, B 2.4 / 4.8, C 1.87 / 3.73 model m/s, so walk and run play at
1.25 / 1.0 / 0.78 on the three tiers (inside the 0.75-1.5 window).

## Gates (`scripts/gates.py` -> `review/gates_v1.json`, every frame)

- Floor: lowest point -0.17..+0.04 cm in every living clip (feet 2 mm over the floor when planted), body never lower
  than 2.2 cm (Hit) while alive; the corpse rests on the floor (0.0 cm). Attachments are left out of the floor rule.
- Rigid pieces: <= 0.55 % edge change (sac and pods scale on purpose and are excluded).
- Body skin: edge stretch p99 <= 1.56 (Dead) and <= 1.46 in the living clips; tension max 2.36 (folded hips in Death),
  compression max 5.8 (hip creases in the gait) and 6.6 (the mouth while the sac squeezes): accepted creases, no tears.
- `check_winding.py`: 0 inverted closed parts on all five GLBs. Viewer `check`: 27 tier/clip switches, no console errors.

## Engine needs and open points (for the user / the parent)

- **Ranged attack data** (fixed 2026-10-22 in `design/kreegan_world/data/make_monster_tables.py`): Attack1 is now
  the spit with the existing green `Body` missile, Attack2 (40 %) the mandible bite. A dedicated acid projectile look
  (`engine/effects/projectiles.yml`) is optional later.
- **Glow** (done 2026-10-22, engine emission and creature bloom, `engine/render/MODEL_RENDERING.md`): the acid glows.
  `build_runtime.sh` ends with `../claude_shared/emission.py`: `textures/hcr_glow_mask.png` (acid region x brightness,
  1K, gamma 1.5) is the shared emissive texture, each tier's emissive factor is 0.6 x its acid ramp's top colour
  (A green, B yellow-green, C lime), with `openyamm_pulse [0.2, 2.5]`; the review viewer GLBs carry the same
  (`build_viewer.sh`). The matron's separate sacs keep their constant emissive factor (static attachments glow in
  bloom as they are). Staged as monsters 10090-10092 in the Hesper stage (no map places them yet); checked in
  `hes_d00.blv` with bloom on and off.
- **Attachments are rigid on one node each** (engine `ModelAttachment`): the sacs ride three segments to follow the
  body bend; they do not deform. B's pods sink up to ~2 cm into the floor on the dead brood crawler (crushed, scale
  0.35) because attachments are not part of the floor rule.
- LOD0 per tier: A 7,529, B 8,229, C 8,129 triangles (B slightly over the 8k target with its 700-triangle pods).
- The death is a skeletal roll; no acid-splash/dissolve effect (an engine death effect could add one).
- Not checked in game; scale, gait rate and the dim-corridor read should be judged in D0-D2.

## Replay

Claim the project, then with `TOK=<lease>`: `scripts/step.sh components.py`, `rig_hcr.py`, `uv_dump_mesh.py`,
`<venv>/bin/python -I scripts/uv_atlas.py work/uv_in.npz work/uv_atlas.npz` (about 15 min), `uv_export.py`, Meshy
`requests/retexture_v2.json`, `weights_fix.py`, `attachments.py`, `anim_hcr.py`, `dump_uv3d.py`,
`python3 scripts/compose_hcr.py`, `bake_ao.py`, `python3 ../claude_shared/grade_basecolor.py --ao textures/hcr_ao_2k.png
textures/hcr_basecolor.png`, `python3 scripts/tier_ramps.py`, `scripts/build_runtime.sh`, `scripts/build_viewer.sh`,
`gates.py`, `clip_sheet.py work/anim_v1.blend review/clips_v1.jpg`; viewer captures with `tools/run_creature_review.py`.
